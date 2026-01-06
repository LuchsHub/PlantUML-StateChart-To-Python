import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from examples.outputs.own.drawer import StateMachine

def test_drawer():
    state_machine = StateMachine()
    print(state_machine.state)
    state_machine.dispatch("schließen")
    print(state_machine.state)
    state_machine.dispatch("verriegeln")
    print(state_machine.state)
    state_machine.dispatch("öffnen")
    print(state_machine.state)
    state_machine.dispatch("entriegeln")
    print(state_machine.state)
    state_machine.dispatch("öffnen")
    print(state_machine.state)

if __name__ == "__main__":
    test_drawer()