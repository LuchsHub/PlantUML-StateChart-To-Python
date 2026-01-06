"""
State Machine Implementation
============================
Unterstützt: Einfache Zustände, Composite States, History States, 
             Guards und Entry/Exit Actions

Generiert aus PlantUML-Spezifikation.
"""

from __future__ import annotations
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


# ═══════════════════════════════════════════════════════════════════════════════
# CORE COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Transition:
    """
    Repräsentiert einen Zustandsübergang.
    
    Attributes:
        source: Name des Quellzustands
        target: Name des Zielzustands
        event: Auslösendes Event
        guard: Optionale Bedingung [Bedingung]
        action: Optionale Transitionsaktion
    """
    source: str
    target: str
    event: str
    guard: Optional[Callable[[dict], bool]] = None
    action: Optional[Callable[[], None]] = None
    
    def can_fire(self, context: dict) -> bool:
        """Prüft, ob der Guard erfüllt ist."""
        return self.guard(context) if self.guard else True


class State:
    """
    Basisklasse für alle Zustände.
    
    Unterstützt Entry/Exit Actions gemäß PlantUML-Konvention:
        State: Entry: method
        State: Exit: method
    """
    
    def __init__(self, name: str):
        self.name = name
        self.entry_action: Optional[Callable[[], None]] = None
        self.exit_action: Optional[Callable[[], None]] = None
        self.parent: Optional[CompositeState] = None
    
    def on_entry(self, machine: StateMachine) -> None:
        """Wird beim Betreten des Zustands aufgerufen."""
        if self.entry_action:
            self.entry_action()
    
    def on_exit(self, machine: StateMachine) -> None:
        """Wird beim Verlassen des Zustands aufgerufen."""
        if self.exit_action:
            self.exit_action()
    
    def __repr__(self) -> str:
        return f"State({self.name})"


