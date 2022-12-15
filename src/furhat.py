import asyncio
import websockets.client as client
import json
from enum import Enum
from contextlib import asynccontextmanager
from typing import Dict, List, AsyncIterator

class SpeechType(Enum):
    FINAL = 0
    INTERIM = 1
    SILENCE = 2
    MAXSPEECH = 3
    INTERRUPTED = 4
    FAILED = 5
    ABORTED = 6

class UserSpeech():
    def __init__(self, event: Dict):
        self.text = event.get("text")
        self.confidence = event.get("conf")
        self.type = SpeechType(event.get("type"))
        self.length = event.get("length")
        self.time = event.get("time")
        self.userId = event.get("userId")
        self.audioLength = event.get("audiolength")

    def __str__(self):
        return str(self.__dict__)

# class RobotSpeech():
#     def __init__(self, text: str, asynchronous: bool = False, ifSilent: bool = False, abort: bool = False, interruptable: bool = False):
#         self.text = text
#         self.asynchronous = asynchronous
#         self.ifSilent = ifSilent
#         self.abort = abort
#         self.interruptable = interruptable

class Furhat():
    def __init__(self, host, port=80):
        self.host = host
        self.port = port
        self.websocket = None
        self.subscriptions: Dict[str, List[asyncio.Queue]] = {}

    @asynccontextmanager
    async def connect(self):
        self.websocket = await client.connect("ws://{}:{}/api".format(self.host, self.port))
        task = asyncio.create_task(self.recv())
        yield self
        task.cancel()
        await self.websocket.close()

    async def send(self, event):
        result = await self.websocket.send(json.dumps(event))

    async def recv(self):
        while True:
            response = await self.websocket.recv()
            event = json.loads(response)
            name = event.get("event_name")
            if name in self.subscriptions:
                for queue in self.subscriptions[name]:
                    await queue.put(event)

    async def subscribe(self, name) -> AsyncIterator[Dict]:
        if name not in self.subscriptions:
            event = { "event_name": 'furhatos.event.actions.ActionRealTimeAPISubscribe', "name": name }
            await self.send(event)
            self.subscriptions[name] = []
        queue = asyncio.Queue()
        self.subscriptions[name].append(queue)
        try:
            while True:
                response = yield await queue.get()
                if response is not None:
                    self.subscriptions[name].remove(queue)
                    break
        finally:
            self.subscriptions[name].remove(queue)

    async def speech(self) -> AsyncIterator[Dict]:
        gen = self.subscribe("furhatos.event.senses.SenseSpeech")
        try:
            async for event in gen:
                s = UserSpeech(event)
                if s.type == SpeechType.FINAL or s.type == SpeechType.MAXSPEECH:
                    yield
        finally:
            gen.asend("stop")

    async def dyadicSpeech(self) -> AsyncIterator[Dict]:
        gen = self.subscribe("furhatos.event.senses.SenseSpeech")
        try:
            prev = None
            num_words_prev = 0
            async for event in gen:
                s = UserSpeech(event)
                s.text = ' '.join(s.text.split(' ')[num_words_prev:])
                if s.type == SpeechType.FINAL:
                    yield s
                    prev = None
                    num_words_prev = 0
                elif prev is not None and prev.userId != s.userId:
                    yield prev
                    num_words_prev = len(prev.text.split(' '))
                    prev = s
        finally:
            gen.asend("stop")

    async def say(self, text: str, asynchronous: bool = False, ifSilent: bool = False, abort: bool = False, interruptable: bool = False):
        subscription = self.subscribe("furhatos.event.monitors.MonitorSpeechEnd")
        event = { "event_name": 'furhatos.event.actions.ActionSpeech', "text": text, "asynchronous": asynchronous, "ifSilent": ifSilent, "abort": abort, "interruptable": interruptable }
        await self.send(event)
        async for event in subscription:
            print("Received")
            break
        subscription.asend("stop")

    async def listen(self, endSilTimeout: int = 1000):
        event = { "event_name": 'furhatos.event.actions.ActionListen', "endSilTimeout": endSilTimeout }
        await self.send(event)
        async for event in self.speech():
            return event.text

    async def unsubscribe(self, name):
        event = { "event_name": 'furhatos.event.actions.ActionRealTimeAPIUnsubscribe', "name": name }
        await self.send(event)

if __name__ == "__main__":
    async def main():
        async with Furhat("141.210.193.186", 80).connect() as furhat:
            async def print_direction():
                async for event in furhat.subscribe("furhatos.event.senses.SenseSpeechDirection"):
                    print(event)
            task = asyncio.create_task(print_direction())
            async for event in furhat.dyadicSpeech():
                print(event)

    asyncio.run(main())