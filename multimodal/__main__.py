from multimodal.furhat import Furhat, DisconnectError
from multimodal.tasklearning.agent import FurhatAgent
from .lfd import LfD
import asyncio
import argparse
import websockets

async def run_experiment(furhat, gui_state):
    async def update_gui_state(event):
        while True:
            event = {"event_name": "ServerEvent", "type": "GUIState", **gui_state}
            await furhat.send(event)
            await asyncio.sleep(1)
    gui_state_task = asyncio.create_task(update_gui_state(gui_state))
    try:
        cmds = furhat.subscribe('furhatos.app.furhatdriver.GUIEvent')
        cmd = await cmds.__anext__()
        while True:
            print("Command:", cmd)
            if cmd['type'] == 'SetMode':
                if cmd['mode'] == 'LfD':
                    gui_state['mode'] = 'LfD'
                    lfd = LfD(cmd['participantId'])
                    lfd_task = asyncio.create_task(lfd.train(furhat.dyadicSpeech()))
                    cmd = await cmds.__anext__()
                    print("Cancelling")
                    lfd_task.cancel()
                    print("Cancelled")
                    await asyncio.get_event_loop().run_in_executor(None, lfd.vectorize)
                    lfd.save()
                elif cmd['mode'] == 'ITL':
                    gui_state['mode'] = 'ITL'
                    print('ITL')
                    cmd = await cmds.__anext__()
                else:
                    gui_state['mode'] = ''
                    cmd = await cmds.__anext__()
            elif cmd['type'] == 'SetITLMode':
                if cmd['mode'] == 'Learning':
                    print('Learning')
                    gui_state['ITLMode'] = 'Learning'
                    itl_task = asyncio.create_task(furhat.learn())
                    async def cancel_itl():
                        cmd = await cmds.__anext__()
                        if cmd['type'] != 'StopLearning':
                            print("Unexpected command:", cmd)
                        itl_task.cancel()
                    cancel_task = asyncio.create_task(cancel_itl())
                    await itl_task
                    cancel_task.cancel()
                    print("Cancelled")
                    gui_state['ITLMode'] = 'Idle'
                cmd = await cmds.__anext__()
            else:
                print("Unknown command", cmd)
                cmd = await cmds.__anext__()
    finally:
        gui_state_task.cancel()

async def loop(args):
    furhat = FurhatAgent(host=args.host, port=args.port)
    gui_state = {"mode": "", "participantId": "1", "ITLMode": "Idle"}
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