class CompositeState(State):
    """
    Composite State mit Unterstützung für verschachtelte Zustände
    und History State [H].
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.substates: dict[str, State] = {}
        self.initial_substate: Optional[str] = None
        self._history: Optional[str] = None  # Für [H]
    
    def add_substate(self, state: State, is_initial: bool = False) -> None:
        """Fügt einen Unterzustand hinzu."""
        state.parent = self
        self.substates[state.name] = state
        if is_initial:
            self.initial_substate = state.name
    
    def save_history(self, state_name: str) -> None:
        """Speichert den letzten aktiven Subzustand für [H]."""
        self._history = state_name
    
    def get_history_state(self) -> Optional[str]:
        """Gibt den History State zurück oder den initialen Subzustand."""
        return self._history or self.initial_substate
    
    def on_entry(self, machine: StateMachine) -> None:
        """Entry: Betritt auch den initialen/history Subzustand."""
        super().on_entry(machine)
        # Bei Composite States wird der initiale Subzustand automatisch betreten
        if self.initial_substate:
            substate = self.substates.get(self.initial_substate)
            if substate:
                substate.on_entry(machine)


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MACHINE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class StateMachine:
    """
    State Machine Engine.
    
    Verarbeitet Events und führt Zustandsübergänge mit korrekter
    Entry/Exit Action-Reihenfolge aus.
    
    Usage:
        sm = StateMachine("MyMachine")
        sm.add_state(State("A"))
        sm.add_transition("A", "B", "go")
        sm.start()
        sm.send("go")
    """
    
    def __init__(self, name: str = "StateMachine"):
        self.name = name
        self._states: dict[str, State] = {}
        self._transitions: list[Transition] = []
        self._current_state: Optional[State] = None
        self._initial_state_name: Optional[str] = None
        self._context: dict[str, Any] = {}  # Für Guard-Auswertung
        self._listeners: list[Callable] = []
    
    # ─────────────────────────────────────────────────────────────────────────
    # Configuration API
    # ─────────────────────────────────────────────────────────────────────────
    
    def add_state(self, state: State) -> StateMachine:
        """Fügt einen Zustand hinzu."""
        self._states[state.name] = state
        return self
    
    def set_initial_state(self, state_name: str) -> StateMachine:
        """Setzt den Initialzustand ([*] --> State)."""
        self._initial_state_name = state_name
        return self
    
    def add_transition(
        self,
        source: str,
        target: str,
        event: str,
        guard: Optional[Callable[[dict], bool]] = None,
        action: Optional[Callable[[], None]] = None
    ) -> StateMachine:
        """
        Fügt eine Transition hinzu.
        
        Args:
            source: Quellzustand
            target: Zielzustand  
            event: Event-Name (z.B. "schließen")
            guard: Optionaler Guard [Bedingung]
            action: Optionale Transitionsaktion
        """
        transition = Transition(source, target, event, guard, action)
        self._transitions.append(transition)
        return self
    
    def set_context_var(self, key: str, value: Any) -> None:
        """Setzt eine Kontextvariable für Guards."""
        self._context[key] = value
    
    def get_context_var(self, key: str, default: Any = None) -> Any:
        """Liest eine Kontextvariable."""
        return self._context.get(key, default)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Runtime API  
    # ─────────────────────────────────────────────────────────────────────────
    
    def start(self) -> None:
        """Startet die State Machine im Initialzustand."""
        if not self._initial_state_name:
            raise RuntimeError("Kein Initialzustand definiert!")
        
        if self._initial_state_name not in self._states:
            raise RuntimeError(f"Initialzustand '{self._initial_state_name}' nicht gefunden!")
        
        self._current_state = self._states[self._initial_state_name]
        self._log(f"Gestartet")
        self._current_state.on_entry(self)
        self._log(f"Aktueller Zustand: {self._current_state.name}")
    
    def send(self, event: str) -> bool:
        """
        Sendet ein Event an die State Machine.
        
        Returns:
            True wenn eine Transition ausgeführt wurde
        """
        if not self._current_state:
            self._log("FEHLER: State Machine nicht gestartet!")
            return False
        
        self._log(f"Event empfangen: '{event}'")
        
        # Finde passende Transition
        for transition in self._transitions:
            if self._matches_transition(transition, event):
                if transition.can_fire(self._context):
                    self._execute_transition(transition)
                    return True
                else:
                    self._log(f"  ✗ Guard verhindert Transition")
        
        self._log(f"  ✗ Keine Transition für '{event}' im Zustand '{self._current_state.name}'")
        return False
    
    def _matches_transition(self, transition: Transition, event: str) -> bool:
        """Prüft, ob eine Transition zum aktuellen Zustand und Event passt."""
        return (
            transition.source == self._current_state.name and
            transition.event == event
        )
    
    def _execute_transition(self, transition: Transition) -> None:
        """Führt eine Transition aus mit korrekter Action-Reihenfolge."""
        self._log(f"  Transition: {transition.source} ──[{transition.event}]──► {transition.target}")
        
        # 1. Exit-Action des Quellzustands
        self._current_state.on_exit(self)
        
        # 2. History speichern (für Composite States)
        if self._current_state.parent:
            self._current_state.parent.save_history(self._current_state.name)
        
        # 3. Transitionsaktion
        if transition.action:
            transition.action()
        
        # 4. Neuen Zustand setzen
        self._current_state = self._states[transition.target]
        
        # 5. Entry-Action des Zielzustands
        self._current_state.on_entry(self)
        
        self._log(f"  Aktueller Zustand: {self._current_state.name}")
    
    @property
    def current_state(self) -> Optional[str]:
        """Gibt den Namen des aktuellen Zustands zurück."""
        return self._current_state.name if self._current_state else None
    
    def _log(self, message: str) -> None:
        """Interne Log-Ausgabe."""
        print(f"[{self.name}] {message}")


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATED STATE MACHINE: Türschloss
# ═══════════════════════════════════════════════════════════════════════════════

class TürschlossStateMachine(StateMachine):
    """
    State Machine generiert aus PlantUML:
    
        state Auf
        state Zu  
        state Verriegelt
        
        [*] --> Auf
        Auf --> Zu : schließen
        Zu --> Verriegelt : verriegeln
        Verriegelt --> Zu : entriegeln
        Zu --> Auf : öffnen
    """
    
    def __init__(self):
        super().__init__("Türschloss")
        self._build()
    
    def _build(self) -> None:
        """Konstruiert die State Machine aus der PlantUML-Spezifikation."""
        
        # ─── Zustände ───
        self.add_state(State("Auf"))
        self.add_state(State("Zu"))
        self.add_state(State("Verriegelt"))
        
        # ─── Initialzustand ───
        self.set_initial_state("Auf")
        
        # ─── Transitionen ───
        self.add_transition("Auf", "Zu", "schließen")
        self.add_transition("Zu", "Verriegelt", "verriegeln")
        self.add_transition("Verriegelt", "Zu", "entriegeln")
        self.add_transition("Zu", "Auf", "öffnen")
    
    # ─── Convenience Methods (matching PlantUML event names) ───
    
    def schließen(self) -> bool:
        """Event: schließen (Auf → Zu)"""
        return self.send("schließen")
    
    def verriegeln(self) -> bool:
        """Event: verriegeln (Zu → Verriegelt)"""
        return self.send("verriegeln")
    
    def entriegeln(self) -> bool:
        """Event: entriegeln (Verriegelt → Zu)"""
        return self.send("entriegeln")
    
    def öffnen(self) -> bool:
        """Event: öffnen (Zu → Auf)"""
        return self.send("öffnen")


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO & TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  TÜRSCHLOSS STATE MACHINE - Demo")
    print("=" * 60)
    
    # State Machine erstellen und starten
    tür = TürschlossStateMachine()
    tür.start()
    
    print("\n" + "─" * 60)
    print("  Valide Transition-Sequenz")
    print("─" * 60)
    
    tür.schließen()      # Auf → Zu
    tür.verriegeln()     # Zu → Verriegelt
    tür.entriegeln()     # Verriegelt → Zu
    tür.öffnen()         # Zu → Auf
    
    print("\n" + "─" * 60)
    print("  Invalide Transition (Guard-Test)")  
    print("─" * 60)
    
    tür.verriegeln()     # Sollte fehlschlagen (kann nicht verriegeln wenn offen)
    
    print("\n" + "=" * 60)
    print(f"  Endzustand: {tür.current_state}")
    print("=" * 60)