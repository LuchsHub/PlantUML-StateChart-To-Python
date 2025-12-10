from treelib import Tree
import click


# @click.command()
# @click.option("--file", prompt="Path to your file", 
#               help="Full or relative path to your file.\nDon't forget starting a venv and installing the requirements")

class Parser():
    def __init__(self, file="example_dishwasher/dishwasher.puml"):
        self.f = open(file)
        self.data = [x.split(" ") for x in self.f.read().split("\n")]
        self.parent = file.split("/")[-1].split(".")[0]
        self.parent_root = self.parent.lower()
        self.tree = Tree()
        self.opened = 1
        self.closed = 0

    def puml_to_ast(self):
        self.tree.create_node(self.parent, self.parent_root)

        self.find_state(self.data, 0, self.parent_root)

        self.tree.show()

    def find_state(self, data, i, parent):
        # print(data)
        self.tree.show()
        print("\n")
        for line in range(len(data)):
            if len(data[line]) >= i+2:
                if data[line][i] == "state":
                    p = data[line][i+1]
                    self.tree.create_node(p, p.lower(), parent=parent)
                    self.explore_inner(line, data, i, p)
                
                if data[line][i+1] == "-->":      #transition
                    pass
                if data[line][i+1] == "Entry:":      #entry
                    state = data[line][i].split(":")[0].lower()
                    entry_name = f"entry_{state}"
                    entry_clear = " ".join(data[line][i+2:])
                    entry_underline = "_".join(data[line][i+2:]).lower()

                    self.tree.create_node("Entry", entry_name, state)
                    self.tree.create_node(entry_clear, f"{entry_name}_{entry_underline}", entry_name)

                if data[line][i+1] == "Exit:":      #exit
                    state = data[line][i].split(":")[0].lower()
                    exit_name = f"exit_{state}"
                    exit_clear = " ".join(data[line][i+2:])
                    exit_underline = "_".join(data[line][i+2:]).lower()

                    self.tree.create_node("Exit", exit_name, state)
                    self.tree.create_node(exit_clear, f"{exit_name}_{exit_underline}", exit_name)

    def explore_inner(self, line, data, i, p):
        lline = line
        if "{" in data[lline]:
            while self.opened!=self.closed:
                lline +=1
                # iterate over following lines
                if "}" in data[lline]: self.closed += 1
                if "{" in data[lline]: self.opened += 1
            #print(lline)
            self.opened, self.closed = (1, 0)

            self.find_state(data[line:lline], i+2, p.lower())

                
if __name__=="__main__":
    parser = Parser()
    parser.puml_to_ast()