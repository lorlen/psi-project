import asyncio
import socket

from psi_project.repo import FileManager
from psi_project.core.message import ActionCode, StatusCode, Message


class UdpServer:
    def __init__(self, fp: FileManager, tcp):
        self.fp = fp
        self.tcp = tcp
        self.fileLocation = None
        print("started UDP Server")
    
    def handle(self, message: Message, addr):
        print("Handling")
        if message.actionCode == ActionCode.ASK_IF_FILE_EXISTS:
            print("Checking for file: {}".format(message.details))
            if self.fp.file_exists(message.details):
                
                return Message(ActionCode.ANSWER_FILE_EXISTS, StatusCode.FILE_EXISTS, None, message.details)
            else:
                
                return Message(ActionCode.ANSWER_FILE_EXISTS, StatusCode.FILE_NOT_FOUND, None, message.details)

        if message.actionCode == ActionCode.ANSWER_FILE_EXISTS:
            print("file exists check")

            if message.status == StatusCode.FILE_EXISTS:
                print(f"file {message.details} exists at {addr}")
                self.fileLocation = addr
                asyncio.create_task(self.tcp.startDownload(addr[0], message.details))
                return
            else :
                print(f"file not exists at {addr}")
                return

        elif message.actionCode == ActionCode.REVOKE:
            # TODO
            pass

    def connection_made(self, transport):
        print("Connection Made")
        self.transport = transport

        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def datagram_received(self, data, addr):
        received_message = Message.bytes_to_message(data)
        # received_message.show_message()
        # 
        # answer = self.loop.create_task(self.handle(received_message, addr))        
        answer = self.handle(received_message, addr)

        if answer:
            answer.show_message()
            self.transport.sendto(answer.message_to_bytes(), addr)

    async def findFile(self, filename):
        message = Message(ActionCode.ASK_IF_FILE_EXISTS, StatusCode.NOT_APPLICABLE, None, filename)
        self.transport.sendto(message.message_to_bytes(), ('<broadcast>', 9000))

    async def revokeFile(self, filename):
        message = Message(ActionCode.REVOKE, StatusCode.NOT_APPLICABLE, None, filename)
        self.transport.sendto(message.message_to_bytes(), ("<broadcast>", 9000))

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
        