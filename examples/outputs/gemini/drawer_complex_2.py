import logging

# Konfiguration des Loggings, um die Zustandsübergänge sichtbar zu machen
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class State:
    """
    Repräsentiert einen Zustand (Einfach oder Composite).
    Unterstützt Hierarchie, Entry/Exit Actions und Transitions.
    """
    def __init__(self, name, parent=None, entry_action=None, exit_action=None):
        self.name = name
        self.parent = parent
        self.entry_action = entry_action
        self.exit_action = exit_action
        self.transitions = {}  # Key: Event Name, Value: List of Transition objects
        self.children = []
        self.initial_state = None
        self.history_state = None # Speichert den letzten aktiven Sub-Zustand für [H]
        self.is_history_target = False # Markiert diesen State als [H] Pseudostate

        if parent:
            parent.children.append(self)

    def add_transition(self, event_name, target_state, guard=None):
        if event_name not in self.transitions:
            self.transitions[event_name] = []
        self.transitions[event_name].append(Transition(self, target_state, guard))

    def set_initial(self, state):
        self.initial_state = state

    def get_path(self):
        """Gibt die Liste der Zustände von der Wurzel bis zu diesem Zustand zurück."""
        path = [self]
        curr = self.parent
        while curr:
            path.insert(0, curr)
            curr = curr.parent
        return path

    def __repr__(self):
        return self.name


class Transition:
    """
    Kapselt eine Transition mit Zielzustand und optionalem Guard.
    """
    def __init__(self, source, target, guard=None):
        self.source = source
        self.target = target
        self.guard = guard  # Callable, das True/False zurückgibt

    def check_guard(self, context):
        if self.guard:
            return self.guard(context)
        return True


class StateMachine:
    """
    Die Engine, die Events verarbeitet und die komplexe Logik für
    Composite States, History und Action-Reihenfolge kapselt.
    """
    def __init__(self, root_state):
        self.root = root_state
        self.current_state = None
        
        # Initialisierung: Start beim Initial State des Root (oder Root selbst)
        self._enter_initial(self.root)

    def _enter_initial(self, state):
        """Rekursives Eintreten in Initial-Zustände."""
        target = state
        path_to_enter = [target]
        
        # Falls Composite, suche den Startpunkt
        while target.initial_state:
            target = target.initial_state
            path_to_enter.append(target)
            
        # Entry Actions von oben nach unten ausführen
        for s in path_to_enter:
            self._execute_entry(s)
            
        self.current_state = target
        logger.info(f"Machine initialized at: {self.current_state.name}")

    def dispatch(self, event_name, context=None):
        """
        Hauptmethode zur Verarbeitung von Events.
        Bubbling: Sucht Transition im aktuellen State, dann im Parent, usw.
        """
        logger.info(f"\nEvent received: {event_name}")
        state = self.current_state
        
        while state:
            if event_name in state.transitions:
                # Prüfe alle Transitionen für dieses Event (wegen möglicher Guards)
                for transition in state.transitions[event_name]:
                    if transition.check_guard(context):
                        self._perform_transition(transition)
                        return
            # Event Bubbling (zu Parent gehen)
            state = state.parent
            
        logger.warning(f"Event '{event_name}' ignored in state '{self.current_state.name}'.")

    def _perform_transition(self, transition):
        source = self.current_state
        target = transition.target
        
        # 1. Least Common Ancestor (LCA) finden
        lca = self._find_lca(source, target)
        
        # 2. Exit Actions: Von Current bis (aber nicht inkl.) LCA
        curr = source
        while curr != lca:
            self._execute_exit(curr)
            # History aktualisieren (für Parent merken, welches Kind aktiv war)
            if curr.parent:
                curr.parent.history_state = curr
            curr = curr.parent
            
        # 3. Transition Logik (Ziel ermitteln)
        # Wenn Ziel ein History-State [H] ist
        actual_target = target
        if target.is_history_target:
             # Falls History gespeichert, nutze diese, sonst Initial des Parents
            if target.parent.history_state:
                actual_target = target.parent.history_state
                logger.info(f"Restoring History: {actual_target.name}")
            else:
                actual_target = target.parent.initial_state

        # 4. Pfad zum Ziel ermitteln (vom LCA nach unten)
        path_down = []
        curr = actual_target
        while curr != lca and curr is not None:
            path_down.insert(0, curr)
            curr = curr.parent
            
        # 5. Entry Actions: Vom LCA (exkl.) bis zum Target
        for s in path_down:
            self._execute_entry(s)

        # 6. Falls Target Composite ist -> in Initial absteigen
        if actual_target.initial_state:
            self._enter_initial_struct(actual_target)
        else:
            self.current_state = actual_target

    def _enter_initial_struct(self, composite_state):
        """Hilfsmethode um tief in eine Struktur einzutauchen nach einer Transition"""
        curr = composite_state
        while curr.initial_state:
            curr = curr.initial_state
            self._execute_entry(curr)
        self.current_state = curr

    def _find_lca(self, s1, s2):
        path1 = s1.get_path()
        path2 = s2.get_path()
        lca = None
        # Gehe beide Pfade durch solange sie gleich sind
        for p1, p2 in zip(path1, path2):
            if p1 == p2:
                lca = p1
            else:
                break
        return lca

    def _execute_entry(self, state):
        if state.entry_action:
            state.entry_action()
        # Logging für Debugging
        # logger.info(f"  -> Entered {state.name}")

    def _execute_exit(self, state):
        if state.exit_action:
            state.exit_action()
        # Logging für Debugging
        # logger.info(f"  <- Exited {state.name}")


