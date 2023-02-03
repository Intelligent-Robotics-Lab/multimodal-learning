from py_trees.behaviour import Behaviour
from py_trees.composites import Sequence, Selector
from py_trees.blackboard import Client
from py_trees.common import Status, Access
from py_trees.decorators import FailureIsSuccess, Decorator
from lemminflect import getInflection
from tqdm import tqdm
from functools import partialmethod
tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)
from simcse import SimCSE
from scipy.spatial.distance import cosine
similarity_model = SimCSE("princeton-nlp/sup-simcse-bert-base-uncased")

import asyncio

class FurhatBlackboard:
    def __init__(self) -> None:
        self.done_speaking = asyncio.Event()
        self.done_listening = asyncio.Event()
        self.speech = None
        self.user_speech = None

class Describable:
    def __init__(self, *args, description : str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.description = description

class LearnableBehaviour(Describable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learned = False

class Approach(Describable, Behaviour):
    def __init__(self, *args, **kwargs):
        super().__init__(name="Approach", description='a person approaches me', *args, **kwargs)
        self.client = Client(name=self.name)
        self.client.register_key(key="approached", access=Access.READ)
    
    def update(self):
        if self.client.approached:
            return Status.SUCCESS
        else:
            return Status.RUNNING

class NullBehaviour(Behaviour):
    def __init__(self, *args, **kwargs):
        super().__init__(name='Do Nothing', *args, **kwargs)

    def update(self):
        return Status.SUCCESS

class LearnableSequence(LearnableBehaviour, Sequence):
    def __init__(self, name, **kwargs):
        super().__init__(name, memory=True, **kwargs)

class CustomBehavior(LearnableBehaviour, Sequence):
    def __init__(self, name, **kwargs):
        super().__init__(name, description=f"I {name}", memory=True, **kwargs)
        first_word = name.split(' ')[0]
        gerund = getInflection(first_word, tag='VBG')[0]
        self.gerund = name.replace(first_word, gerund, 1)

class Conditional(LearnableBehaviour, Selector):
    def __init__(self, state, action, **kwargs):
        super().__init__(name="Conditional", memory=True, **kwargs)
        self.if_statement = LearnableSequence(name="If")
        self.if_statement.add_children([state, action])
        self.else_statement = LearnableSequence(name="Else")
        self.add_child(self.if_statement)
        self.add_child(self.else_statement)

class AskBehavior(Describable, Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Ask', description=f'I ask {text}', **kwargs)
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key(key="furhat", access=Access.WRITE)
        self.running = False

    def update(self):
        if not self.running:
            self.blackboard.furhat.done_speaking.clear()
            self.blackboard.furhat.speech = self.text + '?'
            self.running = True
            return Status.RUNNING
        elif self.blackboard.furhat.done_speaking.is_set():
            self.blackboard.furhat.speech = None
            self.running = False
            return Status.SUCCESS

class SkipListen(Decorator):
    def __init__(self, child, **kwargs):
        super().__init__(child, **kwargs)
        self.blackboard = Client()
        self.blackboard.register_key(key="furhat", access=Access.WRITE)
    
    def update(self):
        self.blackboard.furhat.done_listening.set()
        return super().update()

class SayBehavior(Describable, Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Say', description=f"I say {text}", **kwargs)
        self.text = text
        self.blackboard = Client()
        self.blackboard.register_key("furhat", Access.WRITE)
        self.running = False

    def update(self):
        if not self.running:
            self.blackboard.furhat.done_speaking.clear()
            self.blackboard.furhat.speech = self.text
            self.running = True
            return Status.RUNNING
        elif self.blackboard.furhat.done_speaking.is_set():
            self.blackboard.furhat.speech = None
            self.running = False
            return Status.SUCCESS

class PersonSays(Describable, Behaviour):
    def __init__(self, text, **kwargs):
        super().__init__(name='Person Says', description=f"the person says {text}", **kwargs)
        if text == '':
            raise ValueError("Text cannot be empty")
        self.text = text
        self.blackboard = Client()

    def setup(self):
        self.blackboard.register_key("furhat", Access.WRITE)
        self.running = False

    def update(self):
        print(self.blackboard)
        if self.blackboard.furhat.done_listening.is_set():
            self.running = False
            difference = cosine(*similarity_model.encode([self.text, self.blackboard.furhat.user_speech]))
            if difference < 0.2:
                return Status.SUCCESS
            else:
                return Status.FAILURE
        elif not self.running:
            self.blackboard.furhat.done_listening.clear()
            self.running = True
        return Status.RUNNING