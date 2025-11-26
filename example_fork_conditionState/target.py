import time
import threading
from enum import Enum, auto

# Top-Level-Zustände
class State(Enum):
    READY = auto()
    ERROR = auto()
    PREPARATION = auto()
    PAUSE = auto()
    SERVING = auto()

# Phasen von Preparation (nicht Zustände, da Fork als eine "Phase" behandelt wird)
class PreparationPhase(Enum):
    IDLE = auto()
    GRINDING = auto()
    FORK1 = auto() 

class CoffeeStateMachine:
    def __init__(self):
        # Initialzustand
        self._state = State.READY

        # ggf. Variablen für Condition States
        self.water = 0
        
        # ggf. History für Composite States
        self._preparation_history = PreparationPhase.IDLE
        
        self._stop_event = threading.Event() # besser als "bool stop" laut Gemini
        self._threads = [] # aktive Threads

        print(f"Machine ready in state: {self._state.name}")

    # Events = Public-Methoden

    def start(self):
        if self._state == State.READY:
            print("READY -> start()")
            if self.water == 0:
                print("  -> [Guard] water==0 -> ERROR")
                # Optional Business Logic...
                self._state = State.ERROR
            if self.water > 0:
                print("  -> [Guard] water>0 -> PREPARATION")
                # Optional Business Logic...
                self._state = State.PREPARATION
                self._enter_preparation(use_history=False)
        else:
            print(f"Ignored start in state {self._state.name}")

    def refill(self):
        if self._state == State.ERROR:
            print("ERROR -> refill() -> READY")
            # Optional Business Logic...
            self._state = State.READY
        else:
            print(f"Ignored refill in state {self._state.name}")

    def stop(self):
        if self._state == State.PREPARATION:
            print("PREPARATION -> stop() -> PAUSE")
            # Optional Business Logic...
            self._state = State.PAUSE
            self._stop_event.set() # stop = True
        else:
            print(f"Ignored stop in state {self._state.name}")

    def resume(self):
        if self._state == State.PAUSE:
            print("PAUSE -> resume() -> PREPARATION [History]")
            # Optional Business Logic...
            self._state = State.PREPARATION
            self._stop_event.clear() # stop = False
            self._enter_preparation(use_history=True)

    def drink(self):
        if self._state == State.SERVING:
            print("SERVING -> drink() -> READY")
            # Optional Business Logic...
            self._state = State.READY
        else:
            print(f"Ignored drink in state {self._state.name}")

    # Composite State Logik

    # _enter_X legt abhängig von History den Startzustand fest
    def _enter_preparation(self, use_history=False):
        start_phase = PreparationPhase.GRINDING
        
        if use_history and self._preparation_history != PreparationPhase.IDLE:
            start_phase = self._preparation_history

        self._run_preparation(start_phase)

    # _run_X geht durch die internen Zustände des Composite States
    def _run_preparation(self, phase):
        
        # PHASE 1: Grinding
        if phase == PreparationPhase.GRINDING:
            self._preparation_history = PreparationPhase.GRINDING
            if self._stop_event.is_set(): return
            print()
            # Optional Business Logic...
            phase = PreparationPhase.FORK1

        # PHASE 2: Fork 1
        if phase == PreparationPhase.FORK1:
            self._preparation_history = PreparationPhase.FORK1
            
            t_brew = threading.Thread(target=self._thread_preinfusion_extraction, name="PreInfusionExtractionThread")
            t_froth = threading.Thread(target=self._thread_frothingmilk, name="FrothingMilkThread")
            
            self._threads = [t_brew, t_froth]
            t_brew.start()
            t_froth.start()
            
            t_brew.join()
            t_froth.join()
                        
            if self._stop_event.is_set(): return
            # Optional Business Logic...
            self._state = State.SERVING
            self._preparation_history = PreparationPhase.IDLE

    # Fork-Sequenzen (beschränkt auf simple Zustände)

    def _thread_preinfusion_extraction(self):        
        if self._stop_event.is_set(): return
        # Optional Business Logic...
        
        if self._stop_event.is_set(): return
        # Optional Business Logic...
        

    def _thread_frothingmilk(self):
        if self._stop_event.is_set(): return
        # Optional Business Logic...
        
