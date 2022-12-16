import asyncio
from furhat import Furhat
from multimodal.tasklearning.tasklearner import TaskLearner, Prompt
from multimodal.nlp.sentence_classifier import SentenceClassifier, SentenceType

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
                affirmative = self.sentence_classifier.classify_ready(speech) == SentenceType.YES
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
        if prompt.needs_response:
            while True:
                await self.say(prompt.text)
                response = await self.listen()
                sentence_type = self.sentence_classifier.classify_next(response)
                while sentence_type == SentenceType.UNCERTAIN:
                    response = await self.listen()
                    sentence_type = self.sentence_classifier.classify_next(response)
                if sentence_type == SentenceType.DONE:
                    prompt = gen.send(sentence_type)
                else:
                    print(f"Response: {response}")
                    print(f"Type: {sentence_type}")
                    prompt = gen.send(response)

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
    LIVE = True
    if LIVE:
        agent = FurhatAgent('141.210.193.186')
        async with agent.connect():
            await agent.run()
    else:
        agent = VirtualAgent()
        await agent.run()
        
if __name__ == '__main__':
    asyncio.run(main())