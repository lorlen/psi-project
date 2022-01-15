import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio.tasks import Task
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
        print(reader)
        print(writer)
        data = await reader.read()
        msg = await self.receiveMessage(reader, writer)
        print(f"Received  from {addr!r}")
        addr = writer.get_extra_info('peername')
        print("decing what to do with msg")
        if msg.status != Msg.START_DOWNLOADING:
            print(f"Bad req  from {addr!r}")
            returnMsg = Message(Msg.CONFIRMATION, Msg.BAD_REQUEST, "BAD ACTION")
            writer.close()
            return
        elif msg.details == 'test':
            print(f"Test  from {addr!r}")
            returnMsg = Message(Msg.CONFIRMATION, Msg.ACCEPT, "XXXXX")
        elif self.fp.file_exists(msg.details):
            print(f"Sending file to  {addr!r}")
            returnMsg = Message(Msg.CONFIRMATION, Msg.ACCEPT, self.fp.get_file_metadata(msg.details))
        else: 
            print(f"File not found for  {addr!r}")
            returnMsg = Message(Msg.CONFIRMATION, Msg.FILE_NOT_FOUND, "NOT FOUND")
            writer.close()
            return
        
        await self.sendMessage(reader, writer, returnMsg)
        await self.sendFile(reader, writer, msg.details)
        writer.close()

    async def receiveMessage(self, reader: StreamReader, writer: StreamWriter) -> Message:
        print("diwnea rzecz")
        data = await reader.read()
        print(f"xdd")
        msg = Message.bytes_to_message(data)
        msg.show_message()

        return msg

    async def saveFile(self, reader: StreamReader, writer: StreamWriter, fileName):
        data = await reader.read()
        addr = writer.get_extra_info('peername')

        print(f"Received  from {addr!r}")

        path = f"/var/tmp/received{self.count}.test"
        self.count += 1

        with open(path, 'wb') as f:
            f.write(data)

        self.fp.add_file(Path(path), addr)

    async def serveServer(self):
        server = await asyncio.start_server(self.handle, '0.0.0.0', 8888)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        async with server:
            await server.serve_forever()
    
    def runServer(self) -> Task:
        return asyncio.create_task(self.serveServer())

    def download(self, clinetIP: str, fileName: str):
        asyncio.run(self.startDownload(clinetIP,  fileName))

    async def startDownload(self, clinetIP: str, fileName: str):
        reader, writer = await asyncio.open_connection(clinetIP, 8888)
        msg = Message(Msg.START_DOWNLOADING, Msg.NOT_APPLICABLE, fileName)

        await self.sendMessage(reader, writer, msg)
        print("wating for return msg")
        msg = await self.receiveMessage(reader, writer) # get filename 
        await self.saveFile(reader, writer, msg.details)
        print("Close the connection")
        writer.close()


    async def sendMessage(self, reader: StreamReader, writer: StreamWriter, msg: Message):
        print(f'Sending Message')
        msg.show_message()
        writer.write(msg.message_to_bytes())
        await  writer.drain()
        print(f'Sent')

    async def sendFile(self, reader: StreamReader, writer: StreamWriter, fileName: str):
        print(f'Started reading file for file: {fileName}')
        if fileName == 'test':
            with open('testFile.test', "rb") as f:
                data = f.read()
        else:
            data = self.fp.read_file(fileName)
        self.send(reader, writer, data)

    async def send(self, reader: StreamReader, writer: StreamWriter, data: bytes):
        print(f'Sending: {len(data)}')
        writer.write(data)
        await  writer.drain()

        print('File message')


