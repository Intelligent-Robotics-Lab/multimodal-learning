import asyncio
from multimodal.furhat import Furhat
from multimodal.tasklearning.tasklearner import TaskLearner, Prompt, Response
from multimodal.nlp.sentence_classifier import SentenceClassifier, SentenceType
from multimodal.utils import get_logger

class DialogAgent:
    def __init__(self):
        self.task_tree = TaskLearner()
        self.sentence_classifier = SentenceClassifier()

    async def say(self, phrase: str):
        pass

    async def listen(self) -> str:
        pass

    async def await_yes(self, prompt="Ok, let me know when you're ready"):
        affirmative = False
        while not affirmative:
            speech = await self.listen()
            # print(speech)
            if speech != '':
                ready = self.sentence_classifier.classify_ready(speech)
                if ready == SentenceType.UNKNOWN:
                    await self.say("I'm sorry, I didn't understand that. Please say yes or no.")
                    continue
                affirmative = ready == SentenceType.YES
                if not affirmative:
                    await self.say(prompt)

    async def introduce(self):
        introduction =  """
Hello, my name is Furhat. I am a social robot that can learn to interact with people.
You can teach me new tasks by describing them to me. I will ask some questions about how to behave in different situations.
I will try to understand what you say, and do my best to follow your instructions.
Are you ready to begin?"""
        await self.say(introduction)
        await self.await_yes()
        await self.say("Okay, let's begin!")

    async def run(self):
        await self.introduce()
        gen = self.task_tree.generate_prompts()
        prompt = next(gen)
        while True:
            if prompt.needs_response:
                await self.say(prompt.text)
                user_text = await self.listen()
                sentence_type = self.sentence_classifier.classify_next(user_text)
                response = Response(user_text, sentence_type)
                while sentence_type in [SentenceType.UNCERTAIN, SentenceType.UNKNOWN]:
                    if sentence_type == SentenceType.UNKNOWN:
                        await self.say("I'm sorry, I didn't understand that. Please try again.")
                    else:
                        await self.say("If you aren't sure, that's ok. Continue when you're ready")
                    user_text = await self.listen()
                    sentence_type = self.sentence_classifier.classify_next(user_text)
                    response = Response(user_text, sentence_type)
                prompt = gen.send(response)
            else:
                await self.say(prompt.text)
                prompt = next(gen)

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
            await agent.run()
    else:
        agent = VirtualAgent()
        await agent.run()
        
if __name__ == '__main__':
    asyncio.run(main())