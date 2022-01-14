import asyncio
from asyncio.streams import StreamReader, StreamWriter
from psi_project.repo import FileManager
from pathlib import Path
from psi_project.message import Message
import psi_project.message as Msg

class Server:
    def __init__(self, fp: FileManager):
        self.fp = fp
        # needs to be atomic ?
        self.count = 0 # count for temp files, for uniq file names

    #TODO: better infomation logging 
    async def handle(self, reader, writer):
        msg = self.receiveMessage(reader, writer)

        if msg.status != Msg.START_DOWNLOADING:
            returnMsg = Message(Msg.CONFIRMATION, Msg.BAD_REQUEST, "BAD ACTION")
            return
        elif self.fp.file_exists(msg.details):
            returnMsg = Message(Msg.CONFIRMATION, Msg.ACCEPT, self.fp.get_file_metadata(msg.details))
        else: 
            returnMsg = Message(Msg.CONFIRMATION, Msg.FILE_NOT_FOUND, "NOT FOUND")
        
        await self.sendMessage(reader, writer, returnMsg)
        await self.sendFile(reader, writer, msg.details)

    async def receiveMessage(self, reader: StreamReader, writer: StreamWriter) -> Message:
        data = await reader.read()
        msg = Message.bytes_to_message(data)

        return msg

    async def saveFile(self, reader: StreamReader, writer: StreamWriter):
        data = await reader.read()
        addr = writer.get_extra_info('peername')

        print(f"Received  from {addr!r}")

        path = f"/var/tmp/received{self.count}.test"
        self.count += 1

        with open(path, 'wb') as f:
            f.write(data)
    
        print("Close the connection")
        writer.close()

        self.fp.add_file(Path(path), addr)

    async def serveServer(self):
        server = await asyncio.start_server(self.handle, '0.0.0.0', 8888)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        async with server:
            await server.serve_forever()
    
    def runServer(self):
        asyncio.run(self.serveServer())

    def download(self, clinetIP: str, fileName: str):
        asyncio.run(self.startDownload(clinetIP,  fileName))

    async def startDownload(self, clinetIP: str, fileName: str):
        reader, writer = await asyncio.open_connection(clinetIP, 8888)
        msg = Message(Msg.START_DOWNLOADING, Msg.NOT_APPLICABLE, )

        self.sendMessage(reader, writer, fileName)
        self.saveFile(reader, writer)


    async def sendMessage(self, reader: StreamReader, writer: StreamWriter, msg: Message):
        print(f'Sending Message')
        msg.print_message()
        writer.write(msg.message_to_bytes())
        await  writer.drain()

    async def sendFile(self, reader: StreamReader, writer: StreamWriter, fileName: str):
        print(f'Started reading file for file: {fileName}')
        data = self.fp.read_file(fileName)
        self.send(reader, writer, data)

    async def send(self, reader: StreamReader, writer: StreamWriter, data: bytes):
        print(f'Sending: {len(data)}')
        writer.write(data)
        await  writer.drain()

        print('File message')
        writer.close()
