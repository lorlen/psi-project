from argparse import ArgumentParser
import asyncio
from pathlib import Path
from typing import List

from aioconsole import AsynchronousCli, start_interactive_server
from aioconsole.server import parse_server, print_server

from psi_project.repo.file_manager import FileManager

from . import commands

from psi_project.udp import  UdpServer
from psi_project.tcp import Server


def make_cli(streams=None):
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

    cmds = {
        "get": (commands.get, get_parser),
        "put": (commands.put, put_parser),
        "ls": (commands.ls, ls_parser),
        "exists": (commands.exists, exists_parser),
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


def main(args: List[str] = None):
    loop = asyncio.get_event_loop()
    serve_cli = parse_args(args)

    if serve_cli:
        host, port = serve_cli
        server = loop.run_until_complete(start_interactive_server(make_cli, host, port))
        print_server(server, "command line interface")
    else:
        asyncio.ensure_future(make_cli().interact())
        
    # starting servers
    udp_server = UdpServer()
    asyncio.ensure_future(udp_server.serveServer(loop))

    # I thought we should start server with every new udp message about download ...
    manager = FileManager()
    tcp_server = Server(manager)
    asyncio.ensure_future(tcp_server.serveServer(loop))


    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
