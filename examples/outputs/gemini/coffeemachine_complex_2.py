import logging

# Konfiguration des Loggings für Nachvollziehbarkeit
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ==========================================
# 1. FRAMEWORK (Generic State Machine Logic)
# ==========================================

class Context:
    """Hält die Daten (z.B. wasser stand) und Referenzen zu den Actions."""
    def __init__(self, actions):
        self.actions = actions
        self.data = {}  # Speicher für Variablen (z.B. wasser)

class State:
    """Abstrakte Basisklasse für alle Zustände."""
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.context = None

    def set_context(self, context):
        self.context = context

    def on_entry(self, use_history=False):
        """Wird beim Betreten des Zustands ausgeführt."""
        logging.info(f"-> Entering State: {self.name}")
        self.perform_entry_action()

    def on_exit(self):
        """Wird beim Verlassen des Zustands ausgeführt."""
        self.perform_exit_action()
        logging.info(f"<- Exiting State: {self.name}")

    def perform_entry_action(self):
        pass

    def perform_exit_action(self):
        pass

    def handle_event(self, event_name):
        """
        Verarbeitet Events. 
        Gibt den neuen Zustand zurück, wenn eine Transition feuert, sonst None.
        """
        return None

    def get_root(self):
        node = self
        while node.parent:
            node = node.parent
        return node

class CompositeState(State):
    """
    Ein Zustand, der Unterzustände haben kann (Hierarchie).
    Unterstützt [H] (Shallow History).
    """
    def __init__(self, name, parent=None, initial_state_cls=None):
        super().__init__(name, parent)
        self.initial_state_cls = initial_state_cls
        self.active_substate = None
        self.last_active_substate_cls = None # Für History [H]
        self.substates = {}

    def add_substate(self, state_cls):
        # Instanziiert den Substate und verknüpft ihn
        instance = state_cls(parent=self)
        self.substates[state_cls] = instance
        return instance

    def set_context(self, context):
        super().set_context(context)
        for sub in self.substates.values():
            sub.set_context(context)

    def on_entry(self, use_history=False):
        super().on_entry(use_history)
        
        target_state_cls = self.initial_state_cls
        
        # History Logic [H]
        if use_history and self.last_active_substate_cls:
            logging.info(f"   [History] Restoring state: {self.last_active_substate_cls.__name__}")
            target_state_cls = self.last_active_substate_cls
        
        if target_state_cls:
            new_state = self.substates[target_state_cls]
            self.active_substate = new_state
            new_state.on_entry()

    def on_exit(self):
        # Erst Child exiten, dann Self
        if self.active_substate:
            # Speichere für History
            self.last_active_substate_cls = type(self.active_substate)
            self.active_substate.on_exit()
            self.active_substate = None
        super().on_exit()

    def handle_event(self, event_name):
        # 1. Versuch: Delegiere an aktiven Substate (Bubble Up Prinzip)
        transition = None
        if self.active_substate:
            transition = self.active_substate.handle_event(event_name)
        
        # 2. Wenn Substate nicht reagiert hat, versuche es selbst
        if not transition:
            transition = self._check_own_transitions(event_name)

        return transition

    def _check_own_transitions(self, event_name):
        return None

# ==========================================
# 2. MODEL (Implementation of PlantUML)
# ==========================================

# --- Actions Interface ---
class MachineActions:
    """Definiert alle Action-Methoden aus dem Diagramm."""
    def piepen(self): print("   [ACTION] piepen")
    def wasserReinigen(self): print("   [ACTION] wasserReinigen")
    def kaffeeMachen(self): print("   [ACTION] kaffeeMachen logic triggered") 

# --- Concrete States ---

# Forward declarations for transitions
class StateAus(State): pass
class StateAn(CompositeState): pass
class StatePause(State): pass
# Substates of An
class StateLeerlauf(State): pass
class StateZubereitung(State): pass
class StateAusgabe(State): pass


class StateAus(State):
    def __init__(self, parent=None):
        super().__init__("Aus", parent)

    def perform_exit_action(self):
        self.context.actions.piepen()

    def handle_event(self, event_name):
        # Aus --> An : anschalten
        if event_name == "anschalten":
            return StateAn
        return super().handle_event(event_name)


class StatePause(State):
    def __init__(self, parent=None):
        super().__init__("Pause", parent)

    def handle_event(self, event_name):
        # Pause --> An[H] : fortfahren
        if event_name == "fortfahren":
            # Tuple return indicates (TargetClass, HistoryFlag)
            return (StateAn, True) 
        return super().handle_event(event_name)


class StateLeerlauf(State):
    def __init__(self, parent=None):
        super().__init__("Leerlauf", parent)

    def handle_event(self, event_name):
        # Leerlauf --> Leerlauf : wasserAuffüllen
        if event_name == "wasserAuffüllen":
            # Self transition: Exit and Re-enter usually, 
            # but simple internal transition logic for simplicity:
            logging.info("   [Internal] Wasser wird aufgefüllt")
            self.context.data['wasser'] = 100
            return None # Kein Zustandswechsel, interne Logik oder Self-Transition

        # Leerlauf --> Zubereitung : kaffeeMachen [wasser > 20]
        if event_name == "kaffeeMachen":
            if self.context.data.get('wasser', 0) > 20:
                return StateZubereitung
            else:
                logging.warning("   [Guard Fail] kaffeeMachen verweigert: wasser <= 20")
        
        return super().handle_event(event_name)


