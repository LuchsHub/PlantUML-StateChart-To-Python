import os
import time
from parser import Parser
from generator import Generator

output_dir = "../examples/outputs/own"
path_to_input_puml = "../examples/inputs/coffeeMachine.puml"

os.makedirs(output_dir, exist_ok=True) # create output directory if it doesn't exist

start_time = time.time()

# Parsing
parser = Parser(file=path_to_input_puml, warnings=False)
tree = parser.puml_to_ast()
root = parser.parent

# Generating
gen = Generator(tree, root)
code = gen.generate()

end_time = time.time()
elapsed_time = end_time - start_time

# Writing to file
with open(f"{output_dir}/{root}.py", "w", encoding="utf-8") as f:
    f.write(code)

# Gesamtzeit ausgeben
print(f"Gesamtzeit für Parsing und Generierung: {elapsed_time:.4f} Sekunden")
