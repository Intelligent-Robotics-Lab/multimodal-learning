from multimodal.furhat import Furhat
from lfd import LfD
import asyncio
import argparse

async def run(args):
    furhat = Furhat(host=args.host, port=args.port)
    async with furhat.connect():
        cmds = furhat.subscribe('furhatos.app.furhatdriver.SetMode')
        cmd = await cmds.__anext__()
        print(cmd)
        while True:
            if cmd['mode'] == 'LfD':
                lfd = LfD(cmd['participantId'])
                lfd_task = asyncio.create_task(lfd.train(furhat.dyadicSpeech()))
                cmd = await cmds.__anext__()
                lfd_task.cancel()
                lfd.vectorize()
                lfd.save()
            elif cmd['mode'] == 'ITL':
                pass

    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=80)
    parser.add_argument('--sim', type=bool, default=False)
    args = parser.parse_args()
    asyncio.run(run(args))