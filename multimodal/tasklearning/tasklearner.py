from py_trees.trees import BehaviourTree
from py_trees.composites import Sequence
from py_trees.behaviour import Behaviour
from py_trees.display import ascii_tree
from multimodal.tasklearning.behaviours import Conditional, Approach, AskBehavior, SayBehavior, PersonSays, CustomBehavior, LearnableBehaviour
from multimodal.tasklearning.tree_parser import TreeParser
from multimodal.nlp.sentence_classifier import SentenceType

class Prompt:
    def __init__(self, text: str, needs_response: bool):
        self.text = text
        self.needs_response = needs_response

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
                    response = yield Prompt(f'What should I do after {self.root.children[-1].description}?', True)
                    # print(f"Response: {response}")
                    if isinstance(response, str):
                        self.parser.append_tree(response, self.tree, unlearned)
                    elif isinstance(response, SentenceType):
                        if response == SentenceType.DONE:
                            self.root.learned = True
                            yield Prompt("Okay, I've learned everything I need to know", False)
                            raise StopIteration()
                else:
                    if len(unlearned.children) == 0:
                        # Newly created behavior
                        response = yield Prompt(f'How do I {unlearned.name}?', True)
                        self.parser.append_tree(response, self.tree, unlearned)
                    else:
                        # Existing behavior
                        response = yield Prompt(f'What is the next step of {unlearned.gerund}?', True)
                        # print(f"Response: {response}")
                        if isinstance(response, str):
                            self.parser.append_tree(response, self.tree, unlearned)
                        elif isinstance(response, SentenceType):
                            if response == SentenceType.DONE:
                                unlearned.learned = True
                                yield Prompt(f"Okay, I've learned how to {unlearned.name}", False)


