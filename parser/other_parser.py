from puml_to_ast import Parser

parser = Parser()
ast = parser.puml_to_ast()

ast.show()

sm_name = ast.get_node(ast.root).tag

for state in ast.children(f"states_in_{sm_name}"):
    state_node = ast.get_node(state.identifier)
    print(f"State: {state_node.tag}")
    if state_node.tag == "[*]":
        continue

    substate_count = 0
    for substate in ast.children(f"states_in_{state_node.tag}"):
        substate_count += 1
    print(substate_count)


