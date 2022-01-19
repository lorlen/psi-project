from asyncio import StreamReader, StreamWriter
from pathlib import Path
from typing import Optional
import logging

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

        addr = await self.udp.find_file(filename)

        if addr:
            await self.tcp.start_download(addr, filename)
            self.mgr.retrieve_file(filename, path)
        else:
            writer.write(f"File {filename} does not exist".encode())

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

        if not path.is_file():
            writer.write(f"Filesystem path {path} is not an existing file\n".encode())
            return

        self.mgr.add_file(path, filename)
        writer.write(
            f"Successfully added file {filename or path.name} to the repository\n".encode()
        )

    async def ls(self, reader: StreamReader, writer: StreamWriter):
        for row in self.mgr.list_files():
            text = (
                row["name"]
                + (f" (Owner: {row['owner_address']})" if row["owner_address"] else "")
                + (" (Revoked)" if row["revoked"] == 1 else "")
            )
            writer.write((text + "\n").encode())

    async def exists(self, reader: StreamReader, writer: StreamWriter, filename: str):
        if self.mgr.file_exists(filename):
            writer.write(f"File {filename} exists in the local repository\n".encode())
            return

        addr = await self.udp.find_file(filename)

        if addr:
            writer.write(f"File {filename} exists on host {addr}\n".encode())
        else:
            writer.write(f"File {filename} does not exist\n".encode())

    async def rm(self, reader: StreamReader, writer: StreamWriter, filename: str):
        if not self.mgr.file_exists(filename):
            writer.write(f"File {filename} does not exist\n".encode())
            return

        self.mgr.remove_file(filename)

    async def revoke(self, reader: StreamReader, writer: StreamWriter, filename: str):
        await self.udp.revoke_file(filename)
        self.mgr.revoke_file(filename)

    async def fetch(self, reader: StreamReader, writer: StreamWriter, filename: str):
        addr = await self.udp.find_file(filename)

        if addr:
            await self.tcp.start_download(addr, filename)
            writer.write(f"Successfully fetched file {filename}\n".encode())
        else:
            writer.write(f"File {filename} does not exist\n".encode())
