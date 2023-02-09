from py_trees.trees import BehaviourTree
from py_trees.composites import Sequence
from py_trees.behaviour import Behaviour
from py_trees.display import ascii_tree
from multimodal.tasklearning.behaviours import Conditional, LearnableSequence, Approach, NullBehaviour, PersonSays, CustomBehavior, LearnableBehaviour
from multimodal.tasklearning.tree_parser import TreeParser, ParseError
from multimodal.nlp.sentence_classifier import SentenceType

class Prompt:
    def __init__(self, text: str, needs_response: bool):
        self.text = text
        self.needs_response = needs_response

    def __str__(self) -> str:
        return f"Prompt: {self.text} ({self.needs_response})"

    def __repr__(self) -> str:
        return self.__str__()

class Response:
    def __init__(self, text: str, sentence_type: SentenceType) -> None:
        self.text = text
        self.sentence_type = sentence_type

    def __str__(self) -> str:
        return f"Response: {self.text} ({self.sentence_type})"
    
    def __repr__(self) -> str:
        return self.__str__()

class TaskLearner:
    def __init__(self, root : Behaviour = None):
        if root is None:
            self.root = CustomBehavior(name="Root")
        else:
            self.root = root
        self.tree = BehaviourTree(root=self.root)
        self.root.add_child(Approach())
        self.parser = TreeParser()

    def reset(self):
        self.root = CustomBehavior(name="Root")
        self.tree = BehaviourTree(root=self.root)
        self.root.add_child(Approach())
    
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
                return
            unlearned = self.find_unlearned_behaviour()
            print(f"Unlearned: {unlearned.name}")
            if isinstance(unlearned, LearnableSequence):
                unlearned = unlearned.parent
            print(f"Unlearned: {unlearned.name}")
            try:
                if isinstance(unlearned, CustomBehavior):
                    if unlearned == self.root:
                        prev = self.root.children[-1]
                        if isinstance(prev, Conditional):
                            if len(prev.else_statement.children) >= 1:
                                # yield Prompt(f'Great, now I know what to do if {prev.if_statement.children[0].description} or {prev.else_statement.description}', False)
                                response = yield Prompt(f"After I've finished responding when {prev.if_statement.children[0].description} or {prev.else_statement.description}, what should I do next?", True)
                            else:
                                # yield Prompt(f'Great, now I know what to do if {prev.if_statement.children[0].description}', False)
                                response = yield Prompt(f"After I've finished responding when {prev.if_statement.children[0].description}, what should I do next?", True)
                        else:
                            response: Response = yield Prompt(f'What should I do after {prev.description}?', True)
                        
                        if response.sentence_type == SentenceType.INSTRUCTION:
                            self.parser.append_tree(response.text, self.tree, unlearned)
                        elif response.sentence_type == SentenceType.DONE:
                            self.root.learned = True
                        elif response.sentence_type == SentenceType.MISRECOGNIZED:
                            self.root.remove_child(self.root.children[-1])
                            yield Prompt("I'm sorry I misheard you, let's try again", False)
                        else:
                            raise Exception(f"Unhandled sentence type: {response.sentence_type}")
                    else:
                        if len(unlearned.children) == 0:
                            # Newly created behavior
                            response = yield Prompt(f'How do I {unlearned.name}?', True)
                            if response.sentence_type == SentenceType.INSTRUCTION:
                                self.parser.append_tree(response.text, self.tree, unlearned)
                            elif response.sentence_type == SentenceType.MISRECOGNIZED:
                                unlearned.parent.remove_child(unlearned)
                                yield Prompt("I'm sorry I misheard you, let's go back and try again", False)
                        else:
                            # Existing behavior
                            response = yield Prompt(f'What is the next step of {unlearned.gerund}?', True)
                            if response.sentence_type == SentenceType.INSTRUCTION:
                                self.parser.append_tree(response.text, self.tree, unlearned)
                            elif response.sentence_type == SentenceType.DONE:
                                unlearned.learned = True
                                yield Prompt(f"Okay, I've learned how to {unlearned.name}", False)

                elif isinstance(unlearned, Conditional):
                    if not unlearned.if_statement.learned:
                        response = yield Prompt(f'So when {unlearned.if_statement.children[0].description}, I will {" and ".join([c.description[2:] for c in unlearned.if_statement.children[1:]])}', False)
                        response = yield Prompt(f'Is there anything else I should do when {unlearned.if_statement.children[0].description}?', True)
                        if response.sentence_type == SentenceType.INSTRUCTION:
                            self.parser.append_tree(response.text, self.tree, unlearned.if_statement)
                        elif response.sentence_type == SentenceType.DONE:
                            unlearned.if_statement.learned = True
                            yield Prompt(f"Okay, I've learned how to respond when {unlearned.if_statement.children[0].description}", False)
                            text = unlearned.if_statement.children[0].text
                            if text == "yes":
                                unlearned.else_statement.description = "no"
                                # unlearned.else_statement.add_child(PersonSays("no"))
                                response = yield Prompt(f'What should I do if the person says no?', True)
                            elif text == "no":
                                unlearned.else_statement.description = "yes"
                                # unlearned.else_statement.add_child(PersonSays("yes"))
                                response = yield Prompt(f'What should I do if the person says yes?', True)
                            else:
                                unlearned.else_statement.learned = True
                                continue
                            if response.sentence_type == SentenceType.INSTRUCTION:
                                action = self.parser.append_tree(response.text)
                                unlearned.else_statement.add_child(action)
                            elif response.sentence_type == SentenceType.DONE:
                                unlearned.else_statement.learned = True
                        elif response.sentence_type == SentenceType.MISRECOGNIZED:
                            if len(unlearned.if_statement.children) > 2:
                                unlearned.if_statement.remove_child(unlearned.if_statement.children[-1])
                            else:
                                unlearned.parent.remove_child(unlearned)
                            yield Prompt("I'm sorry I misheard you, let's try again", False)
                        else:
                            print(f"Unhandled response: {response}")
                            yield Prompt("Oh, I appear to be confused, let me think a minute", False)
                    else:
                        response = yield Prompt(f'So when the person says {unlearned.else_statement.description}, I will {" and ".join([c.description[2:] for c in unlearned.else_statement.children])}', False)
                        response = yield Prompt(f'Is there anything else I should do when the person says {unlearned.else_statement.description}?', True)
                        # response = yield Prompt(f'Ok, should I do anything else when the person says {unlearned.else_statement.description}?', True)
                        if response.sentence_type == SentenceType.INSTRUCTION:
                            self.parser.append_tree(response.text, self.tree, unlearned.else_statement)
                        elif response.sentence_type == SentenceType.DONE:
                            unlearned.else_statement.learned = True
                            yield Prompt(f"Okay, I've learned how to respond when the person says {unlearned.else_statement.description}", False)
                        elif response.sentence_type == SentenceType.MISRECOGNIZED:
                            unlearned.else_statement.remove_child(unlearned.else_statement.children[-1])
                            yield Prompt("I'm sorry I misheard you, let's try again", False)
                        else:
                            print(f"Unhandled response 2: {response}")
                            yield Prompt("Oh, I appear to be confused, let me think a minute", False)
                        
                else:
                    raise Exception(f"Unknown behaviour type: {type(unlearned)}")
            except ParseError as e:
                yield Prompt("I'm sorry, I don't quite understand what you said, let's try again", False)
                            


