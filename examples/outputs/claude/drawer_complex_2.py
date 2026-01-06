"""
State Machine Implementation
Basierend auf PlantUML-Spezifikation für Türschloss-Zustandsmaschine

Zustände: Auf, Zu, Verriegelt
Events: schließen, öffnen, verriegeln, entriegeln
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field


# =============================================================================
# CORE FRAMEWORK - Zustandsverwaltung (State Management Logic)
# =============================================================================

@dataclass
class Transition:
    """Repräsentiert einen Zustandsübergang"""
    source: str
    target: str
    event: str
    guard: Optional[Callable[[], bool]] = None
    
    def can_execute(self) -> bool:
        """Prüft ob Guard-Bedingung erfüllt ist"""
        if self.guard is None:
            return True
        return self.guard()


class State(ABC):
    """Abstrakte Basisklasse für alle Zustände (State Pattern)"""
    
    def __init__(self, name: str):
        self._name = name
        self._entry_actions: List[Callable[[], None]] = []
        self._exit_actions: List[Callable[[], None]] = []
    
    @property
    def name(self) -> str:
        return self._name
    
    def add_entry_action(self, action: Callable[[], None]) -> None:
        """Fügt Entry-Action hinzu"""
        self._entry_actions.append(action)
    
    def add_exit_action(self, action: Callable[[], None]) -> None:
        """Fügt Exit-Action hinzu"""
        self._exit_actions.append(action)
    
    def on_entry(self, context: 'StateMachine') -> None:
        """Wird beim Betreten des Zustands aufgerufen"""
        for action in self._entry_actions:
            action()
    
    def on_exit(self, context: 'StateMachine') -> None:
        """Wird beim Verlassen des Zustands aufgerufen"""
        for action in self._exit_actions:
            action()


class SimpleState(State):
    """Einfacher Zustand ohne Unterzustände"""
    pass


class CompositeState(State):
    """Composite State mit Unterstützung für Unterzustände und History"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self._substates: Dict[str, State] = {}
        self._initial_substate: Optional[str] = None
        self._history_state: Optional[str] = None  # Für [H] History State
        self._current_substate: Optional[State] = None
    
    def add_substate(self, state: State, is_initial: bool = False) -> None:
        """Fügt Unterzustand hinzu"""
        self._substates[state.name] = state
        if is_initial:
            self._initial_substate = state.name
    
    def save_history(self) -> None:
        """Speichert aktuellen Unterzustand für History"""
        if self._current_substate:
            self._history_state = self._current_substate.name
    
    def restore_history(self) -> Optional[str]:
        """Gibt gespeicherten History-Zustand zurück"""
        return self._history_state or self._initial_substate


