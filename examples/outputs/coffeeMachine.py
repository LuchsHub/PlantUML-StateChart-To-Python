from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def __init__(self, context):
        pass

    def entry(self, use_hist: bool = False):
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
    def entry(self, use_hist: bool = False):
        pass

    def exit(self):
        self.state.exit()

    def dispatch(self, event: str):
        self.state.dispatch(event)

    def transition(self, new_state: State, use_hist: bool = False):
        self.state.exit()
        self._state = new_state
        self.state.entry(use_hist)


class CompositeStateWithHistory(CompositeState):
    @property
    def history(self) -> State:
        return self._history

    def transition(self, new_state: State, use_hist: bool = False):
        self.state.exit()
        self._state = new_state
        self._history = self._state
        self.state.entry(use_hist)


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

    def entry(self, use_hist: bool = False):
        wasserReinigen()

        if use_hist:
            self._state = self._history
        else:
            self._state = self.leerlauf

        self.state.entry()

    def exit(self):
        self.state.exit()
        piepen()

    def dispatch(self, event: str):
        if event == "stop":
            self.context.transition(self.context.pause)
        else:
            self.state.dispatch(event)


class Leerlauf(SimpleState):
    def dispatch(self, event: str):
        if event == "wasserAuffüllen":
            self.context.transition(self.context.leerlauf)
        elif event == "kaffeeMachen":
            if self.context.wasser > 20:
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
            self.context.transition(self.context.an, use_hist=True)


class StateMachine:
    def __init__(self):
        self.aus = Aus(self)
        self.an = An(self)
        self.pause = Pause(self)
        self.state = self.aus
        self.state.entry()

    def dispatch(self, event: str):
        self.state.dispatch(event)

    def transition(self, new_state: State, use_hist: bool = False):
        self.state.exit()
        self.state = new_state
        self.state.entry(use_hist)


def piepen():
    pass


def wasserReinigen():
    pass

