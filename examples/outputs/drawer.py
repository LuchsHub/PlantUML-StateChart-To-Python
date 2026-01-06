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


class Auf(SimpleState):
    def dispatch(self, event: str):
        if event == "schließen":
            self.context.transition(self.context.zu)


class Zu(SimpleState):
    def dispatch(self, event: str):
        if event == "verriegeln":
            self.context.transition(self.context.verriegelt)
        elif event == "öffnen":
            self.context.transition(self.context.auf)


class Verriegelt(SimpleState):
    def dispatch(self, event: str):
        if event == "entriegeln":
            self.context.transition(self.context.zu)


class StateMachine:
    def __init__(self):
        self.auf = Auf(self)
        self.zu = Zu(self)
        self.verriegelt = Verriegelt(self)
        self.state = self.auf
        self.state.entry()

    def dispatch(self, event: str):
        self.state.dispatch(event)

    def transition(self, new_state: State, use_hist: bool = False):
        self.state.exit()
        self.state = new_state
        self.state.entry(use_hist)