class StateMachine:
    """
    Haupt-Zustandsmaschine
    Verwaltet Zustände, Transitionen und Event-Verarbeitung
    """
    
    def __init__(self, name: str = "StateMachine"):
        self._name = name
        self._states: Dict[str, State] = {}
        self._transitions: List[Transition] = []
        self._current_state: Optional[State] = None
        self._initial_state: Optional[str] = None
        self._running: bool = False
        
        # Callbacks für externe Aktionen
        self._action_handlers: Dict[str, Callable[..., Any]] = {}
    
    # -------------------------------------------------------------------------
    # Konfiguration
    # -------------------------------------------------------------------------
    
    def add_state(self, state: State, is_initial: bool = False) -> None:
        """Registriert einen Zustand"""
        self._states[state.name] = state
        if is_initial:
            self._initial_state = state.name
    
    def add_transition(
        self, 
        source: str, 
        target: str, 
        event: str,
        guard: Optional[Callable[[], bool]] = None
    ) -> None:
        """Registriert eine Transition"""
        transition = Transition(
            source=source,
            target=target,
            event=event,
            guard=guard
        )
        self._transitions.append(transition)
    
    def register_action(self, name: str, handler: Callable[..., Any]) -> None:
        """Registriert einen Action-Handler"""
        self._action_handlers[name] = handler
    
    # -------------------------------------------------------------------------
    # Laufzeit
    # -------------------------------------------------------------------------
    
    def start(self) -> None:
        """Startet die Zustandsmaschine"""
        if self._initial_state is None:
            raise RuntimeError("Kein Initialzustand definiert")
        
        if self._initial_state not in self._states:
            raise RuntimeError(f"Initialzustand '{self._initial_state}' nicht gefunden")
        
        self._current_state = self._states[self._initial_state]
        self._running = True
        
        print(f"╔══════════════════════════════════════════╗")
        print(f"║  State Machine gestartet                 ║")
        print(f"║  Initialzustand: {self._current_state.name:<22} ║")
        print(f"╚══════════════════════════════════════════╝")
        
        # Entry-Action des Initialzustands ausführen
        self._current_state.on_entry(self)
    
    def stop(self) -> None:
        """Stoppt die Zustandsmaschine"""
        if self._current_state:
            self._current_state.on_exit(self)
        self._running = False
        print("\n[State Machine gestoppt]")
    
    @property
    def current_state(self) -> str:
        """Gibt den Namen des aktuellen Zustands zurück"""
        return self._current_state.name if self._current_state else ""
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def process_event(self, event: str) -> bool:
        """
        Verarbeitet ein Event und führt ggf. Zustandsübergang durch
        
        Returns:
            True wenn Transition ausgeführt wurde, sonst False
        """
        if not self._running:
            print(f"⚠ State Machine nicht gestartet!")
            return False
        
        if self._current_state is None:
            return False
        
        # Passende Transition suchen
        for transition in self._transitions:
            if (transition.source == self._current_state.name and 
                transition.event == event and
                transition.can_execute()):
                
                self._execute_transition(transition, event)
                return True
        
        # Keine passende Transition gefunden
        print(f"  ⚠ Event '{event}' im Zustand '{self._current_state.name}' ignoriert")
        return False
    
    def _execute_transition(self, transition: Transition, event: str) -> None:
        """Führt eine Transition aus"""
        old_state_name = self._current_state.name
        new_state = self._states[transition.target]
        
        # 1. Exit-Actions des alten Zustands
        self._current_state.on_exit(self)
        
        # 2. Zustandswechsel
        self._current_state = new_state
        
        # 3. Entry-Actions des neuen Zustands
        self._current_state.on_entry(self)
        
        # Transition protokollieren
        self._log_transition(old_state_name, event, new_state.name)
    
    def _log_transition(self, source: str, event: str, target: str) -> None:
        """Protokolliert eine Transition"""
        print(f"  ┌─ {source}")
        print(f"  │  ──[{event}]──►")
        print(f"  └─ {target}")
    
    def get_available_events(self) -> List[str]:
        """Gibt verfügbare Events für aktuellen Zustand zurück"""
        if not self._current_state:
            return []
        
        events = []
        for transition in self._transitions:
            if transition.source == self._current_state.name:
                if transition.can_execute():
                    events.append(transition.event)
        return events


# =============================================================================
# KONKRETE IMPLEMENTIERUNG - Türschloss State Machine
# =============================================================================

class TürschlossActions:
    """
    Aktionen für die Türschloss-Zustandsmaschine
    (Trennung von Zustandslogik und Aktionsausführung)
    """
    
    @staticmethod
    def on_enter_auf() -> None:
        print("    → Tür ist jetzt OFFEN")
    
    @staticmethod
    def on_exit_auf() -> None:
        print("    ← Verlasse Zustand 'Auf'")
    
    @staticmethod
    def on_enter_zu() -> None:
        print("    → Tür ist jetzt GESCHLOSSEN")
    
    @staticmethod
    def on_exit_zu() -> None:
        print("    ← Verlasse Zustand 'Zu'")
    
    @staticmethod
    def on_enter_verriegelt() -> None:
        print("    → Tür ist jetzt VERRIEGELT 🔒")
    
    @staticmethod
    def on_exit_verriegelt() -> None:
        print("    ← Verlasse Zustand 'Verriegelt'")


def create_türschloss_state_machine() -> StateMachine:
    """
    Factory-Funktion: Erstellt die Türschloss-Zustandsmaschine
    basierend auf der PlantUML-Spezifikation
    """
    sm = StateMachine("Türschloss")
    
    # -------------------------------------------------------------------------
    # Zustände erstellen
    # -------------------------------------------------------------------------
    
    # state Auf
    state_auf = SimpleState("Auf")
    state_auf.add_entry_action(TürschlossActions.on_enter_auf)
    state_auf.add_exit_action(TürschlossActions.on_exit_auf)
    
    # state Zu
    state_zu = SimpleState("Zu")
    state_zu.add_entry_action(TürschlossActions.on_enter_zu)
    state_zu.add_exit_action(TürschlossActions.on_exit_zu)
    
    # state Verriegelt
    state_verriegelt = SimpleState("Verriegelt")
    state_verriegelt.add_entry_action(TürschlossActions.on_enter_verriegelt)
    state_verriegelt.add_exit_action(TürschlossActions.on_exit_verriegelt)
    
    # Zustände registrieren
    # [*] --> Auf (Initialzustand)
    sm.add_state(state_auf, is_initial=True)
    sm.add_state(state_zu)
    sm.add_state(state_verriegelt)
    
    # -------------------------------------------------------------------------
    # Transitionen erstellen (exakt wie in PlantUML)
    # -------------------------------------------------------------------------
    
    # Auf --> Zu : schließen
    sm.add_transition(
        source="Auf",
        target="Zu",
        event="schließen"
    )
    
    # Zu --> Verriegelt : verriegeln
    sm.add_transition(
        source="Zu",
        target="Verriegelt",
        event="verriegeln"
    )
    
    # Verriegelt --> Zu : entriegeln
    sm.add_transition(
        source="Verriegelt",
        target="Zu",
        event="entriegeln"
    )
    
    # Zu --> Auf : öffnen
    sm.add_transition(
        source="Zu",
        target="Auf",
        event="öffnen"
    )
    
    return sm


