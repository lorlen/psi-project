from argparse import ArgumentParser
import asyncio
from functools import partial
from pathlib import Path
from typing import List
from psi_project.tcp import TcpServer
from psi_project.udp import UdpServer, serveUdpServer
from psi_project.repo import FileManager
import logging
from aioconsole import AsynchronousCli, start_interactive_server
from aioconsole.server import parse_server, print_server

from .commands import Commands


def make_cli(commands: Commands, streams=None):
    get_parser = ArgumentParser(
        description="Download a file onto the local filesystem."
    )
    get_parser.add_argument("filename", help="filename to search for in the network")
    get_parser.add_argument(
        "path", type=Path, help="local filesystem path to store the file in"
    )

    put_parser = ArgumentParser(description="Put a file in the daemon's repository.")
    put_parser.add_argument(
        "path", type=Path, help="filesystem path from which to take the file"
    )
    put_parser.add_argument(
        "filename", nargs="?", help="custom name to store the file under"
    )

    ls_parser = ArgumentParser(
        description="List all files in the daemon's local repository."
    )

    exists_parser = ArgumentParser(
        description="Check if the file exists in the network."
    )
    exists_parser.add_argument("filename", help="filename to check existence of")

    rm_parser = ArgumentParser(description="Remove a file from the local repository.")
    rm_parser.add_argument("filename", help="file to remove")
    rm_parser.add_argument(
        "-r",
        "--revoke",
        action="store_true",
        help="also revoke this file on remote nodes",
    )

    fetch_parser = ArgumentParser(description="Fetch a file to local repository.")
    fetch_parser.add_argument("filename", help="file to fetch")

    cmds = {
        "get": (commands.get, get_parser),
        "put": (commands.put, put_parser),
        "ls": (commands.ls, ls_parser),
        "exists": (commands.exists, exists_parser),
        "rm": (commands.rm, rm_parser),
        "fetch": (commands.fetch, fetch_parser),
    }

    logging.debug("Starting cli")
    return AsynchronousCli(cmds, streams, prog="PSI Project")


def parse_args(args: List[str] = None):
    parser = ArgumentParser(description="A P2P file-sharing daemon.")
    parser.add_argument(
        "-s",
        "--serve-cli",
        metavar="[HOST:]PORT",
        help="Serve the daemon's CLI over the network",
    )
    namespace = parser.parse_args(args)
    return parse_server(namespace.serve_cli) if namespace.serve_cli else None


async def cli_main(args: List[str] = None):
    logging.basicConfig(
        filename='psi-project.log',
        filemode='a',
        encoding='utf-8',
        level=logging.DEBUG
    )
    serve_cli = parse_args(args)
    fp = FileManager()
    tcp = TcpServer(fp)
    udp = UdpServer(fp, tcp)
    commands = Commands(fp, tcp, udp)

    if serve_cli:
        host, port = serve_cli
        cli_server = await start_interactive_server(
            partial(make_cli, commands=commands), host, port
        )
        print_server(cli_server, "command line interface")
        cli_task = asyncio.create_task(cli_server.serve_forever())
    else:
        cli_task = asyncio.create_task(make_cli(commands).interact())

    logging.info("Cli started")

    tcp_task = tcp.runServer()
    udp_task = asyncio.create_task(serveUdpServer(udp))

    await asyncio.gather(cli_task, tcp_task, udp_task, return_exceptions=True)

    logging.info("Shuting down")
