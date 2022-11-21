from py_trees.behaviour import Behaviour
from py_trees.composites import Sequence, Selector
from py_trees.blackboard import Client
from py_trees.common import Status, Access

class LearnableBehaviour:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learned = False

class Approach(Behaviour):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = Client(name=self.name)
        self.client.register_key(key="approached", access=Access.READ)
        self.description = 'a person approaches me'
    
    def update(self):
        if self.client.approached:
            return Status.SUCCESS
        else:
            return Status.FAILURE

class CustomBehavior(LearnableBehaviour, Sequence):
    def __init__(self, name, **kwargs):
        super().__init__(name, memory=True, **kwargs)

class Conditional(LearnableBehaviour, Selector):
    def __init__(self, state, action, **kwargs):
        super().__init__(name="Conditional", **kwargs)
        self.if_statement = Sequence(name="If")
        self.if_statement.add_children([state, action])
        self.add_child(self.if_statement)

    def add_else(self, action):
        self.add_child(action)

class AskBehavior(Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Ask', **kwargs)
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key(key="speech", access=Access.WRITE)

    def update(self):
        self.blackboard.speech = self.text
        return Status.SUCCESS

class SayBehavior(Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Say', **kwargs)
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key("speech", Access.WRITE)

    def update(self):
        self.blackboard.speech = self.text
        return Status.SUCCESS

class PersonSays(Behaviour):
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