import logging
from typing import Dict, List, Optional, Callable, Union

# Konfiguration des Loggings, um den Ablauf zu sehen
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("StateMachine")

# ============================================================================
# 1. STATE MACHINE FRAMEWORK (Generic)
# ============================================================================

class State:
    """
    Repräsentiert einen Zustand im State Pattern.
    Unterstützt Hierarchie (Composite States) und History.
    """
    def __init__(self, name: str, parent: Optional['State'] = None):
        self.name = name
        self.parent = parent
        self.substates: Dict[str, 'State'] = {}
        self.initial_state: Optional['State'] = None
        self.transitions: Dict[str, 'Transition'] = {}
        
        # Für History-Mechanismus [H]
        self.last_active_child: Optional['State'] = None
        self.is_history_shallow = False

        if parent:
            parent.add_substate(self)

    def add_substate(self, state: 'State'):
        self.substates[state.name] = state

    def set_initial(self, state: 'State'):
        self.initial_state = state

    def add_transition(self, event: str, target: Union['State', str], guard: Optional[Callable[[], bool]] = None):
        """
        Fügt eine Transition hinzu. 
        Target kann ein State-Objekt oder der String '[H]' für History sein.
        """
        self.transitions[event] = Transition(self, target, guard)

    def on_entry(self):
        """Platzhalter für Entry Action 'State: Entry: method'"""
        logger.info(f"Entry Action: {self.name}")

    def on_exit(self):
        """Platzhalter für Exit Action 'State: Exit: method'"""
        logger.info(f"Exit Action: {self.name}")

    def get_root(self) -> 'State':
        return self.parent.get_root() if self.parent else self

    def is_descendant_of(self, other: 'State') -> bool:
        temp = self.parent
        while temp:
            if temp == other:
                return True
            temp = temp.parent
        return False

    def __repr__(self):
        return f"<State: {self.name}>"


class Transition:
    """Kapselt die Logik eines Übergangs inkl. Guard."""
    def __init__(self, source: State, target: Union[State, str], guard: Optional[Callable[[], bool]] = None):
        self.source = source
        self.target = target # Kann State-Objekt oder '[H]' sein
        self.guard = guard

    def check_guard(self) -> bool:
        if self.guard:
            result = self.guard()
            logger.info(f"Guard check for transition {self.source.name}->...: {'PASS' if result else 'FAIL'}")
            return result
        return True


