from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def __init__(self, context):
        pass

    def entry(self, use_history=False):
        pass

    def exit(self):
        pass

    def dispatch(self, event: str):
        pass


class SimpleState(State):
    def __init__(self, context):
        self.context = context


class CompositeState(State):
    @property
    def state(self) -> State:
        return self._state

    # __init__ bleibt abstrakt: konkrete Unterzustände + Startzustand müssen implementiert werden

    @abstractmethod
    def entry(self, use_history=False):
        pass

    def dispatch(self, event: str):
        self._state.dispatch(event)

    def transition(self, new_state: State, use_history=False):
        self._state.exit()
        self._state = new_state
        self._state.entry(use_history)


class CompositeStateWithHistory(CompositeState):
    @property
    def history(self) -> State:
        return self._history

    # __init__ bleibt abstrakt: konkrete Unterzustände + Startzustand müssen implementiert werden

    def transition(self, new_state: State, use_history=False):
        self._state.exit()
        self._state = new_state
        self._history = self._state
        self._state.entry(use_history)


class Aus(SimpleState):
    def exit(self):
        piepen()

    def dispatch(self, event: str):
        if event == "anschalten":
            self.context.transition(self.context.an)


class An(CompositeStateWithHistory):
    def __init__(self, context):
        self.context = context

        self.leerlauf = Leerlauf(self)
        self.zubereitung = Zubereitung(self)
        self.ausgabe = Ausgabe(self)
        self._state = None
        self._history = None

        self.wasser = 0 
            
    def entry(self, use_history=False):
        wasserReinigen()

        if use_history:
            self._state = self._history
        else:
            self._state = self.leerlauf

        self._state.entry()

    
    def dispatch(self, event: str):
        if event == "stop":
            self._state.exit()
            self.context.transition(self.context.pause)
        else: 
            self._state.dispatch(event)


class Leerlauf(SimpleState):
    def dispatch(self, event: str):
        if event == "wasserAuffüllen":
            self.context.transition(self.context.leerlauf)
        elif event == "kaffeeMachen" and self.context.wasser > 20:
            self.context.transition(self.context.zubereitung)


class Zubereitung(SimpleState):
    def dispatch(self, event: str):
        if event == "zubereitungAbschließen":
            self.context.transition(self.context.ausgabe)


class Ausgabe(SimpleState):
    def dispatch(self, event: str):
        if event == "kaffeeEntnehmen":
            self.context.transition(self.context.leerlauf)


class Pause(SimpleState):
    def dispatch(self, event: str):
        if event == "fortfahren":
            self.context.transition(self.context.an, use_history=True)


class StateMachine:
    def __init__(self):
        self.aus = Aus(self)
        self.an = An(self)
        self.pause = Pause(self)

        self._state = self.aus
        self._state.entry()

    def dispatch(self, event: str):
        self._state.dispatch(event)

    def transition(self, new_state: State, use_history=False):
        self._state.exit()
        self._state = new_state
        self._state.entry(use_history)


def piepen():
    pass


def wasserReinigen():
    pass


sm = StateMachine()
print(sm._state.__class__.__name__)  # Aus
sm.dispatch("anschalten")
print(sm._state.__class__.__name__)  # An
print(sm._state.state.__class__.__name__)  # Unterzustand Leerlauf
sm.dispatch("kaffeeMachen")
print(sm._state.state.__class__.__name__)  # Unterzustand Leerlauf
sm.an.wasser = 50  # Wasser auffüllen
sm.dispatch("kaffeeMachen")
print(sm._state.state.__class__.__name__)  # Unterzustand Zubereitung
sm.dispatch("stop")
print(sm._state.__class__.__name__) # Pause
sm.dispatch("fortfahren")
print(sm._state.state.__class__.__name__)  # Unterzustand Zubereitung
