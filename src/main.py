from parser import Parser
from generator import Generator

parser = Parser(file="../examples/inputs/coffeeMachine.puml", warnings=False)
tree = parser.puml_to_ast()
root = parser.parent

gen = Generator(tree, root)
code = gen.generate()

with open(f"../outputs/{root}.py", "w", encoding="utf-8") as f:
    f.write(code)
