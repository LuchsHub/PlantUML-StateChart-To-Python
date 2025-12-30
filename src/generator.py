from treelib.exceptions import NodeIDAbsentError

# TODO: Variablen für Guards


class Generator:
    def __init__(self, tree, root):
        self.tree = tree
        self.root = root
        self.actions = set()
        self.lines = []

    def generate(self):
        self.emit_base_classes()
        self.emit_states(self.root)
        self.emit_state_machine()
        self.emit_actions()
        return "\n".join(self.lines)

    def uses_history(self, state_node):
        for c in self.tree.children(state_node.identifier):
            if c.tag == "history":
                return True

        return False

    def emit_base_classes(self):
        self.lines += [
            "from abc import ABC, abstractmethod",
            "",
            "",
            "class State(ABC):",
            "    @abstractmethod",
            "    def __init__(self, context):",
            "        pass",
            "",
            "    def entry(self, use_hist: bool = False):",
            "        pass",
            "",
            "    def exit(self):",
            "        pass",
            "",
            "    def dispatch(self, event: str):",
            "        pass",
            "",
            "",
            "class SimpleState(State):",
            "    def __init__(self, context):",
            "        self.context = context",
            "",
            "",
            "class CompositeState(State):",
            "    @property",
            "    def state(self) -> State:",
            "        return self._state",
            "",
            "    @abstractmethod",
            "    def entry(self, use_hist: bool = False):",
            "        pass",
            "",
            "    def exit(self):",
            "        self.state.exit()",
            "",
            "    def dispatch(self, event: str):",
            "        self.state.dispatch(event)",
            "",
            "    def transition(self, new_state: State, use_hist: bool = False):",
            "        self.state.exit()",
            "        self._state = new_state",
            "        self.state.entry(use_hist)",
            "",
            "",
            "class CompositeStateWithHistory(CompositeState):",
            "    @property",
            "    def history(self) -> State:",
            "        return self._history",
            "",
            "    def transition(self, new_state: State, use_hist: bool = False):",
            "        self.state.exit()",
            "        self._state = new_state",
            "        self._history = self._state",
            "        self.state.entry(use_hist)",
            "",
            "",
        ]

    def emit_state(self, state_node):
        name = state_node.tag
        try:
            is_composite = bool(self.tree.children(f"states_in_{name}"))
        except NodeIDAbsentError:
            is_composite = False
        
        has_hist = False
        if is_composite:
            has_hist = self.uses_history(state_node)
            super_class = "CompositeStateWithHistory" if has_hist else "CompositeState"
        else:
            super_class = "SimpleState"
        self.lines.append(f"class {name.capitalize()}({super_class}):")

        self.emit_init(state_node, is_composite, has_hist)
        self.emit_entry_exit(state_node, is_composite, has_hist)
        self.emit_dispatch(state_node, is_composite)
        self.lines.append("")

        # funktioniert noch nicht, Unterzustände haben noch kein states_in_x und transitions_in_x
        if is_composite:
            self.emit_states(name)

    def emit_states(self, parent):
        states_root = f"states_in_{parent}"

        for state_node in self.tree.children(states_root):
            self.emit_state(state_node)

    def emit_init(self, state_node, composite, has_hist):
        name = state_node.tag

        if not composite:
            return

        self.lines.append("    def __init__(self, context):")
        self.lines.append("        self.context = context")

        substates = self.tree.children(f"states_in_{name}")
        for sub in substates:
            if sub.tag == "[*]":
                continue

            self.lines.append(f"        self.{sub.tag} = {sub.tag.capitalize()}(self)")

        self.lines.append("        self._state = None")
        if has_hist:
            self.lines.append("        self._history = None")
        self.lines.append("")

    def emit_entry_exit(self, state_node, is_composite, has_hist):
        name = state_node.tag
        entry = exit = None

        for child in self.tree.children(state_node.identifier):
            if child.tag == "entry":
                entry = self.tree.children(child.identifier)[0].tag
                self.actions.add(entry)
            elif child.tag == "exit":
                exit = self.tree.children(child.identifier)[0].tag
                self.actions.add(exit)

        if is_composite:
            self.lines.append("    def entry(self, use_hist: bool = False):")
            if entry:
                self.lines.append(f"        {entry}()")
                self.lines.append("")
            if has_hist:
                self.lines.append(f"        if use_hist:")
                self.lines.append(f"            self._state = self._history")
                self.lines.append("        else:")

            transitions_root = f"transitions_in_{name}"
            for t in self.tree.children(transitions_root):
                source, target = None, None

                for c in self.tree.children(t.identifier):
                    if c.tag == "source_state":
                        source = self.tree.children(c.identifier)[0].tag
                    elif c.tag == "goal_state":
                        target = self.tree.children(c.identifier)[0].tag

                if source == "[*]":
                    if has_hist:
                        self.lines.append(f"            self._state = self.{target}")
                    else:
                        self.lines.append(f"        self._state = self.{target}")
                    break

            self.lines.append("")
            self.lines.append("        self.state.entry()")
            self.lines.append("")
            if exit:
                self.lines.append("    def exit(self):")
                self.lines.append("        self.state.exit()")
                self.lines.append(f"        {exit}()")
                self.lines.append("")
        else:
            if entry:
                self.lines.append("    def entry(self):")
                self.lines.append(f"        {entry}()")
                self.lines.append("")
            if exit:
                self.lines.append("    def exit(self):")
                self.lines.append(f"        {exit}()")
                self.lines.append("")

    def emit_dispatch(self, state_node, is_composite):
        name = state_node.tag

        parent_id = state_node.predecessor(self.tree.identifier)
        parent_node = self.tree.get_node(parent_id)
        grandparent_id = parent_node.predecessor(self.tree.identifier)
        grandparent_node = self.tree.get_node(grandparent_id)
        grandparent_name = grandparent_node.tag

        trans_root = f"transitions_in_{grandparent_name}"

        dispatch_lines = []
        for t in self.tree.children(trans_root):
            source, target, guard = "", "", ""

            for c in self.tree.children(t.identifier):
                if c.tag == "source_state":
                    source = self.tree.children(c.identifier)[0].tag
                elif c.tag == "goal_state":
                    target = self.tree.children(c.identifier)[0].tag
                elif c.tag == "guard":
                    guard = self.tree.children(c.identifier)[0].tag

            if source != name:
                continue

            event_label = t.tag
            condition = f'event == "{event_label}"'
            if guard:
                condition += f" and (self.context.{guard})"

            dispatch_lines.append(f"        if {condition}:")
            if target.startswith("history_state_"):
                dispatch_lines.append(
                    f"            self.context.transition(self.context.{target[14:]}, use_hist=True)"
                )
            else:
                dispatch_lines.append(
                    f"            self.context.transition(self.context.{target})"
                )

        if dispatch_lines:
            self.lines.append("    def dispatch(self, event: str):")
            self.lines += dispatch_lines
            if is_composite:
                self.lines.append("        else:")
                self.lines.append("            self.state.dispatch(event)")
            self.lines.append("")

    def emit_state_machine(self):
        self.lines.append("class StateMachine:")
        self.lines.append("    def __init__(self):")

        states_root = f"states_in_{self.root}"
        for state_node in self.tree.children(states_root):
            if state_node.tag == "[*]":
                continue

            self.lines.append(
                f"        self.{state_node.tag} = {state_node.tag.capitalize()}(self)"
            )

        transitions_root = f"transitions_in_{self.root}"
        for t in self.tree.children(transitions_root):
            source, target = None, None

            for c in self.tree.children(t.identifier):
                if c.tag == "source_state":
                    source = self.tree.children(c.identifier)[0].tag
                elif c.tag == "goal_state":
                    target = self.tree.children(c.identifier)[0].tag

            if source == "[*]":
                self.lines.append(f"        self.state = self.{target}")
                break

        self.lines.append("        self.state.entry()")
        self.lines.append("")
        self.lines.append("    def dispatch(self, event: str):")
        self.lines.append("        self.state.dispatch(event)")
        self.lines.append("")
        self.lines.append(
            "    def transition(self, new_state: State, use_hist: bool = False):"
        )
        self.lines.append("        self.state.exit()")
        self.lines.append("        self.state = new_state")
        self.lines.append("        self.state.entry(use_hist)")
        self.lines.append("")
        self.lines.append("")

    def emit_actions(self):
        for a in self.actions:
            self.lines.append(f"def {a}():")
            self.lines.append(f"    pass")
            self.lines.append("")
            self.lines.append("")

