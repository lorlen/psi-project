import asyncio

from .cli import cli_main

def main():
    asyncio.run(cli_main())

main()