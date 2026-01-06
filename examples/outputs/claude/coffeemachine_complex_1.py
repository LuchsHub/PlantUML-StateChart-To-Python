#!/usr/bin/env python3
"""
Hierarchische State Machine für Kaffeemaschine
Basierend auf PlantUML-Spezifikation mit Composite States, History und Guards

Autor: State Machine Generator
"""

from typing import Callable, Dict, List, Optional
from abc import ABC


# ============================================================================
#  KERN-KLASSEN DER STATE MACHINE
# ============================================================================

class State:
    """Basisklasse für alle Zustände."""
    
    def __init__(self, name: str):
        self.name = name
        self.parent: Optional['CompositeState'] = None
        self._entry_actions: List[Callable[[], None]] = []
        self._exit_actions: List[Callable[[], None]] = []
    
    def add_entry_action(self, action: Callable[[], None]) -> 'State':
        """Fügt Entry-Action hinzu. Gibt self für Method-Chaining zurück."""
        self._entry_actions.append(action)
        return self
    
    def add_exit_action(self, action: Callable[[], None]) -> 'State':
        """Fügt Exit-Action hinzu. Gibt self für Method-Chaining zurück."""
        self._exit_actions.append(action)
        return self
    
    def on_entry(self) -> None:
        """Führt alle Entry-Actions aus."""
        for action in self._entry_actions:
            action()
    
    def on_exit(self) -> None:
        """Führt alle Exit-Actions aus."""
        for action in self._exit_actions:
            action()
    
    def get_ancestor_chain(self) -> List['State']:
        """Gibt Kette von self bis zur Wurzel zurück."""
        chain = [self]
        current = self.parent
        while current is not None:
            chain.append(current)
            current = current.parent
        return chain
    
    def __repr__(self) -> str:
        return f"State({self.name})"


