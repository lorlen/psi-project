from asyncio import StreamReader, StreamWriter
from pathlib import Path
from typing import Callable, Optional
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


        async def do_get():
            addr = await self.udp.find_file(filename)

            if addr:
                await self.tcp.start_download(addr, filename)
                self.mgr.retrieve_file(filename, path)
            else:
                writer.write(f"File {filename} does not exist".encode())

        await self.try_to_connect(reader, writer, do_get)

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

        addr = await self.udp.find_file(filename)

        if addr:
            writer.write(f"File {filename} exists on host {addr}\n".encode())
        else:
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
            await self.udp.revoke_file(filename)

        self.mgr.remove_file(filename)

    async def fetch(self, reader: StreamReader, writer: StreamWriter, filename: str):
        addr = await self.udp.find_file(filename)

        async def do_fetch():
            if addr:
                await self.tcp.start_download(addr, filename)
                writer.write(f"Successfully fetched file {filename}\n".encode())
            else:
                writer.write(f"File {filename} does not exist\n".encode())

        await self.try_to_connect(reader, writer, do_fetch)

    async def try_to_connect(self, reader: StreamReader, writer: StreamWriter, func: Callable):
        try: 
            await func()
        except ConnectionRefusedError as e:
            writer.write(f"Could not connect to host, other host could end work.\n If you see this error again please check your network")
        except ConnectionResetError as e:
            writer.write(f"Connection was reset on the remote host, could not connect")
        except ConnectionAbortedError as e:
            writer.write(f"Connection was aborted by remote host")