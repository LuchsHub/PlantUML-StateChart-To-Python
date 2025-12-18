from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def __init__(self, context):
        pass

    def entry(self):
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

    def dispatch(self, event: str):
        self._state.dispatch(event)

    def transition(self, new_state: State):
        self._state.exit()
        self._state = new_state
        self._state.entry()


class Aus(SimpleState):
    def exit(self):
        piepen()

    def dispatch(self, event: str):
        if event == "anschalten":
            self.context.transition(self.context.an)


class An(CompositeState):
    def __init__(self, context):
        self.context = context
        self.leerlauf = Leerlauf(self)
        self.zubereitung = Zubereitung(self)
        self.ausgabe = Ausgabe(self)

        self._state = self.leerlauf

    def entry(self):
        wasserReinigen()


class Leerlauf(SimpleState):
    def dispatch(self, event: str):
        if event == "wasserAuffüllen":
            self.context.transition(self.context.leerlauf)
        elif event == "kaffeeMachen":
            self.context.transition(self.context.zubereitung)


class Zubereitung(SimpleState):
    def dispatch(self, event: str):
        if event == "zubereitungAbschließen":
            self.context.transition(self.context.ausgabe)


class Ausgabe(SimpleState):
    def dispatch(self, event: str):
        if event == "kaffeeEntnehmen":
            self.context.transition(self.context.leerlauf)


class StateMachine:
    def __init__(self):
        self.aus = Aus(self)
        self.an = An(self)

        self._state = self.aus

    def dispatch(self, event: str):
        self._state.dispatch(event)

    def transition(self, new_state: State):
        self._state.exit()
        self._state = new_state
        self._state.entry()


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
print(sm._state.state.__class__.__name__)  # Unterzustand Zubereitung