class CompositeState(State):
    """Zusammengesetzter Zustand mit Unterzuständen und History-Unterstützung."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.substates: Dict[str, State] = {}
        self.initial_state: Optional[State] = None
        self._history: Optional[State] = None  # [H] History State
    
    def add_substate(self, state: State, is_initial: bool = False) -> 'CompositeState':
        """Fügt Unterzustand hinzu."""
        state.parent = self
        self.substates[state.name] = state
        if is_initial:
            self.initial_state = state
        return self
    
    def save_history(self, state: State) -> None:
        """Speichert History-Zustand für [H]."""
        self._history = state
    
    def get_entry_target(self, use_history: bool = False) -> Optional[State]:
        """Gibt Eintritts-Zielzustand zurück (History oder Initial)."""
        if use_history and self._history is not None:
            return self._history
        return self.initial_state
    
    def __repr__(self) -> str:
        return f"CompositeState({self.name})"


class Transition:
    """Repräsentiert einen Zustandsübergang."""
    
    def __init__(self, 
                 event: str, 
                 source: State, 
                 target: State,
                 guard: Optional[Callable[[], bool]] = None,
                 use_history: bool = False):
        self.event = event
        self.source = source
        self.target = target
        self.guard = guard          # [Bedingung]
        self.use_history = use_history  # [H]
    
    def is_enabled(self) -> bool:
        """Prüft ob Guard-Bedingung erfüllt ist."""
        return self.guard is None or self.guard()
    
    def __repr__(self) -> str:
        guard_str = f" [{self.guard.__name__}]" if self.guard else ""
        history_str = "[H]" if self.use_history else ""
        return f"{self.source.name} --> {self.target.name}{history_str} : {self.event}{guard_str}"


class StateMachine:
    """Generische hierarchische State Machine mit History-Unterstützung."""
    
    def __init__(self, name: str):
        self.name = name
        self.states: Dict[str, State] = {}
        self.transitions: List[Transition] = []
        self.current_state: Optional[State] = None
        self.log_enabled: bool = True
    
    def add_state(self, state: State) -> 'StateMachine':
        """Fügt Top-Level-Zustand hinzu."""
        self.states[state.name] = state
        return self
    
    def add_transition(self, transition: Transition) -> 'StateMachine':
        """Fügt Transition hinzu."""
        self.transitions.append(transition)
        return self
    
    def _log(self, message: str) -> None:
        if self.log_enabled:
            print(message)
    
    def is_in_state(self, state: State) -> bool:
        """Prüft ob aktueller Zustand gleich oder Unterzustand von state ist."""
        if self.current_state is None:
            return False
        return state in self.current_state.get_ancestor_chain()
    
    def initialize(self, initial_state: State) -> None:
        """Initialisiert die State Machine mit Startzustand."""
        self._log(f"\n{'='*50}")
        self._log(f" Initialisiere: {self.name}")
        self._log(f"{'='*50}")
        self._enter_state(initial_state, use_history=False)
    
    def _enter_state(self, state: State, use_history: bool = False) -> None:
        """Betritt Zustand rekursiv (inkl. Unterzustände)."""
        self._log(f"  ▶ ENTER: {state.name}")
        state.on_entry()
        
        if isinstance(state, CompositeState):
            substate = state.get_entry_target(use_history)
            if substate:
                self._enter_state(substate, use_history)
        else:
            self.current_state = state
    
    def _exit_state(self, state: State) -> None:
        """Verlässt Zustand."""
        self._log(f"  ◀ EXIT:  {state.name}")
        state.on_exit()
    
    def dispatch(self, event: str) -> bool:
        """
        Verarbeitet ein Event und führt ggf. Transition aus.
        Gibt True zurück wenn Transition ausgeführt wurde.
        """
        self._log(f"\n┌─ Event: {event}")
        self._log(f"│  Aktuell: {self.get_state_path()}")
        
        # Passende Transition finden
        for transition in self.transitions:
            if transition.event != event:
                continue
            if not self.is_in_state(transition.source):
                continue
            if not transition.is_enabled():
                self._log(f"│  ✗ Guard blockiert")
                continue
            
            # Transition ausführen
            self._execute_transition(transition)
            self._log(f"└─ Neu: {self.get_state_path()}")
            return True
        
        self._log(f"└─ ✗ Kein Übergang gefunden")
        return False
    
    def _execute_transition(self, transition: Transition) -> None:
        """Führt Zustandsübergang aus."""
        source = transition.source
        target = transition.target
        
        # States zum Verlassen sammeln (von current bis einschl. source)
        exit_chain: List[State] = []
        current = self.current_state
        
        while current is not None:
            exit_chain.append(current)
            # History in Composite-Parent speichern
            if isinstance(current.parent, CompositeState):
                current.parent.save_history(current)
            if current == source:
                break
            current = current.parent
        
        # Bei Composite-Source: aktuellen Unterzustand als History speichern
        if isinstance(source, CompositeState):
            source.save_history(self.current_state)
        
        # States verlassen (in gesammelter Reihenfolge)
        for state in exit_chain:
            self._exit_state(state)
        
        # Zielzustand betreten
        self._enter_state(target, transition.use_history)
    
    def get_state_path(self) -> str:
        """Gibt aktuellen Zustandspfad als String zurück."""
        if self.current_state is None:
            return "[---]"
        chain = self.current_state.get_ancestor_chain()
        chain.reverse()
        return " → ".join(s.name for s in chain)


# ============================================================================
#  KAFFEEMASCHINE IMPLEMENTATION
# ============================================================================

class ActionHandler:
    """
    Separate Klasse für Action-Methoden.
    Trennt Aktions-Logik von Zustandsverwaltung.
    """
    
    def piepen(self) -> None:
        """Exit-Action: Akustisches Signal."""
        print("      🔔 piepen()")
    
    def wasserReinigen(self) -> None:
        """Entry-Action: Wasser reinigen beim Einschalten."""
        print("      💧 wasserReinigen()")


class KaffeeMaschine:
    """
    Kaffeemaschine State Machine
    
    Zustandsdiagramm:
    ┌─────────────────────────────────────────┐
    │  [*] → Aus                              │
    │         │ anschalten                    │
    │         ▼                               │
    │  ┌─────────────────────────────────┐    │
    │  │ An                              │    │
    │  │  [*] → Leerlauf ←──┐            │    │
    │  │         │    │     │            │    │
    │  │         │    └─────┘            │    │
    │  │         │ kaffeeMachen          │    │
    │  │         │ [wasser > 20]         │    │
    │  │         ▼                       │    │
    │  │      Zubereitung                │    │
    │  │         │                       │    │
    │  │         │ zubereitungAbschließen│    │
    │  │         ▼                       │    │
    │  │      Ausgabe ───────────────────┘    │
    │  │         kaffeeEntnehmen              │
    │  └─────────────────────────────────┘    │
    │         │ stop          ▲               │
    │         ▼               │ fortfahren    │
    │       Pause ────────────┘ [H]           │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self):
        # Kontext-Daten
        self.wasser: int = 100
        
        # Action Handler (trennt Logik von Zustandsverwaltung)
        self.actions = ActionHandler()
        
        # State Machine aufbauen
        self._build_states()
        self._setup_actions()
        self._build_transitions()
        
        # Initial: [*] --> Aus
        self._sm.initialize(self.Aus)
    
    def _build_states(self) -> None:
        """Erstellt Zustandshierarchie gemäß PlantUML."""
        
        # === Top-Level States ===
        self.Aus = State("Aus")
        self.Pause = State("Pause")
        
        # === Composite State: An ===
        self.An = CompositeState("An")
        
        # Substates von An
        self.Leerlauf = State("Leerlauf")
        self.Zubereitung = State("Zubereitung")
        self.Ausgabe = State("Ausgabe")
        
        # Hierarchie: An enthält Leerlauf, Zubereitung, Ausgabe
        # [*] --> Leerlauf (initial)
        self.An.add_substate(self.Leerlauf, is_initial=True)
        self.An.add_substate(self.Zubereitung)
        self.An.add_substate(self.Ausgabe)
        
        # State Machine erstellen
        self._sm = StateMachine("Kaffeemaschine")
        self._sm.add_state(self.Aus)
        self._sm.add_state(self.An)
        self._sm.add_state(self.Pause)
    
    def _setup_actions(self) -> None:
        """Konfiguriert Entry/Exit Actions gemäß PlantUML."""
        
        # Aus: Exit: piepen
        self.Aus.add_exit_action(self.actions.piepen)
        
        # An: Entry: wasserReinigen
        self.An.add_entry_action(self.actions.wasserReinigen)
        
        # An: Exit: piepen
        self.An.add_exit_action(self.actions.piepen)
    
    def _build_transitions(self) -> None:
        """Definiert Übergänge gemäß PlantUML."""
        
        # Aus --> An : anschalten
        self._sm.add_transition(Transition(
            event="anschalten",
            source=self.Aus,
            target=self.An
        ))
        
        # Leerlauf --> Leerlauf : wasserAuffüllen
        self._sm.add_transition(Transition(
            event="wasserAuffüllen",
            source=self.Leerlauf,
            target=self.Leerlauf
        ))
        
        # Leerlauf --> Zubereitung : kaffeeMachen [wasser > 20]
        self._sm.add_transition(Transition(
            event="kaffeeMachen",
            source=self.Leerlauf,
            target=self.Zubereitung,
            guard=lambda: self.wasser > 20  # Guard-Bedingung
        ))
        
        # Zubereitung --> Ausgabe : zubereitungAbschließen
        self._sm.add_transition(Transition(
            event="zubereitungAbschließen",
            source=self.Zubereitung,
            target=self.Ausgabe
        ))
        
        # Ausgabe --> Leerlauf : kaffeeEntnehmen
        self._sm.add_transition(Transition(
            event="kaffeeEntnehmen",
            source=self.Ausgabe,
            target=self.Leerlauf
        ))
        
        # An --> Pause : stop
        self._sm.add_transition(Transition(
            event="stop",
            source=self.An,
            target=self.Pause
        ))
        
        # Pause --> An[H] : fortfahren
        self._sm.add_transition(Transition(
            event="fortfahren",
            source=self.Pause,
            target=self.An,
            use_history=True  # [H] History State
        ))
    
    # ==================== Öffentliche API ====================
    
    def trigger(self, event: str) -> bool:
        """Sendet Event an State Machine."""
        return self._sm.dispatch(event)
    
    def set_wasser(self, level: int) -> None:
        """Setzt Wasserstand (für Guard-Tests)."""
        self.wasser = level
        print(f"\n📊 Wasserstand gesetzt: {self.wasser}")
    
    @property
    def zustand(self) -> str:
        """Aktueller Zustandspfad."""
        return self._sm.get_state_path()


