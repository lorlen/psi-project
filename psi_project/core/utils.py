import asyncio
import sys


# https://stackoverflow.com/a/65326191
async def ainput(string: str) -> str:
    await asyncio.get_event_loop().run_in_executor(
            None, lambda: sys.stdout.write(string))
    return await asyncio.get_event_loop().run_in_executor(
            None, sys.stdin.readline)
