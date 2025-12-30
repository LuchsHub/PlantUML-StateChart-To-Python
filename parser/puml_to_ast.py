from treelib import Tree
from treelib.exceptions import NodeIDAbsentError
import random


class Parser():
    def __init__(self, file="example_coffeeMachine/coffeeMachine.puml", warnings=True):
        self.f = open(file)
        self.data = [x.split(" ") for x in self.f.read().split("\n")]
        self.parent = file.split("/")[-1].split(".")[0].lower()
        self.tree = Tree()
        self.warnings = warnings
        self.opened = 1
        self.closed = 0


    def puml_to_ast(self):
        self.tree.create_node(self.parent, self.parent)
        self.tree.create_node(f"transitions_in_{self.parent}", f"transitions_in_{self.parent}", parent=self.parent)
        self.tree.create_node(f"states_in_{self.parent}", f"states_in_{self.parent}", parent=self.parent)

        self.find_state(self.data, 0, self.parent)

        return self.tree


    def find_state(self, data, i, parent):

        for line in range(len(data)):
            if len(data[line]) >= i+2:

                # state
                if data[line][i] == "state":
                    self.create_state(line, i, parent, True, data=data)
                    
                # transition
                if data[line][i+1] == "-->" or data[line][i+1] == "->" :
                    self.create_transition(data[line], i, "_".join(parent.split("_")[:1]))

                # entry
                if data[line][i+1] == "Entry:":
                    self.create_entry(data[line], i, parent.split("_")[-1])

                # exit
                if data[line][i+1] == "Exit:":
                    self.create_exit(data[line], i, parent.split("_")[-1])


    def create_transition(self, line, i, parent):
        #first get all names
        source_state = line[i].split(":")[0].lower()
        goal_state = line[i+2].split(":")[0].lower()
        t_id = random.random()

        # dumb way of creating the transition root
        try:
            if len(line) >= i+5:
                self.tree.create_node(line[i+4], t_id, f"transitions_in_{parent}")
            else:
                self.tree.create_node("+", t_id, f"transitions_in_{parent}")
        except NodeIDAbsentError as msg:
            if self.warnings:
                print(msg)
            if len(line) >= i+5:
                self.tree.create_node(line[i+4], t_id, f"transitions_in_{parent}")
            else:
                self.tree.create_node("+", t_id, f"transitions")

        # set source state
        s_id = random.random()
        self.tree.create_node("source_state", s_id, t_id)
        self.tree.create_node(source_state, random.random(), s_id)
        # save source state to states if not there already
        if self.tree.get_node(f"{source_state}_in_{parent}") is None and source_state != "[*]":
            self.create_state(line, i, parent, False, new_node=source_state)
            #self.tree.create_node(source_state, f"{source_state}_in_{parent}", f"states_in_{parent}")

        # set destination state
        history_check = goal_state.split("[")
        if len(history_check)==2:
            g_id = random.random()
            self.tree.create_node("goal_state", g_id, t_id)
            self.tree.create_node(f"history_state_{history_check[0]}", random.random(), g_id)

            if self.tree.get_node(f"h_{history_check[0]}") is None:
                self.tree.create_node(f"history", f"h_{history_check[0]}", parent=f"{history_check[0]}_in_{parent}")
        
        else:
            g_id = random.random()
            self.tree.create_node("goal_state", g_id, t_id)
            self.tree.create_node(goal_state, random.random(), g_id)
            # save destination state to states if not there already
            if self.tree.get_node(f"{goal_state}_in_{parent}") is None and source_state != "[*]":
                self.create_state(line, i, parent, False, new_node=goal_state)
                #self.tree.create_node(goal_state, f"{goal_state}_in_{parent}", f"states_in_{parent}")

        # set guard
        if len(line) > i+6:
            gu_id = random.random()
            self.tree.create_node("guard", gu_id, t_id)
            self.tree.create_node("".join(line[7:])[1:-1], random.random(), gu_id)



    def create_state(self, line, i, parent, braces, data=None, new_node=None):
        parent = parent.split("_")[0]
        if new_node == None:
            new_node = data[line][i+1].lower()
        new_node_id = f"{new_node}_in_{parent}"
        
        if self.tree.get_node(new_node_id) is None and new_node != "[*]":
            self.tree.create_node(new_node_id, new_node_id, parent=f"states_in_{parent}")   # create state node

            self.tree.create_node(f"transitions_in_{new_node}", f"transitions_in_{new_node}", parent=new_node_id)  # create Transitions leaf
            self.tree.create_node(f"states_in_{new_node}", f"states_in_{new_node}", parent=new_node_id)  # create States leaf

        # for declared history states / therefor probably irrelevant
        history_check = new_node.split("[")
        if len(history_check)==2:
            self.tree.create_node(f"history_state_{new_node}", f"h_{new_node}", parent=f"states_in_{new_node}")

        if braces:
            self.explore_inner(line, data, i, new_node_id)


    def create_exit(self, line, i, parent):
        state = line[i].split(":")[0].lower()
        exit_name = f"exit_{state}"
        exit_clear = " ".join(line[i+2:])
        exit_underline = "_".join(line[i+2:]).lower()

        self.tree.create_node("exit", exit_name, f"{state}_in_{parent}")
        self.tree.create_node(exit_clear, f"{exit_name}_{exit_underline}", exit_name)


    def create_entry(self, line, i, parent):
        state = line[i].split(":")[0].lower()
        entry_name = f"entry_{state}"
        entry_clear = " ".join(line[i+2:])
        entry_underline = "_".join(line[i+2:]).lower()

        self.tree.create_node("entry", entry_name, f"{state}_in_{parent}")
        self.tree.create_node(entry_clear, f"{entry_name}_{entry_underline}", entry_name)


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
    parser = Parser(warnings=False, file="example_coffeeMachine/deepCoffeeMachine.puml")
    parser.puml_to_ast()
    parser.tree.show()