# ============================================================================
#  TEST
# ============================================================================

def main():
    """Testet die Kaffeemaschine State Machine."""
    
    print("\n" + "═" * 60)
    print(" KAFFEEMASCHINE - STATE MACHINE TEST")
    print("═" * 60)
    
    maschine = KaffeeMaschine()
    
    # --- Test 1: Normaler Betriebsablauf ---
    print("\n" + "─" * 60)
    print(" TEST 1: Normaler Betriebsablauf")
    print("─" * 60)
    
    maschine.trigger("anschalten")          # Aus → An → Leerlauf
    maschine.trigger("wasserAuffüllen")     # Leerlauf → Leerlauf
    maschine.trigger("kaffeeMachen")        # Leerlauf → Zubereitung
    maschine.trigger("zubereitungAbschließen")  # Zubereitung → Ausgabe
    maschine.trigger("kaffeeEntnehmen")     # Ausgabe → Leerlauf
    
    # --- Test 2: History State ---
    print("\n" + "─" * 60)
    print(" TEST 2: Pause mit History [H]")
    print("─" * 60)
    
    maschine.trigger("kaffeeMachen")        # Leerlauf → Zubereitung
    maschine.trigger("zubereitungAbschließen")  # Zubereitung → Ausgabe
    maschine.trigger("stop")                # An(Ausgabe) → Pause [speichert History]
    maschine.trigger("fortfahren")          # Pause → An[H] → Ausgabe [History]
    maschine.trigger("kaffeeEntnehmen")     # Ausgabe → Leerlauf
    
    # --- Test 3: Guard-Bedingung ---
    print("\n" + "─" * 60)
    print(" TEST 3: Guard [wasser > 20]")
    print("─" * 60)
    
    maschine.set_wasser(10)                 # Unter Schwellwert
    maschine.trigger("kaffeeMachen")        # ✗ Guard blockiert
    
    maschine.set_wasser(50)                 # Über Schwellwert
    maschine.trigger("kaffeeMachen")        # ✓ Leerlauf → Zubereitung
    
    # --- Test 4: Ungültiges Event ---
    print("\n" + "─" * 60)
    print(" TEST 4: Ungültiges Event")
    print("─" * 60)
    
    maschine.trigger("unbekanntes_event")   # Kein Übergang
    
    print("\n" + "═" * 60)
    print(" ALLE TESTS ABGESCHLOSSEN")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    main()