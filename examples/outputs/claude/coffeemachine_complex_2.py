"""
State Machine Implementation for Coffee Machine
Based on PlantUML specification with support for:
- Simple states
- Composite states with hierarchy
- History states [H]
- Guards [condition]
- Entry/Exit actions
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict, Any


# ============================================================================
# ACTION METHODS (Business Logic - separated from state management)
# ============================================================================

class CoffeeMachineActions:
    """Contains all action methods referenced in the state machine."""
    
    def __init__(self):
        self.wasser = 100  # Water level for guard conditions
    
    def piepen(self):
        """Exit action for 'Aus' and 'An' states."""
        print("  [ACTION] piepen: *BEEP*")
    
    def wasserReinigen(self):
        """Entry action for 'An' state."""
        print("  [ACTION] wasserReinigen: Reinige Wassersystem...")


# ============================================================================
# STATE PATTERN - BASE CLASSES
# ============================================================================

class State(ABC):
    """Abstract base class for all states."""
    
    def __init__(self, name: str, machine: 'CoffeeMachine'):
        self.name = name
        self.machine = machine
    
    def on_entry(self):
        """Called when entering this state."""
        print(f"  -> Entering state: {self.name}")
    
    def on_exit(self):
        """Called when exiting this state."""
        print(f"  <- Exiting state: {self.name}")
    
    def handle_event(self, event: str) -> bool:
        """
        Handle an event. Returns True if transition occurred.
        Override in subclasses for specific event handling.
        """
        return False
    
    def get_full_state_path(self) -> str:
        """Returns the full hierarchical state path."""
        return self.name


class CompositeState(State):
    """A state that contains substates."""
    
    def __init__(self, name: str, machine: 'CoffeeMachine'):
        super().__init__(name, machine)
        self.substates: Dict[str, State] = {}
        self.initial_substate: Optional[str] = None
        self.current_substate: Optional[State] = None
        self.history_substate: Optional[str] = None
    
    def add_substate(self, state: State, is_initial: bool = False):
        """Add a substate to this composite state."""
        self.substates[state.name] = state
        if is_initial:
            self.initial_substate = state.name
    
    def on_entry(self, use_history: bool = False):
        """Enter composite state, optionally using history."""
        super().on_entry()
        
        # Determine which substate to enter
        if use_history and self.history_substate:
            target = self.history_substate
            print(f"  [HISTORY] Restoring to: {target}")
        elif self.initial_substate:
            target = self.initial_substate
        else:
            return
        
        self.current_substate = self.substates[target]
        self.current_substate.on_entry()
    
    def on_exit(self):
        """Exit composite state, saving history."""
        if self.current_substate:
            # Save history before exiting
            self.history_substate = self.current_substate.name
            self.current_substate.on_exit()
            self.current_substate = None
        super().on_exit()
    
    def transition_to_substate(self, target_name: str):
        """Transition between substates."""
        if self.current_substate:
            self.current_substate.on_exit()
        
        self.current_substate = self.substates[target_name]
        self.current_substate.on_entry()
    
    def handle_event(self, event: str) -> bool:
        """First let current substate handle, then try own transitions."""
        if self.current_substate:
            if self.current_substate.handle_event(event):
                return True
        return False
    
    def get_full_state_path(self) -> str:
        """Returns the full hierarchical state path."""
        if self.current_substate:
            return f"{self.name}.{self.current_substate.get_full_state_path()}"
        return self.name


# ============================================================================
# CONCRETE STATES
# ============================================================================

class AusState(State):
    """'Aus' (Off) state."""
    
    def __init__(self, machine: 'CoffeeMachine'):
        super().__init__("Aus", machine)
    
    def on_exit(self):
        super().on_exit()
        self.machine.actions.piepen()  # Exit: piepen
    
    def handle_event(self, event: str) -> bool:
        if event == "anschalten":
            self.machine.transition_to("An")
            return True
        return False


class PauseState(State):
    """'Pause' state."""
    
    def __init__(self, machine: 'CoffeeMachine'):
        super().__init__("Pause", machine)
    
    def handle_event(self, event: str) -> bool:
        if event == "fortfahren":
            self.machine.transition_to("An", use_history=True)
            return True
        return False


# --- Substates of 'An' (On) ---

class LeerlaufState(State):
    """'Leerlauf' (Idle) substate of 'An'."""
    
    def __init__(self, machine: 'CoffeeMachine'):
        super().__init__("Leerlauf", machine)
    
    def handle_event(self, event: str) -> bool:
        if event == "wasserAuffüllen":
            # Self-transition: Leerlauf --> Leerlauf
            print(f"  [SELF-TRANSITION] {self.name} -> {self.name}")
            self.machine.actions.wasser += 50
            print(f"  [INFO] Wasserstand: {self.machine.actions.wasser}")
            return True
        
        if event == "kaffeeMachen":
            # Guard: [wasser > 20]
            if self.machine.actions.wasser > 20:
                print(f"  [GUARD] wasser > 20: PASSED (wasser={self.machine.actions.wasser})")
                an_state = self.machine.states["An"]
                an_state.transition_to_substate("Zubereitung")
                return True
            else:
                print(f"  [GUARD] wasser > 20: FAILED (wasser={self.machine.actions.wasser})")
                return False
        
        return False


class ZubereitungState(State):
    """'Zubereitung' (Preparation) substate of 'An'."""
    
    def __init__(self, machine: 'CoffeeMachine'):
        super().__init__("Zubereitung", machine)
    
    def handle_event(self, event: str) -> bool:
        if event == "zubereitungAbschließen":
            # Consume water
            self.machine.actions.wasser -= 25
            print(f"  [INFO] Wasserstand nach Zubereitung: {self.machine.actions.wasser}")
            
            an_state = self.machine.states["An"]
            an_state.transition_to_substate("Ausgabe")
            return True
        return False


class AusgabeState(State):
    """'Ausgabe' (Dispensing) substate of 'An'."""
    
    def __init__(self, machine: 'CoffeeMachine'):
        super().__init__("Ausgabe", machine)
    
    def handle_event(self, event: str) -> bool:
        if event == "kaffeeEntnehmen":
            an_state = self.machine.states["An"]
            an_state.transition_to_substate("Leerlauf")
            return True
        return False


class AnState(CompositeState):
    """'An' (On) composite state containing Leerlauf, Zubereitung, Ausgabe."""
    
    def __init__(self, machine: 'CoffeeMachine'):
        super().__init__("An", machine)
        
        # Create and add substates
        self.add_substate(LeerlaufState(machine), is_initial=True)
        self.add_substate(ZubereitungState(machine))
        self.add_substate(AusgabeState(machine))
    
    def on_entry(self, use_history: bool = False):
        print(f"  -> Entering state: {self.name}")
        self.machine.actions.wasserReinigen()  # Entry: wasserReinigen
        
        # Enter appropriate substate
        if use_history and self.history_substate:
            target = self.history_substate
            print(f"  [HISTORY] Restoring to: {target}")
        elif self.initial_substate:
            target = self.initial_substate
        else:
            return
        
        self.current_substate = self.substates[target]
        self.current_substate.on_entry()
    
    def on_exit(self):
        if self.current_substate:
            self.history_substate = self.current_substate.name
            self.current_substate.on_exit()
            self.current_substate = None
        
        print(f"  <- Exiting state: {self.name}")
        self.machine.actions.piepen()  # Exit: piepen
    
    def handle_event(self, event: str) -> bool:
        # First, let substate handle
        if super().handle_event(event):
            return True
        
        # Handle transition out of 'An'
        if event == "stop":
            self.machine.transition_to("Pause")
            return True
        
        return False


# ============================================================================
# STATE MACHINE
# ============================================================================

class CoffeeMachine:
    """
    Coffee Machine State Machine.
    Manages states, transitions, and event processing.
    """
    
    def __init__(self):
        self.actions = CoffeeMachineActions()
        self.states: Dict[str, State] = {}
        self.current_state: Optional[State] = None
        
        self._initialize_states()
        self._initialize_to_start_state()
    
    def _initialize_states(self):
        """Create all states."""
        self.states["Aus"] = AusState(self)
        self.states["An"] = AnState(self)
        self.states["Pause"] = PauseState(self)
    
    def _initialize_to_start_state(self):
        """Set initial state: [*] --> Aus"""
        print("=== Initializing State Machine ===")
        self.current_state = self.states["Aus"]
        self.current_state.on_entry()
        print(f"=== Current State: {self.get_current_state_path()} ===\n")
    
    def transition_to(self, target_name: str, use_history: bool = False):
        """Execute a transition to a new state."""
        print(f"\n--- Transition: {self.current_state.name} --> {target_name} ---")
        
        # Exit current state
        if self.current_state:
            self.current_state.on_exit()
        
        # Enter new state
        self.current_state = self.states[target_name]
        
        if isinstance(self.current_state, CompositeState):
            self.current_state.on_entry(use_history=use_history)
        else:
            self.current_state.on_entry()
        
        print(f"--- Current State: {self.get_current_state_path()} ---\n")
    
    def process_event(self, event: str):
        """Process an incoming event."""
        print(f"\n>>> Event: '{event}'")
        
        handled = self.current_state.handle_event(event)
        
        if not handled:
            print(f"  [WARNING] Event '{event}' not handled in state '{self.get_current_state_path()}'")
        
        print(f">>> Current State: {self.get_current_state_path()}\n")
    
    def get_current_state_path(self) -> str:
        """Get the full hierarchical state path."""
        if self.current_state:
            return self.current_state.get_full_state_path()
        return "None"
    
    def get_water_level(self) -> int:
        """Get current water level (for testing guards)."""
        return self.actions.wasser


# ============================================================================
# DEMONSTRATION
# ============================================================================

def main():
    """Demonstrate the state machine functionality."""
    
    print("=" * 60)
    print(" COFFEE MACHINE STATE MACHINE DEMO")
    print("=" * 60)
    
    # Create machine (starts in 'Aus')
    machine = CoffeeMachine()
    
    # Test sequence demonstrating all features
    test_events = [
        ("anschalten", "Turn on the machine"),
        ("wasserAuffüllen", "Fill water (self-transition)"),
        ("kaffeeMachen", "Make coffee (guard: wasser > 20)"),
        ("zubereitungAbschließen", "Finish preparation"),
        ("kaffeeEntnehmen", "Take coffee"),
        ("kaffeeMachen", "Make another coffee"),
        ("stop", "Pause the machine"),
        ("fortfahren", "Resume with history (should restore Zubereitung)"),
        ("zubereitungAbschließen", "Finish preparation after resume"),
        ("kaffeeEntnehmen", "Take coffee"),
    ]
    
    for event, description in test_events:
        print("=" * 60)
        print(f" {description}")
        print("=" * 60)
        machine.process_event(event)
        input("Press Enter to continue...")
    
    # Demonstrate guard failure
    print("=" * 60)
    print(" Testing Guard Failure")
    print("=" * 60)
    
    # Drain water
    machine.actions.wasser = 15
    print(f"\n[TEST] Set water level to: {machine.actions.wasser}")
    machine.process_event("kaffeeMachen")  # Should fail guard
    
    print("\n" + "=" * 60)
    print(" DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()