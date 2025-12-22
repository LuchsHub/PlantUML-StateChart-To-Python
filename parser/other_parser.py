import treelib
from puml_to_ast import Parser

parser = Parser()
ast = parser.puml_to_ast()

ast.show()

print(ast.children("coffeemachine"))
