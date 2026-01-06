import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from examples.outputs.own.coffeemachine import StateMachine

def test_coffeemachine():
    state_machine = StateMachine()
    state_machine.dispatch("anschalten")
    print(state_machine.state.state)
    state_machine.dispatch("kaffeeMachen")
    print(state_machine.state.state)
    state_machine.dispatch("stop")
    print(state_machine.state)
    state_machine.dispatch("fortfahren")
    print(state_machine.state.state)
    state_machine.dispatch("zubereitungAbschließen")
    print(state_machine.state.state)
    state_machine.dispatch("kaffeeEntnehmen")
    print(state_machine.state.state)

if __name__ == "__main__":
    test_coffeemachine()