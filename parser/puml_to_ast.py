from treelib import Tree
from treelib.exceptions import NodeIDAbsentError
import random


class Parser():
    def __init__(self, file="example_coffeeMachine/coffee_machine.puml", warnings=True):
        self.f = open(file)
        self.data = [x.split(" ") for x in self.f.read().split("\n")]
        self.parent = file.split("/")[-1].split(".")[0]
        self.parent_root = self.parent.lower()
        self.tree = Tree()
        self.warnings = warnings
        self.opened = 1
        self.closed = 0

    def puml_to_ast(self):
        self.tree.create_node(self.parent, self.parent_root)
        self.tree.create_node("Transitions", f"transitions", parent=self.parent_root)

        self.find_state(self.data, 0, self.parent_root)

    def find_state(self, data, i, parent):

        for line in range(len(data)):
            if len(data[line]) >= i+2:

                if data[line][i] == "state":
                    new_node = data[line][i+1].lower()
                    
                    self.tree.create_node(new_node, new_node, parent=parent)
                    self.tree.create_node(f"Transitions_in_{new_node}", f"transitions_in_{new_node}", parent=new_node)
                    self.explore_inner(line, data, i, new_node)
                    
                #transition
                if data[line][i+1] == "-->" or data[line][i+1] == "->" :
                    source_state = data[line][i].split(":")[0].lower()
                    goal_state = data[line][i+2].split(":")[0].lower()
                    t_id = random.random()

                    try:
                        self.tree.create_node("+", t_id, f"transitions_in_{parent}")
                    except NodeIDAbsentError as msg:
                        if self.warnings:
                            print(msg)
                        self.tree.create_node("+", t_id, f"transitions")

                    s_id = random.random()
                    self.tree.create_node("Source_state", s_id, t_id)
                    self.tree.create_node(source_state, random.random(), s_id)

                    g_id = random.random()
                    self.tree.create_node("Goal_state", g_id, t_id)
                    self.tree.create_node(goal_state, random.random(), g_id)

                #entry
                if data[line][i+1] == "Entry:":
                    state = data[line][i].split(":")[0].lower()
                    entry_name = f"entry_{state}"
                    entry_clear = " ".join(data[line][i+2:])
                    entry_underline = "_".join(data[line][i+2:]).lower()

                    self.tree.create_node("Entry", entry_name, state)
                    self.tree.create_node(entry_clear, f"{entry_name}_{entry_underline}", entry_name)

                #exit
                if data[line][i+1] == "Exit:":
                    state = data[line][i].split(":")[0].lower()
                    exit_name = f"exit_{state}"
                    exit_clear = " ".join(data[line][i+2:])
                    exit_underline = "_".join(data[line][i+2:]).lower()

                    self.tree.create_node("Exit", exit_name, state)
                    self.tree.create_node(exit_clear, f"{exit_name}_{exit_underline}", exit_name)

    def explore_inner(self, line, data, i, parent):
        lline = line
        if "{" in data[lline]:
            while self.opened!=self.closed:
                lline +=1
                # iterate over following lines
                if "}" in data[lline]: self.closed += 1
                if "{" in data[lline]: self.opened += 1
            
            self.opened, self.closed = (1, 0)

            self.find_state(data[line:lline], i+2, parent.lower())


                
if __name__=="__main__":
    parser = Parser(warnings=False)
    parser.puml_to_ast()
    parser.tree.show()