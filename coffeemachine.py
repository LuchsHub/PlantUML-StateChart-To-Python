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


class Aus_in_coffeemachine(SimpleState):
    def exit(self):
        piepen()


class An_in_coffeemachine(CompositeStateWithHistory):
    def __init__(self, context):
        self.context = context
        self.leerlauf_in_an = Leerlauf_in_an(self)
        self.zubereitung_in_an = Zubereitung_in_an(self)
        self.ausgabe_in_an = Ausgabe_in_an(self)
        self._state = None
        self._history = None

    def entry(self, use_history=False):
        wasserReinigen()

        if use_history:
            self._state = self._history
        else:
            self._state = self.leerlauf

        self._state.entry()


class Pause_in_coffeemachine(SimpleState):

class StateMachine:
    def __init__(self):
        self.aus_in_coffeemachine = Aus_in_coffeemachine(self)
        self.an_in_coffeemachine = An_in_coffeemachine(self)
        self.pause_in_coffeemachine = Pause_in_coffeemachine(self)
        self._state = self.aus
        self._state.entry()

    def dispatch(self, event: str):
        self._state.dispatch(event)

    def transition(self, new_state: State, use_hist: bool = False):
        self._state.exit()
        self._state = new_state
        self._state.entry(use_hist)


def wasserReinigen():
    pass


def piepen():
    pass

