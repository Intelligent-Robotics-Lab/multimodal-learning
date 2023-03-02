import asyncio
from social_itl.furhat import Furhat
from social_itl.tasklearning.tasklearner import TaskLearner, Prompt, Response
from social_itl.nlp.sentence_classifier import SentenceClassifier, SentenceType
from social_itl.utils import get_logger, get_data_path
from social_itl.tasklearning.behaviours import AskBehavior, SayBehavior
from py_trees.trees import BehaviourTree
from py_trees.blackboard import Client
from py_trees.common import Status, Access
from pickle import dump, load
from social_itl.tasklearning.behaviours import FurhatBlackboard
import py_trees

class DialogAgent:
    def __init__(self):
        self.task_tree = TaskLearner()
        self.sentence_classifier = SentenceClassifier()
        # self.model_gen = asyncio.get_event_loop().run_in_executor(None, get_model)

    async def say(self, phrase: str):
        pass

    async def listen(self) -> str:
        pass

    async def await_yes(self, prompt="Ok, let me know when you're ready"):
        affirmative = False
        while not affirmative:
            speech = await self.listen()
            print(speech)
            if speech == '':
                await self.say("I'm sorry, I didn't understand that. Please say yes or no.")
                continue
            ready = self.sentence_classifier.classify_ready(speech)
            if ready == SentenceType.UNKNOWN:
                await self.say("I'm sorry, I didn't understand that. Please say yes or no.")
                continue
            affirmative = ready == SentenceType.YES
            if not affirmative:
                await self.say(prompt)

    async def introduce(self):
        introduction =  """
Hello, my name is Alpha. I am a social robot that can learn to interact with people.
You can teach me new tasks by describing them to me. I will ask some questions about how to behave in different situations.
I will try to understand what you say, and do my best to follow your instructions.
If at any point I misunderstand you, let me know so I can correct the mistake.
Are you ready to begin?"""
#         introduction =  """
# Are you ready to begin?"""
        await self.say("Hello, my name is Alpha. I am a social robot that can learn to interact with people.")
        await self.say("You can teach me new tasks by describing them to me. I will ask some questions about how to behave in different situations.")
        await self.say("I will try to understand what you say, and do my best to follow your instructions.")
        await self.say("If at any point I misunderstand you, let me know so I can correct the mistake.")
        await self.say("Are you ready to begin?")
        await self.await_yes()
        await self.say("Okay, let's begin!")

    async def learn(self, participant_id=0):
        logger = get_logger(f"Participant-{participant_id}", "learning_dialog", True)
        model_path = get_data_path(f"itl-models/participant-{participant_id}.pkl")
        # if model_path.exists():
        #     self.task_tree.tree = load(open(model_path, 'rb'))
        #     self.task_tree.root = self.task_tree.tree.root
        # else:
        #     self.task_tree.reset()
        self.task_tree.reset()
        try:
            await self.introduce()
            gen = self.task_tree.generate_prompts()
            prompt = next(gen)
            try:
                while True:
                    if prompt.needs_response:
                        await self.say(prompt.text)
                        user_text = await self.listen()
                        if user_text == '':
                            await self.say("I'm sorry, I didn't hear you.")
                            continue
                        sentence_type = self.sentence_classifier.classify_next(user_text)
                        response = Response(user_text, sentence_type)
                        logger.info(str(response))
                        unknown_count = 0
                        while sentence_type in [SentenceType.UNCERTAIN, SentenceType.UNKNOWN]:
                            if sentence_type == SentenceType.UNKNOWN:
                                if unknown_count > 1:
                                    await self.say("I'm sorry, I still don't understand what you're trying to say. Try using simpler words, or breaking your command into smaller steps.")
                                else:
                                    await self.say("I'm sorry, I didn't understand that. Please try again.")
                                unknown_count += 1
                            else:
                                await self.say("If you aren't sure, that's ok. Continue when you're ready")
                            user_text = await self.listen()
                            sentence_type = self.sentence_classifier.classify_next(user_text)
                            response = Response(user_text, sentence_type)
                            logger.info(str(response))
                        prompt = gen.send(response)
                        logger.info(str(prompt))
                    else:
                        await self.say(prompt.text)
                        prompt = next(gen)
                        logger.info(str(prompt))
            except StopIteration:
                await self.say("Okay, I think I've learned everything I need to know. Thank you for your help!")
        except asyncio.exceptions.CancelledError as e:
            print("Dialog cancelled")

        # try:
        #     print("Waiting for model to load...")
        #     model, tokenizer = await self.model_gen
        #     for behavior in self.task_tree.root.iterate():
        #         if isinstance(behavior, AskBehavior) and (behavior.text.startswith("if") or behavior.text.startswith("whether") or behavior.text.startswith("what")):
        #             print("Rephrasing:", behavior.text)
        #             behavior.text = await asyncio.get_event_loop().run_in_executor(None, rephrase_ask, "Ask " + behavior.text, model, tokenizer)
        #             print("Rephrased:", behavior.text)
        #         # elif isinstance(behavior, SayBehavior):
        #         #     print("Rephrasing:", behavior.text)
        #         #     behavior.text = await asyncio.get_event_loop().run_in_executor(None, rephrase, "Say " + behavior.text, model, tokenizer)
        #         #     print("Rephrased:", behavior.text
        # except Exception as e:
        #     print("Exception while rephrasing:", e)
        #     return
        model_path = get_data_path(f"itl-models/participant-{participant_id}.pkl")
        dump(self.task_tree.tree, open(model_path, 'wb'))

    async def execute(self, participant_id=0, skip_intro=False):
        print("Loading pkl...")
        try:
            path = get_data_path(f"itl-models/participant-{participant_id}.pkl")
            tree: BehaviourTree = load(open(path, 'rb'))
        except FileNotFoundError:
            print("No ITL data for participant", participant_id)
            return
        if not skip_intro:
            await self.say("Great, now that you've taught me to be a concierge, I can try it myself. Here we go!")
        snapshot_visitor = py_trees.visitors.SnapshotVisitor()
        tree.visitors.append(snapshot_visitor)
        client = Client(name="Furhat")
        client.register_key(key="furhat", access=Access.WRITE)
        client.register_key(key="approached", access=Access.WRITE)
        client.approached = True
        client.furhat = FurhatBlackboard()
        print("Setting up")
        while True:
            tree.setup(timeout=15)
            while True:
                print(client.furhat.done_listening.is_set())
                tree.tick()
                print(py_trees.display.unicode_tree(
                    tree.root,
                    visited=snapshot_visitor.visited,
                    previously_visited=snapshot_visitor.visited
                ))
                if tree.root.status == Status.SUCCESS:
                    break
                if tree.root.status == Status.FAILURE:
                    await self.say("I'm sorry, I didn't understand that. Please try again.")
                if tree.root.status == Status.RUNNING:
                    print(client.furhat.speech)
                    print(client.furhat.done_listening.is_set())
                    print(client.furhat.done_speaking.is_set())
                    if client.furhat.speech:
                        client.furhat.done_listening.clear()
                        await self.say(client.furhat.speech)
                        print("Said:", client.furhat.speech)
                        client.furhat.speech = ''
                        client.furhat.done_speaking.set()
                    elif not client.furhat.done_listening.is_set():
                        client.furhat.user_speech = await self.listen()
                        if client.furhat.user_speech == '':
                            await self.say("I'm sorry, I didn't hear you.")
                        else:
                            client.furhat.done_listening.set()
                await asyncio.sleep(0.1)


class FurhatAgent(Furhat, DialogAgent):
    def __init__(self, host='localhost', port=80):
        Furhat.__init__(self, host, port)
        DialogAgent.__init__(self)

class VirtualAgent(DialogAgent):
    async def say(self, phrase: str):
        print("Robot says:", phrase)

    async def listen(self):
        return input("Human says: ")

async def main():
    LIVE = False
    if LIVE:
        agent = FurhatAgent('141.210.193.186')
        async with agent.connect():
            await agent.learn()
    else:
        agent = VirtualAgent()
        await agent.learn()
        
if __name__ == '__main__':
    asyncio.run(main())