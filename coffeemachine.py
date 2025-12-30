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


class Pause(SimpleState):
    def dispatch(self, event: str):
        if event == "fortfahren":
            self.context.transition(self.context.an, use_hist=True)


class StateMachine:
    def __init__(self):
        self.aus = Aus(self)
        self.an = An(self)
        self.pause = Pause(self)
        self._state = self.aus
        self._state.entry()

    def dispatch(self, event: str):
        self._state.dispatch(event)

    def transition(self, new_state: State, use_hist: bool = False):
        self._state.exit()
        self._state = new_state
        self._state.entry(use_hist)


def piepen():
    pass


def wasserReinigen():
    pass

