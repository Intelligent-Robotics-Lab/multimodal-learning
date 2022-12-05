from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn import svm
import numpy as np
from threading import Event
import py_trees
from furhat_remote_api import FurhatRemoteAPI
import readline
from tasklearner import TaskLearner
from sentence_classifier import SentenceClassifier, SentenceType

class DialogAgent:
    def __init__(self):
        self.task_tree = TaskLearner()
        self.sentence_classifier = SentenceClassifier()

    def say(self, phrase: str):
        pass

    def listen(self) -> str:
        pass

    def await_yes(self, prompt="Ok, let me know when you're ready"):
        affirmative = False
        while not affirmative:
            speech = self.listen()
            # print(speech)
            if speech != '':
                affirmative = self.sentence_classifier.classify_ready(speech) == SentenceType.YES
                if not affirmative:
                    self.say(prompt)

    def introduce(self):
        introduction =  """
Hello, my name is Furhat. I am a social robot that can learn to interact with people.
You can teach me new tasks by describing them to me. I will ask some questions about how to behave in different situations.
I will try to understand what you say, and do my best to follow your instructions.
Are you ready to begin?"""
        self.say(introduction)
        self.await_yes()
        self.say("Okay, let's begin!")

    def learn_approach(self):
        self.say("What should I do when a person first approaches me?")
        result = self.listen()

    def run(self):
        self.introduce()
        gen = self.task_tree.generate_prompts()
        prompt = next(gen)
        while True:
            self.say(prompt)
            response = self.listen()
            sentence_type = self.sentence_classifier.classify_next(response)
            while sentence_type == SentenceType.UNCERTAIN:
                response = self.listen()
                sentence_type = self.sentence_classifier.classify_next(response)
            if sentence_type == SentenceType.DONE:
                prompt = gen.send(sentence_type)
            else:
                print(f"Response: {response}")
                print(f"Type: {sentence_type}")
                prompt = gen.send(response)

class FurhatAgent(DialogAgent):
    def __init__(self, ip: str):
        super().__init__()
        self.furhat = FurhatRemoteAPI(ip)
        print(self.furhat.get_users())
        self.furhat.attend(user='CLOSEST')

    def say(self, phrase: str):
        self.furhat.say(text=phrase, blocking=True)
        print(self.furhat.get_users())

    def listen(self):
        msg = ''
        while msg == '':
            resp = self.furhat.listen()
            if resp.success:
                msg = resp.message
            else:
                raise ValueError('Failed to listen')
        return msg

class VirtualAgent(DialogAgent):
    def say(self, phrase: str):
        print("Robot says:", phrase)

    def listen(self):
        return input("Human says: ")

        
if __name__ == '__main__':
    agent = VirtualAgent()
    # agent = FurhatAgent('141.210.193.186')
    agent.run()