from asyncio import StreamReader, StreamWriter
from pathlib import Path
from typing import Optional

from psi_project.repo import FileManager
from psi_project.tcp import TcpServer
from psi_project.udp import UdpServer


class Commands:
    def __init__(
        self, manager: FileManager, tcp_server: TcpServer, udp_server: UdpServer
    ) -> None:
        self.mgr = manager
        self.tcp = tcp_server
        self.udp = udp_server

    async def get(
        self, reader: StreamReader, writer: StreamWriter, filename: str, path: Path
    ):
        if self.mgr.file_exists(filename):
            self.mgr.retrieve_file(filename, path)
            return

        # TODO: move this section to fetch() and call fetch() from here
        await self.udp.findFile(filename)
        # tcp download
        # await self.tcp.startDownload("127.0.0.1", filename)

        # ======

        writer.write(f"File {filename} does not exist\n".encode())

    async def put(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        path: Path,
        filename: Optional[str] = None,
    ):
        if self.mgr.file_exists(filename or path.name):
            writer.write(
                f"File {filename or path.name} already exists in the repository\n".encode()
            )
            return

        self.mgr.add_file(path, filename)
        writer.write(
            f"Successfully added file {filename or path.name} to the repository\n".encode()
        )

    async def ls(self, reader: StreamReader, writer: StreamWriter):
        for row in self.mgr.list_files():
            text = row["name"] + (
                f" (Owner: {row['owner_address']})" if row["owner_address"] else ""
            )
            writer.write((text + "\n").encode())

    async def exists(self, reader: StreamReader, writer: StreamWriter, filename: str):
        if self.mgr.file_exists(filename):
            writer.write(f"File {filename} exists in the local repository\n".encode())
            return

        addr = self.udp.findFile(filename)

        if addr:
            writer.write(f"File {filename} exists on host {addr}\n".encode())
            return

        writer.write(f"File {filename} does not exist\n".encode())

    async def rm(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        filename: str,
        revoke: bool = False,
    ):
        if not self.mgr.file_exists(filename):
            writer.write(f"File {filename} does not exist\n".encode())
            return

        if revoke:
            await self.udp.revokeFile(filename)

        self.mgr.remove_file(filename)

    async def fetch(self, reader: StreamReader, writer: StreamWriter, filename: str):
        # TODO: download the file from the network
        raise NotImplementedError()
