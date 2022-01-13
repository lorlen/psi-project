import asyncio
from asyncio.streams import StreamReader, StreamWriter
from psi_project.repo import FileManager
from pathlib import Path

class Server:
    def __init__(self, fp: FileManager):
        self.fp = fp
        # needs to be atomic ?
        self.count = 0 # count for temp files, for uniq file names

    
    async def handle(self, reader, writer):
        fileName = self.receiveMessage(reader, writer)
        await self.sendMessage(reader, writer)
        await self.sendFile(reader, writer, fileName)

    def receiveMessage(self, reader: StreamReader, writer: StreamWriter) -> str:
        #decode message
        pass

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
        self.sendMessage(reader, writer, fileName)
        self.saveFile(reader, writer)


    async def sendMessage(self, reader: StreamReader, writer: StreamWriter):
        #Send Message to start download, make it generic
        pass

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
