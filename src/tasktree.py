from py_trees.trees import BehaviourTree
from py_trees.composites import Sequence
from py_trees.behaviour import Behaviour
from .behaviours import Conditional, Approach, AskBehavior, SayBehavior, PersonSays, CustomBehavior, LearnableBehaviour
from .tree_parser import TreeParser


class TaskTree:
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
    
        for child in parent.children:
            if isinstance(child, LearnableBehaviour) and not child.learned:
                return self.find_unlearned_behaviour(child)
        # No children are unlearned, so return the parent
        return parent

    def generate_prompts(self):
        while True:
            if self.root.learned:
                # Done learning, stop generating prompts
                raise StopIteration()
            unlearned = self.find_unlearned_behaviour()
            if isinstance(unlearned, CustomBehavior):
                if len(unlearned.children) == 0:
                    # Newly created behavior
                    yield f'How do I {unlearned.name}?'
                else:
                    # Existing behavior
                    if unlearned == self.root:
                        yield f'What do I do ?'

