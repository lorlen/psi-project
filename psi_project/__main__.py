import asyncio
from .tcp import Server 
from .repo import FileManager
import sys

fp = FileManager()
s = Server(fp)

async def run():
    task = s.runServer()

    await task

def send():
    asyncio.run(s.startDownload('127.0.0.1', 'test'))

if sys.argv[1] == 's':
    asyncio.run(run())
else:
    send()
