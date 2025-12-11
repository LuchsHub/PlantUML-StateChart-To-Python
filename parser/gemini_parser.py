from dataclasses import dataclass, field
from typing import List, Optional, Dict
import re

@dataclass
class Transition:
    source: str
    target: str
    event: Optional[str] = None
    guard: Optional[str] = None

@dataclass
class StateNode:
    name: str
    is_composite: bool = False
    parent: Optional[str] = None
    entry_action: Optional[str] = None
    exit_action: Optional[str] = None
    substates: List['StateNode'] = field(default_factory=list)

@dataclass
class StateMachineAST:
    name: str
    states: Dict[str, StateNode] = field(default_factory=dict)
    transitions: List[Transition] = field(default_factory=list)

# --- Parser Implementation -- #
class PlantUMLParser:
    def __init__(self):
        # Regex-Patterns für dein Subset
        self.rx_state_def = re.compile(r'^state\s+(\w+)(?:\s*(\{))?') # Matches: state Name {
        self.rx_transition = re.compile(r'^([\w\[\]\*]+)\s*-->\s*([\w\[\]\*]+)(?:\s*:\s*(.*))?') # Matches: A --> B : Event [Guard]
        self.rx_action = re.compile(r'^(\w+)\s*:\s*(entry|exit)\s*:\s*(.+)') # Matches: Name : entry : func()
        self.rx_composite_end = re.compile(r'^\}')

    def parse(self, puml_content: str) -> StateMachineAST:
        ast = StateMachineAST(name="MyStateMachine")
        current_parent: Optional[StateNode] = None
        
        lines = puml_content.splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("'") or line.startswith("@"):
                continue

            # 1. State Definition (Simple oder Composite Start)
            match_state = self.rx_state_def.match(line)
            if match_state:
                name = match_state.group(1)
                is_composite_start = match_state.group(2) == "{"
                
                # State erstellen oder holen (falls er schon durch Transition bekannt war)
                if name not in ast.states:
                    new_state = StateNode(name=name, is_composite=is_composite_start)
                    ast.states[name] = new_state
                else:
                    ast.states[name].is_composite = is_composite_start
                    new_state = ast.states[name]

                # Hierarchie verknüpfen
                if current_parent:
                    new_state.parent = current_parent.name
                    current_parent.substates.append(new_state)
                
                if is_composite_start:
                    current_parent = new_state
                continue

            # 2. Composite End "}"
            if self.rx_composite_end.match(line):
                current_parent = None
                continue

            # 3. Entry / Exit Actions
            match_action = self.rx_action.match(line)
            if match_action:
                state_name = match_action.group(1)
                action_type = match_action.group(2) # "entry" oder "exit"
                func_call = match_action.group(3)

                # State muss existieren (PlantUML erlaubt Actions oft nach Definition)
                if state_name not in ast.states:
                     ast.states[state_name] = StateNode(name=state_name)
                
                if action_type == "entry":
                    ast.states[state_name].entry_action = func_call
                elif action_type == "exit":
                    ast.states[state_name].exit_action = func_call
                continue

            # 4. Transitions
            match_trans = self.rx_transition.match(line)
            if match_trans:
                source = match_trans.group(1)
                target = match_trans.group(2)
                label = match_trans.group(3) # "Event [Guard]" oder None

                event = None
                guard = None

                # Label zerlegen in Event und Guard
                if label:
                    # Check auf Guard [x > 0]
                    guard_match = re.search(r'\[(.*?)\]', label)
                    if guard_match:
                        guard = guard_match.group(1)
                        # Event ist der Teil VOR dem Guard
                        event_part = label.split('[')[0].strip()
                        event = event_part if event_part else None
                    else:
                        event = label

                trans = Transition(source=source, target=target, event=event, guard=guard)
                ast.transitions.append(trans)

                # States registrieren, falls sie neu sind (implicit definition)
                for s_name in [source, target]:
                    if s_name not in ["[*]", "[H]"] and s_name not in ast.states:
                         ast.states[s_name] = StateNode(name=s_name, parent=current_parent.name if current_parent else None)
                         if current_parent:
                             current_parent.substates.append(ast.states[s_name])
                continue

        return ast
    
puml_code = """
@startuml
state State_A
state Composite_State

[*] --> State_A
State_A --> Composite_State: Start
Composite_State --> State_A : Pause

state Composite_State {
  state Substate_A
  state Substate_B

  [*] --> Substate_A
  Substate_A --> Substate_B

  State_A --> [H]: Resume
}
@enduml
"""

parser = PlantUMLParser()
ast = parser.parse(puml_code)

# Ausgabe zum Checken
import pprint
print("--- STATES ---")
pprint.pprint(ast.states)
print("\n--- TRANSITIONS ---")
pprint.pprint(ast.transitions)