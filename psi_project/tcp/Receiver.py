import asyncio
# from psi_project.repo import FileManager


class Receiver:
    # def __init__(self, fp: FileManager):
    #     self.fp = fp

    
    async def handle(self, reader, writer):

        data = await reader.read()

        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received  from {addr!r}")

        with open(f"recived{self.count}.test", 'wb') as f:
            f.write(data)
        self.count += 1

        print("Close the connection")
        writer.close()

    async def main(self):
        self.count = 0
        server = await asyncio.start_server(self.handle, '0.0.0.0', 8888)

        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        async with server:
            await server.serve_forever()
    
    def run(self):
        asyncio.run(self.main())


r = Receiver()
r.run()