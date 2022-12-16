from py_trees.behaviour import Behaviour
from py_trees.composites import Sequence, Selector
from py_trees.blackboard import Client
from py_trees.common import Status, Access
from lemminflect import getInflection

class Describable:
    def __init__(self, *args, description : str = None, **kwargs):
        super().__init__(*args, **kwargs)
        print("Description: ", description)
        self.description = description

class LearnableBehaviour(Describable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learned = False

class Approach(Describable, Behaviour):
    def __init__(self, *args, **kwargs):
        super().__init__(description='a person approaches me', *args, **kwargs)
        self.client = Client(name=self.name)
        self.client.register_key(key="approached", access=Access.READ)
    
    def update(self):
        if self.client.approached:
            return Status.SUCCESS
        else:
            return Status.FAILURE

class CustomBehavior(LearnableBehaviour, Sequence):
    def __init__(self, name, **kwargs):
        super().__init__(name, description=f"I {name}", memory=True, **kwargs)
        first_word = name.split(' ')[0]
        gerund = getInflection(first_word, tag='VBG')[0]
        self.gerund = name.replace(first_word, gerund, 1)

class Conditional(LearnableBehaviour, Selector):
    def __init__(self, state, action, **kwargs):
        super().__init__(name="Conditional", **kwargs)
        self.if_statement = Sequence(name="If")
        self.if_statement.add_children([state, action])
        self.add_child(self.if_statement)

    def add_else(self, action):
        self.add_child(action)

class AskBehavior(Describable, Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Ask', description=f'I ask {text}', **kwargs)
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key(key="speech", access=Access.WRITE)

    def update(self):
        self.blackboard.speech = self.text
        return Status.SUCCESS

class SayBehavior(Describable, Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Say', description=f"I say {text}", **kwargs)
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key("speech", Access.WRITE)

    def update(self):
        self.blackboard.speech = self.text
        return Status.SUCCESS

class PersonSays(Describable, Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Person Says', **kwargs)
        if text == '':
            raise ValueError("Text cannot be empty")
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key("person-speech", Access.READ)

    def update(self):
        speech = self.blackboard.person_speech
        if speech == self.text:
            return Status.SUCCESS
        else:
            return Status.FAILURE