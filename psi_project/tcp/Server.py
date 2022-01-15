import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio.tasks import Task
from psi_project.repo import FileManager
from pathlib import Path
from psi_project.message import Message
import psi_project.message as Msg
import tempfile

class Server:
    def __init__(self, fp: FileManager):
        self.fp = fp
        # needs to be atomic ?
        self.count = 0 # count for temp files, for uniq file names
        print(self.fp.list_files())

    #TODO: better infomation logging 
    async def handle(self, reader, writer):
        msg = await self.receiveMessage(reader, writer)
        
        addr = writer.get_extra_info('peername')
        print(f"Received  from {addr!r}")
        print("decing what to do with msg")

        if msg.actionCode != Msg.START_DOWNLOADING:
            print(f"Bad req  from {addr!r}")
            returnMsg = Message(Msg.CONFIRMATION, Msg.BAD_REQUEST, "BAD ACTION")
            writer.close()
            return
        # elif msg.details == 'test':
        #     print(f"Test  from {addr!r}")
        #     returnMsg = Message(Msg.CONFIRMATION, Msg.ACCEPT, "XXXXX")
        elif self.fp.file_exists(msg.details):
            print(f"Sending file to  {addr!r}")
            metaData = self.fp.get_file_metadata(msg.details)
            list(metaData.keys())
            returnMsg = Message(Msg.CONFIRMATION, Msg.ACCEPT, )
        else: 
            print(f"File not found for  {addr!r}")
            returnMsg = Message(Msg.CONFIRMATION, Msg.FILE_NOT_FOUND, "NOT FOUND")
            writer.close()
            return
        
        await self.sendMessage(reader, writer, returnMsg)
        await self.sendFile(reader, writer, msg.details)
        writer.close()

    async def receiveMessage(self, reader: StreamReader, writer: StreamWriter) -> Message:
        #TODO maybey handle details length correctly
        data = await reader.read(48)
        print(data)
        msg = Message.bytes_to_message(data)
        msg.show_message()

        return msg

    async def saveFile(self, reader: StreamReader, writer: StreamWriter, fileName):
        data = await reader.read()
        addr = writer.get_extra_info('peername')

        print(f"Received  from {addr!r}")

        fp = tempfile.NamedTemporaryFile(delete=False)
        self.count += 1

        fp.write(data)

        self.fp.add_file(Path(fp.name), name=fileName, owner_address=addr[0])
        print(self.fp.list_files())

    async def serveServer(self):
        server = await asyncio.start_server(self.handle, '0.0.0.0', 8888)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        async with server:
            await server.serve_forever()
    
    def serveServerLoop(self, loop):
        server = asyncio.start_server(self.handle, '0.0.0.0', 8888)
        loop.server = loop.run_until_complete(server)


    def runServer(self) -> Task:
        return asyncio.create_task(self.serveServer())

    def download(self, clinetIP: str, fileName: str):
        asyncio.run(self.startDownload(clinetIP,  fileName))

    async def startDownload(self, clinetIP: str, fileName: str):
        reader, writer = await asyncio.open_connection(clinetIP, 8888)
        msg = Message(Msg.START_DOWNLOADING, Msg.NOT_APPLICABLE, fileName)

        await self.sendMessage(reader, writer, msg)
        print("wating for return msg")
        await self.receiveMessage(reader, writer) # get filename 
        await self.saveFile(reader, writer, msg.details)
        print("Close the connection")
        writer.close()


    async def sendMessage(self, reader: StreamReader, writer: StreamWriter, msg: Message):
        print(f'Sending Message')
        msg.show_message()
        data = msg.message_to_bytes()
        print(data)
        writer.write(data)
        await  writer.drain()
        print(f'Sent')

    async def sendFile(self, reader: StreamReader, writer: StreamWriter, fileName: str):
        print(f'Started reading file for file: {fileName}')
        # if fileName == 'test':
        #     with open('testFile.test', "rb") as f:
        #         data = f.read()
        # else:
        data = self.fp.read_file(fileName)
        await self.send(reader, writer, data)

    async def send(self, reader: StreamReader, writer: StreamWriter, data: bytes):
        print(f'Sending: {len(data)}')
        writer.write(data)
        await  writer.drain()

        print('File message')