# =============================================================================
# IMPLEMENTIERUNG DES PLANTUML MODELLS
# =============================================================================

class DoorController:
    """
    Container für Action-Methoden (Entry/Exit) und Guards.
    Hier wird die Business-Logik von der State-Machine-Logik getrennt.
    """
    def log_state(self, name):
        logger.info(f"State changed to: {name}")

    # Actions können hier definiert werden (falls im PlantUML gefordert)
    # Beispiel: def on_entry_zu(self): print("Tür ist zu")

def build_door_machine():
    ctrl = DoorController()
    
    # 1. Zustände definieren
    # Root Container (implizit in PlantUML)
    root = State("Root")
    
    # Einfache Zustände
    auf = State("Auf", parent=root)
    zu = State("Zu", parent=root)
    verriegelt = State("Verriegelt", parent=root)
    
    # Entry Actions zuweisen (Optional, für Visualisierung)
    auf.entry_action = lambda: ctrl.log_state("Auf")
    zu.entry_action = lambda: ctrl.log_state("Zu")
    verriegelt.entry_action = lambda: ctrl.log_state("Verriegelt")

    # 2. Initial State definieren ([*] --> Auf)
    root.set_initial(auf)

    # 3. Transitionen definieren (Exakt nach PlantUML)
    # Auf --> Zu : schließen
    auf.add_transition("schließen", zu)
    
    # Zu --> Verriegelt : verriegeln
    zu.add_transition("verriegeln", verriegelt)
    
    # Verriegelt --> Zu : entriegeln
    verriegelt.add_transition("entriegeln", zu)
    
    # Zu --> Auf : öffnen
    zu.add_transition("öffnen", auf)
    
    # Machine instanziieren
    sm = StateMachine(root)
    return sm

# =============================================================================
# AUSFÜHRUNG / TEST
# =============================================================================

if __name__ == "__main__":
    # Aufbau der State Machine
    sm = build_door_machine()
    
    # Simulation der Events
    sm.dispatch("schließen")    # Erwartet: Auf -> Zu
    sm.dispatch("verriegeln")   # Erwartet: Zu -> Verriegelt
    sm.dispatch("öffnen")       # Erwartet: Ignoriert (da verriegelt)
    sm.dispatch("entriegeln")   # Erwartet: Verriegelt -> Zu
    sm.dispatch("öffnen")       # Erwartet: Zu -> Auf