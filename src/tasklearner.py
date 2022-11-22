from py_trees.trees import BehaviourTree
from py_trees.composites import Sequence
from py_trees.behaviour import Behaviour
from py_trees.display import ascii_tree
from behaviours import Conditional, Approach, AskBehavior, SayBehavior, PersonSays, CustomBehavior, LearnableBehaviour
from tree_parser import TreeParser


class TaskLearner:
    def __init__(self, root : Behaviour = None):
        if root is None:
            self.root = CustomBehavior(name="Root")
        else:
            self.root = root
        self.tree = BehaviourTree(root=self.root)
        self.root.add_child(Approach())
        self.parser = TreeParser()

    def find_unlearned_behaviour(self, parent : Behaviour = None):
        if parent is None:
            parent = self.root
        # print(parent.name)
        for child in parent.children:
            if isinstance(child, LearnableBehaviour) and not child.learned:
                return self.find_unlearned_behaviour(child)
        # No children are unlearned, so return the parent
        return parent

    def test_gen(self):
        while True:
            response = yield f'How do I {self.root.name}?'
            print(f"Response: {response}")

    def generate_prompts(self):
        while True:
            print(ascii_tree(self.tree.root))
            if self.root.learned:
                # Done learning, stop generating prompts
                raise StopIteration()
            unlearned = self.find_unlearned_behaviour()
            print(f"Unlearned: {unlearned.name}")
            if isinstance(unlearned, CustomBehavior):
                if unlearned == self.root:
                    response = yield f'What should I do after {self.root.children[-1].description}?'
                    print(f"Response: {response}")
                    self.parser.append_tree(response, self.tree, unlearned)
                else:
                    if len(unlearned.children) == 0:
                        # Newly created behavior
                        response = yield f'How do I {unlearned.name}?'
                        self.parser.append_tree(response, self.tree, unlearned)
                    else:
                        # Existing behavior
                        response = yield f'What is the next step of {unlearned.gerund}?'
                        print(f"Response: {response}")
                        self.parser.append_tree(response, self.tree, unlearned)
            # Empty return to send
            yield None

