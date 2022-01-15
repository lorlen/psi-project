from asyncio import StreamReader, StreamWriter
from pathlib import Path
from typing import Optional

from psi_project.repo import FileManager
from psi_project.tcp import Server

class Commands():
    def __init__(self, TCPServer: Server, UDPServer) -> None:
        self.tcp = TCPServer
        self.udp = UDPServer

    async def get(self, reader: StreamReader, writer: StreamWriter, filename: str, path: Path):
        manager = FileManager()

        if manager.file_exists(filename):
            manager.retrieve_file(filename, path)
            return

        # TODO: download the file from the network

        # tcp download
        await self.tcp.startDownload("127.0.0.1", filename)


        writer.write(f"File {filename} does not exist\n".encode())


    async def put(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        path: Path,
        filename: Optional[str] = None,
    ):
        manager = FileManager()

        if manager.file_exists(filename or path.name):
            writer.write(
                f"File {filename or path.name} already exists in the repository\n".encode()
            )
            return

        manager.add_file(path, filename)
        writer.write(
            f"Successfully added file {filename or path.name} to the repository\n".encode()
        )


    async def ls(self, reader: StreamReader, writer: StreamWriter):
        manager = FileManager()

        for row in manager.list_files():
            text = row["name"] + (
                f"(Owner: {row['owner_address']})" if row["owner_address"] else ""
            )
            writer.write((text + "\n").encode())


    async def exists(self, reader: StreamReader, writer: StreamWriter, filename: str):
        manager = FileManager()

        if manager.file_exists(filename):
            writer.write(f"File {filename} exists in the local repository\n".encode())
            return

        # TODO: ask the network whether the file exists

        writer.write(f"File {filename} does not exist\n".encode())
