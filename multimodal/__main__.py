from multimodal.furhat import Furhat, DisconnectError
from multimodal.tasklearning.agent import FurhatAgent
from .lfd import LfD
import asyncio
import argparse
import websockets

async def run_experiment(furhat: FurhatAgent, gui_state):
    async def update_gui_state(event):
        while True:
            event = {"event_name": "ServerEvent", "type": "GUIState", **gui_state}
            await furhat.send(event)
            await asyncio.sleep(1)
    gui_state_task = asyncio.create_task(update_gui_state(gui_state))
    event_queue = asyncio.Queue()
    async def event_handler():
        async for event in furhat.subscribe('furhatos.app.furhatdriver.GUIEvent'):
            await event_queue.put(event)
        print("Event handler done")
    event_handler_task = asyncio.create_task(event_handler())
    try:
        cmd = await event_queue.get()
        while True:
            print("Command:", cmd)
            if cmd['type'] == 'SetMode':
                gui_state['participantId'] = cmd['participantId']
                if cmd['mode'] == 'LfD':
                    gui_state['mode'] = 'LfD'
                    print('LfD')
                    cmd = await event_queue.get()
                elif cmd['mode'] == 'ITL':
                    gui_state['mode'] = 'ITL'
                    print('ITL')
                    cmd = await event_queue.get()
                else:
                    gui_state['mode'] = ''
                    cmd = await event_queue.get()
            elif cmd['type'] == 'SetLfDMode':
                if cmd['mode'] == 'Learning':
                    print('Learning')
                    gui_state['LfDMode'] = 'Learning'
                    lfd = LfD(gui_state['participantId'])
                    lfd_task = asyncio.create_task(lfd.train(furhat.dyadicSpeech()))
                    cmd = await event_queue.get()
                    print("Cancelling")
                    lfd_task.cancel()
                    await lfd_task
                    print("Cancelled")
                    lfd.save()
                    print(lfd.pairs)
                    gui_state['LfDMode'] = 'Idle'
                elif cmd['mode'] == 'Testing':
                    print('Testing')
                    gui_state['LfDMode'] = 'Testing'
                    lfd = LfD(gui_state['participantId'])
                    load_task = asyncio.get_event_loop().run_in_executor(None, lfd.load)
                    await load_task
                    action = ''
                    cancel = asyncio.Event()
                    async def cancel_lfd():
                        cmd = await event_queue.get()
                        cancel.set()
                    cancel_task = asyncio.create_task(cancel_lfd())
                    while not cancel.is_set():
                        speech = await furhat.listen(noSpeechTimeout=2000)
                        if cancel.is_set():
                            break
                        action, confidence = lfd.get_action(speech, action)
                        await furhat.say(action)
                    cmd = await event_queue.get()
                    print("Cancelling")
                    cancel_task.cancel()
                    print("Cancelled")
                    gui_state['LfDMode'] = 'Idle'
                elif cmd['mode'] == 'Evaluating':
                    print('Evaluating')
                    gui_state['LfDMode'] = 'Evaluating'
                    try:
                        lfd = LfD(str(int(gui_state['participantId']) - 1))
                        load_task = asyncio.get_event_loop().run_in_executor(None, lfd.load)
                        await load_task
                        action = ''
                        cancel = asyncio.Event()
                        async def cancel_lfd():
                            cmd = await event_queue.get()
                            cancel.set()
                        cancel_task = asyncio.create_task(cancel_lfd())
                        with furhat.log(f'Participant-{gui_state["participantId"]}', 'lfd_eval'):
                            while not cancel.is_set():
                                speech = await furhat.listen(noSpeechTimeout=2000, endSilTimeout=1000)
                                if cancel.is_set():
                                    break
                                action, confidence = lfd.get_action(speech, action)
                                await furhat.say(action)
                        print("Cancelling")
                        cancel_task.cancel()
                    except FileNotFoundError:
                        print("No LfD data for participant", gui_state['participantId'])
                    print("Cancelled")
                    gui_state['LfDMode'] = 'Idle'
                cmd = await event_queue.get()
            elif cmd['type'] == 'SetITLMode':
                if cmd['mode'] == 'Learning':
                    print('Learning')
                    gui_state['ITLMode'] = 'Learning'
                    itl_task = asyncio.create_task(furhat.learn(gui_state['participantId']))
                    async def cancel_itl():
                        cmd = await event_queue.get()
                        if cmd['type'] != 'StopLearning':
                            print("Unexpected command:", cmd)
                    cancel_task = asyncio.create_task(cancel_itl())
                    done, pending = await asyncio.wait([itl_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)
                    for task in pending:
                        task.cancel()
                    await asyncio.wait(pending)
                    gui_state['ITLMode'] = 'Idle'
                elif cmd['mode'] == 'Testing':
                    print('Testing')
                    gui_state['ITLMode'] = 'Testing'
                    itl_task = asyncio.create_task(furhat.execute(gui_state['participantId']))
                    async def cancel_itl():
                        cmd = await event_queue.get()
                        if cmd['type'] != 'StopLearning':
                            print("Unexpected command:", cmd)
                    cancel_task = asyncio.create_task(cancel_itl())
                    done, pending = await asyncio.wait([itl_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)
                    print("Done:", done)
                    for task in pending:
                        task.cancel()
                    await asyncio.wait(pending)
                    print ("Done waiting")
                    gui_state['ITLMode'] = 'Idle'
                elif cmd['mode'] == 'Evaluating':
                    print('Evaluating')
                    gui_state['ITLMode'] = 'Evaluating'
                    with furhat.log(f'Participant-{gui_state["participantId"]}', 'itl_eval'):
                        itl_task = asyncio.create_task(furhat.execute(int(gui_state['participantId']) - 1))
                        async def cancel_itl():
                            cmd = await event_queue.get()
                            if cmd['type'] != 'StopLearning':
                                print("Unexpected command:", cmd)
                        cancel_task = asyncio.create_task(cancel_itl())
                        done, pending = await asyncio.wait([itl_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)
                    print("Done:", done)
                    for task in pending:
                        task.cancel()
                    await asyncio.wait(pending)
                    print ("Done waiting")
                    gui_state['ITLMode'] = 'Idle'
                cmd = await event_queue.get()
            else:
                print("Unknown command", cmd)
                cmd = await event_queue.get()
    # except Exception as e:
    #     print("Error:", repr(e))
    finally:
        gui_state_task.cancel()
        event_handler_task.cancel()

async def loop(args):
    furhat = FurhatAgent(host=args.host, port=args.port)
    gui_state = {"mode": "", "participantId": "1", "ITLMode": "Idle", "LfDMode": "Idle"}
    # async with furhat.connect():
    #     print('Connected to Furhat')
    #     await run_experiment(furhat, gui_state)
    while True:
        try:
            async with furhat.connect():
                print('Connected to Furhat')
                await run_experiment(furhat, gui_state)
        except DisconnectError:
            print('Disconnected from Furhat')
            await asyncio.sleep(5)
        except websockets.exceptions.WebSocketException as e:
            print("Websocket error:", e)
            await asyncio.sleep(5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=80)
    parser.add_argument('--sim', type=bool, default=False)
    args = parser.parse_args()
    asyncio.run(loop(args))

if __name__ == '__main__':
    main()