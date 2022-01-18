import asyncio
import socket
from typing import Dict

from psi_project.core.message import ActionCode, StatusCode, Message
from psi_project.repo import FileManager
from psi_project.tcp import TcpServer


class UdpServer(asyncio.DatagramProtocol):
    def __init__(self, fp: FileManager, tcp: TcpServer):
        self.fp = fp
        self.tcp = tcp
        self.file_exists_futures: Dict[str, asyncio.Future] = {}
        print("started UDP Server")
    
    def handle(self, message: Message, addr):
        if message.actionCode == ActionCode.ASK_IF_FILE_EXISTS:
            if self.fp.file_exists(message.details):
                owner_addr = self.fp.get_file_metadata(message.details)["owner_address"]
                return Message(ActionCode.ANSWER_FILE_EXISTS, StatusCode.FILE_EXISTS, owner_addr, message.details)
            else:
                return Message(ActionCode.ANSWER_FILE_EXISTS, StatusCode.FILE_NOT_FOUND, None, message.details)

        elif message.actionCode == ActionCode.ANSWER_FILE_EXISTS:
            if message.status == StatusCode.FILE_EXISTS and message.details in self.file_exists_futures:
                self.file_exists_futures[message.details].set_result(addr)

        elif message.actionCode == ActionCode.REVOKE:
            if message.details in self.tcp.running_tasks:
                self.tcp.running_tasks[message.details].add_done_callback(lambda _: self.fp.remove_file(message.details))
            else:
                self.fp.remove_file(message.details)

    def connection_made(self, transport):
        self.transport = transport

        sock = transport.get_extra_info("socket")
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def datagram_received(self, data, addr):
        received_message = Message.bytes_to_message(data)
        answer = self.handle(received_message, addr)

        if answer:
            answer.show_message()
            self.transport.sendto(answer.message_to_bytes(), addr)

    async def findFile(self, filename, timeout: int = 10):
        future = asyncio.get_event_loop().create_future()
        self.file_exists_futures[filename] = future
        message = Message(ActionCode.ASK_IF_FILE_EXISTS, StatusCode.NOT_APPLICABLE, None, filename)
        self.transport.sendto(message.message_to_bytes(), ('<broadcast>', 9000))
        
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            del self.file_exists_futures[filename]

    async def revokeFile(self, filename):
        message = Message(ActionCode.REVOKE, StatusCode.NOT_APPLICABLE, None, filename)
        self.transport.sendto(message.message_to_bytes(), ("<broadcast>", 9000))

    def runServer(self):
        return asyncio.create_task(self.serveServer())

    async def serveServer(self):
        loop = asyncio.get_event_loop()
        server = await loop.create_datagram_endpoint(
            UdpServer, local_addr=('0.0.0.0', 9000)
        )
        