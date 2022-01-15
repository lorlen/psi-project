from argparse import ArgumentParser
import asyncio
from pathlib import Path
from typing import List
from psi_project.tcp import Server
from psi_project.repo import FileManager

from aioconsole import AsynchronousCli, start_interactive_server
from aioconsole.server import parse_server, print_server

from .commands import Commands
from psi_project.cli import commands


def make_cli(commands: Commands, streams=None):
    get_parser = ArgumentParser(description="Download a file onto the local filesystem")
    get_parser.add_argument("filename", help="filename to search for in the network")
    get_parser.add_argument(
        "path", type=Path, help="local filesystem path to store the file in"
    )

    put_parser = ArgumentParser(description="Put a file in the daemon's repository")
    put_parser.add_argument(
        "path", type=Path, help="filesystem path from which to take the file"
    )
    put_parser.add_argument(
        "filename", nargs="?", help="custom name to store the file under"
    )

    ls_parser = ArgumentParser(
        description="List all files in the daemon's local repository"
    )

    exists_parser = ArgumentParser(
        description="Check if the file exists in the network"
    )
    exists_parser.add_argument("filename", help="filename to check existence of")

    rm_parser = ArgumentParser(
        description="Remove a file from the local repository"
    )
    rm_parser.add_argument("filename", help="file to remove")

    cmds = {
        "get": (commands.get, get_parser),
        "put": (commands.put, put_parser),
        "ls": (commands.ls, ls_parser),
        "exists": (commands.exists, exists_parser),
        "rm": (commands.rm, rm_parser),
    }

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

def mainProgram(args: List[str] = None):
    loop = asyncio.get_event_loop()
    serve_cli = parse_args(args)
    fp = FileManager()
    tcp = Server(fp)
    commands = Commands(tcp, None)
    tcp.serveServerLoop(loop)

    if serve_cli:
        host, port = serve_cli
        server = loop.run_until_complete(start_interactive_server(make_cli, host, port))
        print_server(server, "command line interface")
    else:
        loop.run_until_complete(make_cli(commands).interact())

    # TODO: start the UDP server
