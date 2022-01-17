import socket
import asyncio
from asyncio.tasks import Task
from psi_project.repo import FileManager
from psi_project.message import Message
import psi_project.message as Msg



class UdpServer:
    def __init__(self, fp: FileManager, tcp):
        self.fp = fp
        self.tcp = tcp
        self.fileLocation = None
        print("started UDP Server")
    
    def handle(self, message: Message, addr):
        print("Handling")
        if message.actionCode == Msg.ASK_IF_FILE_EXISTS:
            print("Checking for file: {}".format(message.details))
            if self.fp.file_exists(message.details):
                
                return Msg.Message(Msg.ANSWER_FILE_EXISTS, Msg.FILE_EXISTS, message.details)
            else:
                
                return Msg.Message(Msg.ANSWER_FILE_EXISTS, Msg.FILE_NOT_FOUND, message.details)

        if message.actionCode == Msg.ANSWER_FILE_EXISTS:
            print("file exists check")

            if message.status == Msg.FILE_EXISTS:
                print(f"file {message.details} exists at {addr}")
                self.fileLocation = addr
                asyncio.create_task(self.tcp.startDownload(addr[0], message.details))
                return
            else :
                print(f"file not exists at {addr}")
                return

    def connection_made(self, transport):
        print("Connection Made")
        self.transport = transport

        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def datagram_received(self, data, addr):
        received_message = Msg.Message.bytes_to_message(data)
        # received_message.show_message()
        # 
        # answer = self.loop.create_task(self.handle(received_message, addr))        
        answer = self.handle(received_message, addr)

        if answer:
            answer.show_message()
            self.transport.sendto(answer.message_to_bytes(), addr)

    async def findFile(self, filename):
        message = Msg.Message(Msg.ASK_IF_FILE_EXISTS, Msg.NOT_APPLICABLE, filename)
        self.transport.sendto(message.message_to_bytes(), ('<broadcast>', 9000))

    async def revokeFile(self, filename):
        pass

    def serveServerLoop(self):
        server = self.loop.create_datagram_endpoint(
            lambda: self, local_addr=('0.0.0.0', 9000)
        )
        self.loop.server = self.loop.run_until_complete(server)

    def runServer(self):
        return asyncio.create_task(self.serveServer())

    async def serveServer(self):
        loop = asyncio.get_event_loop()
        # print("hallo")
        server = await loop.create_datagram_endpoint(
            lambda: self, local_addr=('0.0.0.0', 9000)
        )
        