class StateMachine:
    """
    Die Engine, die Events verarbeitet und Zustandsübergänge steuert.
    """
    def __init__(self):
        self.root = State("Root")
        self.current_state: Optional[State] = None

    def start(self):
        """Startet die Maschine und betritt den initialen Zustand."""
        logger.info("--- State Machine Started ---")
        if self.root.initial_state:
            self._enter_state(self.root.initial_state)
        else:
            self.current_state = self.root

    def dispatch(self, event_name: str):
        """Verarbeitet ein Event und löst Transitionen aus."""
        logger.info(f"Event received: '{event_name}'")
        
        # 1. Finde den Zustand, der das Event behandelt (Bubble-Up für Hierarchie)
        source_state = self.current_state
        transition = None
        
        while source_state:
            if event_name in source_state.transitions:
                pot_trans = source_state.transitions[event_name]
                if pot_trans.check_guard():
                    transition = pot_trans
                    break
            source_state = source_state.parent

        if not transition:
            logger.warning(f"Event '{event_name}' ignoriert (keine gültige Transition im Zustand {self.current_state.name} oder Eltern).")
            return

        # 2. Ziel bestimmen (History Handling)
        target_state = self._resolve_target(transition.target, transition.source)

        # 3. LCA (Least Common Ancestor) finden für korrekte Exit/Entry Reihenfolge
        lca = self._find_lca(transition.source, target_state)

        # 4. Exits ausführen (von Current hoch bis LCA)
        self._execute_exits(self.current_state, lca)

        # 5. Transition durchführen (State Update)
        # Wenn wir Composite States verlassen, speichern wir die History im Parent
        temp = self.current_state
        while temp and temp != lca:
            if temp.parent:
                temp.parent.last_active_child = temp
            temp = temp.parent
            
        self.current_state = target_state

        # 6. Entries ausführen (von LCA runter bis Target)
        self._execute_entries(target_state, lca)

        # 7. Initial States von Substates betreten (Drill-Down)
        self._enter_initial_substates(target_state)

    def _resolve_target(self, target: Union[State, str], source: State) -> State:
        """Löst [H] oder normale Targets auf."""
        if isinstance(target, str) and target == "[H]":
            # History Transition: Wenn Parent History hat, nutze sie, sonst Initial
            parent = source.parent # Vereinfacht: Annahme Transition ist lokal
            if parent and parent.last_active_child:
                return parent.last_active_child
            elif parent and parent.initial_state:
                return parent.initial_state
            else:
                return source # Fallback
        return target

    def _find_lca(self, s1: State, s2: State) -> Optional[State]:
        """Findet den gemeinsamen Vorfahren (Least Common Ancestor)."""
        if s1 == s2: return s1.parent
        path1 = []
        curr = s1
        while curr:
            path1.append(curr)
            curr = curr.parent
        curr = s2
        while curr:
            if curr in path1:
                return curr
            curr = curr.parent
        return None

    def _execute_exits(self, start_node: State, up_to_node: State):
        curr = start_node
        while curr and curr != up_to_node:
            curr.on_exit()
            curr = curr.parent

    def _execute_entries(self, target_node: State, down_from_node: State):
        path = []
        curr = target_node
        while curr and curr != down_from_node:
            path.append(curr)
            curr = curr.parent
        for s in reversed(path):
            s.on_entry()

    def _enter_state(self, state: State):
        """Hilfsmethode für direkten Eintritt (z.B. beim Start)."""
        # Hier vereinfacht ohne LCA, da Start
        path = []
        curr = state
        while curr and curr.parent:
            path.append(curr)
            curr = curr.parent
        for s in reversed(path):
            s.on_entry()
        self.current_state = state
        self._enter_initial_substates(state)

    def _enter_initial_substates(self, state: State):
        """Rekursives Betreten der Initial States, falls Composite."""
        curr = state
        while curr.initial_state:
            curr = curr.initial_state
            curr.on_entry()
            self.current_state = curr


# ============================================================================
# 2. IMPLEMENTIERUNG (PlantUML Spezifisch)
# ============================================================================

class DoorStateMachine(StateMachine):
    def __init__(self):
        super().__init__()

        # --- Zustände definieren ---
        # Namen identisch zum PlantUML Code
        self.Auf = State("Auf", parent=self.root)
        self.Zu = State("Zu", parent=self.root)
        self.Verriegelt = State("Verriegelt", parent=self.root)

        # --- Initial State ---
        # [*] --> Auf
        self.root.set_initial(self.Auf)

        # --- Transitionen definieren ---
        # Auf --> Zu : schließen
        self.Auf.add_transition("schließen", self.Zu)

        # Zu --> Verriegelt : verriegeln
        self.Zu.add_transition("verriegeln", self.Verriegelt)

        # Verriegelt --> Zu : entriegeln
        self.Verriegelt.add_transition("entriegeln", self.Zu)

        # Zu --> Auf : öffnen
        self.Zu.add_transition("öffnen", self.Auf)

        # --- Actions & Guards (Optional) ---
        # Da das bereitgestellte PlantUML keine expliziten Entry/Exit oder Guards hat,
        # sind diese Methoden standardmäßig leer (siehe Basisklasse).
        # Um die Anforderung "Methoden identisch zum PlantUML" zu erfüllen:
        # Würde im PlantUML stehen: `Zu: Entry: validate`, müssten wir hier tun:
        # self.Zu.on_entry = self.validate
        # self.validate = lambda: print("Validating...")

# ============================================================================
# 3. EXECUTION DEMO
# ============================================================================

if __name__ == "__main__":
    # Instanziierung
    sm = DoorStateMachine()
    
    # Start ([*] --> Auf)
    sm.start()
    
    # Test Ablauf
    sm.dispatch("schließen")  # Auf -> Zu
    sm.dispatch("verriegeln") # Zu -> Verriegelt
    sm.dispatch("öffnen")     # Verriegelt -> Ignoriert (keine Transition definiert)
    sm.dispatch("entriegeln") # Verriegelt -> Zu
    sm.dispatch("öffnen")     # Zu -> Auf