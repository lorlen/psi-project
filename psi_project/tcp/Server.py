import asyncio
from asyncio.streams import StreamReader, StreamWriter
from asyncio.tasks import Task
from pathlib import Path
import tempfile
from typing import Dict
import logging

from psi_project.core.message import ActionCode, StatusCode, Message
from psi_project.repo import FileManager

class TcpServer:
    def __init__(self, fp: FileManager):
        self.fp = fp
        self.running_tasks: Dict[str, Task] = {}
        logging.info("Started TCP Server")


    #TODO: better infomation logging 
    async def handle(self, reader, writer):
        msg = await self.receiveMessage(reader, writer)
        
        addr = writer.get_extra_info('peername')
        logging.info(f"Received  from {addr!r}")
        logging.debug("decing what to do with msg")

        if msg.actionCode != ActionCode.START_DOWNLOADING:
            logging.info(f"Bad req  from {addr!r}")
            returnMsg = Message(ActionCode.CONFIRMATION, StatusCode.BAD_REQUEST, None, "BAD ACTION")
            writer.close()
            return
        # elif msg.details == 'test':
        #     returnMsg = Message(Msg.CONFIRMATION, Msg.ACCEPT, "XXXXX")
        elif self.fp.file_exists(msg.details):
            logging.info(f"Sending file to  {addr!r}")
            metaData = self.fp.get_file_metadata(msg.details)
            list(metaData.keys())
            returnMsg = Message(ActionCode.CONFIRMATION, StatusCode.ACCEPT, None)
        else: 
            logging.info(f"File not found for  {addr!r}")
            returnMsg = Message(ActionCode.CONFIRMATION, StatusCode.FILE_NOT_FOUND, None, "NOT FOUND")
            writer.close()
            return

        logging.debug(f"Sending Message")
        await self.sendMessage(reader, writer, returnMsg)
        await self.sendFile(reader, writer, msg.details)
        writer.close()

    async def receiveMessage(self, reader: StreamReader, writer: StreamWriter) -> Message:
        #TODO maybey handle details length correctly
        data = await reader.read(48)
        logging.trace(f"Received msg data {data} ")
        msg = Message.bytes_to_message(data)
        logging.debug(f"Received msg {data} ")

        return msg

    async def saveFile(self, reader: StreamReader, writer: StreamWriter, fileName):
        data = await reader.read()
        addr = writer.get_extra_info('peername')

        logging.info(f"Saving file: {fileName} from {addr!r}")

        with tempfile.NamedTemporaryFile(delete=False) as fp:
            self.count += 1
            fp.write(data)

        self.fp.add_file(Path(fp.name), name=fileName, owner_address=addr[0])

    async def serveServer(self):
        server = await asyncio.start_server(self.handle, '0.0.0.0', 8888)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logging.info(f'Serving on {addrs}')

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
        logging.info(f"Starting download to: {clinetIP}, file: {fileName}")
        reader, writer = await asyncio.open_connection(clinetIP, 8888)
        msg = Message(ActionCode.START_DOWNLOADING, StatusCode.NOT_APPLICABLE, None, fileName)

        await self.sendMessage(reader, writer, msg)
        logging.debug("wating for return msg")
        await self.receiveMessage(reader, writer) # get filename 
        await self.saveFile(reader, writer, msg.details)
        logging.info("Close the connection")
        writer.close()


    async def sendMessage(self, reader: StreamReader, writer: StreamWriter, msg: Message):
        logging.debug(f'Sending Message: {msg}')
        data = msg.message_to_bytes()
        logging.trace(f"Message data bytes {data}")
        writer.write(data)
        await  writer.drain()
        logging.debug(f'Sent')

    async def sendFile(self, reader: StreamReader, writer: StreamWriter, fileName: str):
        logging.debug(f'Started reading file for file: {fileName}')
        # if fileName == 'test':
        #     with open('testFile.test', "rb") as f:
        #         data = f.read()
        # else:
        data = self.fp.read_file(fileName)
        upload_task = asyncio.create_task(self.send(reader, writer, data))
        logging.trace("Task created")
        self.running_tasks[fileName] = upload_task
        await upload_task
        logging.trace("Task awaited")
        del self.running_tasks[fileName]

    async def send(self, reader: StreamReader, writer: StreamWriter, data: bytes):
        logging.info(f'Sending: {len(data)}')
        writer.write(data)
        await  writer.drain()

        logging.debug('Data sent')
