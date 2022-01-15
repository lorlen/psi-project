import asyncio
from .tcp import Server 
from .repo import FileManager

async def run():
    fp = FileManager()
    s = Server(fp)
    task = s.runServer()

    await task


asyncio.run(run()) 
