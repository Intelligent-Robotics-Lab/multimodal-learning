from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn import svm
import numpy as np
from threading import Event
import py_trees
from furhat_remote_api import FurhatRemoteAPI
import readline
from tasklearner import TaskLearner

model = SentenceTransformer('all-MiniLM-L6-v2')

yes_answers = ['yes', 'yeah', 'sure', 'ok', 'okay', 'yes I am ready', 'sounds good', 'I am', "yes I am", "I'm ready"]
no_answers = ['no', 'not yet', 'give me a minute', 'I am not ready yet', "I'm not sure", "hang on", 'I would like a moment']
done_answers = ['all done', 'all finished', 'then you are done', 'you are done', "that's all", "that's it", "there is no next step", "none"]

yes_labels = [1] * len(yes_answers)
no_labels = [0] * len(no_answers)
yes_embeddings = model.encode(yes_answers)
no_embeddings = model.encode(no_answers)
X = np.concatenate((yes_embeddings, no_embeddings))
Y = np.concatenate((yes_labels, no_labels))

clf = svm.SVC()
clf.fit(X, Y)

class DialogAgent:
    def __init__(self):
        self.speech = None
        self.furhat = FurhatRemoteAPI('141.210.144.104')
        self.furhat.attend(user='CLOSEST')
        self.task_tree = TaskLearner()

    def say(self, phrase: str):
        self.furhat.say(text=phrase)

    def listen(self):
        resp = self.furhat.listen()
        if resp.success:
            return resp.message
        else:
            raise ValueError('Failed to listen')
    # def recv_speech(self, phrase: str):
    #     self.speech = phrase
    #     if self.event:
    #         self.event.set()

    def await_yes(self, prompt="Ok, let me know when you're ready"):
        affirmative = False
        while not affirmative:
            # self.event = Event()
            # self.event.is_set()
            # self.event.wait()
            speech = self.listen()
            if speech != '':
                affirmative = self.check_affirmative(speech)
                if not affirmative:
                    self.say(prompt)


    def check_affirmative(self, phrase: str):
        embedding = model.encode(phrase)
        score = clf.predict([embedding])
        return score[0] == 1
        # print(f'Yes similarity: {yes_similarity}, No similarity: {no_similarity}')

    def introduce(self):
        introduction =  """
Hello, my name is Furhat. I am a social robot that can learn to interact with people.
You can teach me new tasks by describing them to me. I will ask some questions about how to behave in different situations.
I will try to understand what you say and do my best to follow your instructions.
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
        for prompt in gen:
            self.say(prompt)
            response = self.listen()
            gen.send(response)

class VirtualAgent(DialogAgent):
    def __init__(self):
        self.task_tree = TaskLearner()

    def say(self, phrase: str):
        print("Robot says:", phrase)

    def listen(self):
        return input("Human says: ")

        
if __name__ == '__main__':
    agent = VirtualAgent()
    agent.run()
    # agent.check_affirmative('yes')
    # agent.check_affirmative('no')
    # agent.check_affirmative('not yet')
    # agent.check_affirmative('I don\'t know')
    # agent.check_affirmative('No I would like a moment')