# =============================================================================
# DEMO & TEST
# =============================================================================

def demo_interactive():
    """Interaktive Demo der Zustandsmaschine"""
    sm = create_türschloss_state_machine()
    sm.start()
    
    print("\n" + "═" * 50)
    print("INTERAKTIVE DEMO - Türschloss State Machine")
    print("═" * 50)
    print("Befehle: schließen, öffnen, verriegeln, entriegeln, quit")
    print("═" * 50 + "\n")
    
    while sm.is_running:
        available = sm.get_available_events()
        print(f"\n┌── Aktueller Zustand: [{sm.current_state}]")
        print(f"│   Verfügbare Events: {available}")
        
        try:
            event = input("└── Event eingeben: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if event.lower() == 'quit':
            break
        
        if event:
            sm.process_event(event)
    
    sm.stop()


def demo_automated():
    """Automatisierte Demo mit vordefinierten Events"""
    print("\n" + "═" * 50)
    print("AUTOMATISIERTE DEMO - Türschloss State Machine")
    print("═" * 50 + "\n")
    
    sm = create_türschloss_state_machine()
    sm.start()
    
    # Testszenario
    test_events = [
        "schließen",      # Auf → Zu
        "verriegeln",     # Zu → Verriegelt
        "öffnen",         # Ignoriert (nicht möglich)
        "entriegeln",     # Verriegelt → Zu
        "öffnen",         # Zu → Auf
        "verriegeln",     # Ignoriert (nicht möglich)
        "schließen",      # Auf → Zu
    ]
    
    print("\nTest-Sequenz wird ausgeführt...")
    print("─" * 40)
    
    for event in test_events:
        print(f"\n► Event: '{event}'")
        sm.process_event(event)
    
    print("\n" + "─" * 40)
    print(f"Endzustand: {sm.current_state}")
    sm.stop()


def run_unit_tests():
    """Einfache Unit-Tests"""
    print("\n" + "═" * 50)
    print("UNIT TESTS")
    print("═" * 50 + "\n")
    
    sm = create_türschloss_state_machine()
    sm.start()
    
    tests_passed = 0
    tests_total = 0
    
    def assert_state(expected: str, message: str):
        nonlocal tests_passed, tests_total
        tests_total += 1
        if sm.current_state == expected:
            tests_passed += 1
            print(f"  ✓ {message}")
        else:
            print(f"  ✗ {message} (erwartet: {expected}, ist: {sm.current_state})")
    
    # Tests
    assert_state("Auf", "Initialzustand ist 'Auf'")
    
    sm.process_event("schließen")
    assert_state("Zu", "Nach 'schließen' ist Zustand 'Zu'")
    
    sm.process_event("verriegeln")
    assert_state("Verriegelt", "Nach 'verriegeln' ist Zustand 'Verriegelt'")
    
    sm.process_event("öffnen")
    assert_state("Verriegelt", "Event 'öffnen' wird in 'Verriegelt' ignoriert")
    
    sm.process_event("entriegeln")
    assert_state("Zu", "Nach 'entriegeln' ist Zustand 'Zu'")
    
    sm.process_event("öffnen")
    assert_state("Auf", "Nach 'öffnen' ist Zustand 'Auf'")
    
    print(f"\n═══ Ergebnis: {tests_passed}/{tests_total} Tests bestanden ═══\n")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Unit Tests ausführen
    run_unit_tests()
    
    # Automatisierte Demo
    demo_automated()
    
    # Für interaktive Demo, diese Zeile einkommentieren:
    # demo_interactive()