import os
from parser import Parser
from generator import Generator

output_dir = "../examples/outputs"
path_to_input_puml = "../examples/inputs/drawer.puml"

os.makedirs(output_dir, exist_ok=True) # create output directory if it doesn't exist

# Parsing
parser = Parser(file=path_to_input_puml, warnings=False)
tree = parser.puml_to_ast()
root = parser.parent

# Generating
gen = Generator(tree, root)
code = gen.generate()

# Writing to file
with open(f"{output_dir}/{root}.py", "w", encoding="utf-8") as f:
    f.write(code)