class StateZubereitung(State):
    def __init__(self, parent=None):
        super().__init__("Zubereitung", parent)

    def handle_event(self, event_name):
        # Zubereitung --> Ausgabe : zubereitungAbschließen
        if event_name == "zubereitungAbschließen":
            # Wasser verbrauchen
            self.context.data['wasser'] -= 20
            return StateAusgabe
        return super().handle_event(event_name)


class StateAusgabe(State):
    def __init__(self, parent=None):
        super().__init__("Ausgabe", parent)

    def handle_event(self, event_name):
        # Ausgabe --> Leerlauf : kaffeeEntnehmen
        if event_name == "kaffeeEntnehmen":
            return StateLeerlauf
        return super().handle_event(event_name)


class StateAn(CompositeState):
    def __init__(self, parent=None):
        # Composite Setup: Initial State ist Leerlauf
        super().__init__("An", parent, initial_state_cls=StateLeerlauf)
        
        # Substates registrieren
        self.add_substate(StateLeerlauf)
        self.add_substate(StateZubereitung)
        self.add_substate(StateAusgabe)

    def perform_entry_action(self):
        self.context.actions.wasserReinigen()

    def perform_exit_action(self):
        self.context.actions.piepen()

    def _check_own_transitions(self, event_name):
        # An --> Pause : stop
        # Da dies im Composite definiert ist, greift es, 
        # wenn der aktive Substate das Event nicht behandelt hat.
        if event_name == "stop":
            return StatePause
        return None


# --- Main Controller ---

class CoffeeMachineController:
    def __init__(self):
        self.actions = MachineActions()
        self.context = Context(self.actions)
        self.context.data['wasser'] = 0 # Initialwert

        # Alle Top-Level Zustände initialisieren
        self.states = {}
        self.states[StateAus] = StateAus()
        self.states[StateAn] = StateAn()
        self.states[StatePause] = StatePause()

        # Context injizieren
        for s in self.states.values():
            s.set_context(self.context)

        # Startzustand: [*] --> Aus
        self.current_state = self.states[StateAus]
        self.current_state.on_entry()

    def dispatch(self, event_name):
        logging.info(f"EVENT: '{event_name}' received.")
        
        # Frage aktuellen Zustand nach Transition
        result = self.current_state.handle_event(event_name)
        
        if result:
            target_cls = None
            use_history = False

            # Check if result is tuple (State, HistoryFlag) or just State
            if isinstance(result, tuple):
                target_cls, use_history = result
            else:
                target_cls = result

            self._transition_to(target_cls, use_history)
        else:
            logging.info("   (Event ignored or internal)")

    def _transition_to(self, target_cls, use_history=False):
        # Vereinfachte Transition Logic für diese spezifische Hierarchie.
        # Annahme: Transitionen finden hauptsächlich zwischen Top-Level States
        # oder innerhalb des Composite States statt.
        
        target_instance = self.states.get(target_cls)
        
        # 1. Fall: Wechsel innerhalb des Composite 'An'
        # (z.B. Leerlauf -> Zubereitung)
        if (isinstance(self.current_state, StateAn) and 
            self.current_state.active_substate and
            target_cls in self.current_state.substates):
            
            # Nur Substate wechseln
            old_sub = self.current_state.active_substate
            old_sub.on_exit()
            
            new_sub = self.current_state.substates[target_cls]
            self.current_state.active_substate = new_sub
            new_sub.on_entry()
            return

        # 2. Fall: Wechsel Top-Level
        if target_instance:
            self.current_state.on_exit()
            self.current_state = target_instance
            self.current_state.on_entry(use_history=use_history)
            return
        
        logging.error(f"Critical: Target state {target_cls} not found logic.")


# ==========================================
# 3. DEMO / VERIFICATION
# ==========================================

if __name__ == "__main__":
    sm = CoffeeMachineController()
    
    print("\n--- Szenario 1: Normaler Ablauf ---")
    sm.dispatch("anschalten")        # Aus -> An (Entry: wasserReinigen) -> Leerlauf
    sm.dispatch("kaffeeMachen")      # Leerlauf -> Guard Check (wasser=0) -> Blocked
    
    print("\n--- Szenario 2: Wasser füllen ---")
    sm.dispatch("wasserAuffüllen")   # Internal: wasser=100
    sm.dispatch("kaffeeMachen")      # Leerlauf -> Zubereitung
    
    print("\n--- Szenario 3: Pause & History ---")
    # Wir sind in 'Zubereitung'. Jetzt drücken wir Stop.
    sm.dispatch("stop")              # An (bubbles up) -> Pause. 
                                     # Exit Zubereitung -> Exit An (piepen) -> Enter Pause
    
    # Fortfahren mit History [H]
    sm.dispatch("fortfahren")        # Pause -> An[H]. 
                                     # Enter An (wasserReinigen) -> Restore Zubereitung
    
    print("\n--- Szenario 4: Abschluss ---")
    sm.dispatch("zubereitungAbschließen") # Zubereitung -> Ausgabe
    sm.dispatch("kaffeeEntnehmen")        # Ausgabe -> Leerlauf
    
    # Abschalten
    # Hinweis: Diagramm definiert keinen Weg von An nach Aus, nur Pause->An oder [*]->Aus.
    # Daher bleibt die Maschine An, bis wir den Prozess beenden.
    print("\n--- End Status ---")
    print(f"Wasserstand: {sm.context.data['wasser']}")