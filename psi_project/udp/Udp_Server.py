import socket
import asyncio
import time

from psi_project.message import Message
import psi_project.message as Msg
from psi_project.repo import FileManager

class UdpServer:
    def connection_made(self, transport):
        self.transport = transport

    def handle(self, message):
        manager = FileManager()
        if message.actionCode == Msg.ASK_IF_FILE_EXISTS:
            print("Checking for file: {}".format(message.details))
            if manager.file_exists(message.details):
                return Msg.Message(Msg.ANSWER_FILE_EXISTS, Msg.FILE_EXISTS, message.details)
            else:
                return Msg.Message(Msg.ANSWER_FILE_EXISTS, Msg.FILE_NOT_FOUND, message.details)
        
        elif message.actionCode == Msg.REVOKE_FILE:
            if manager.file_exists(message.details):
                print("Revoking file: {}".format(message.details))
                manager.remove_file(message.details)
                return Msg.Message(Msg.CONFIRMATION, Msg.ACCEPT, message.details)
            else:
                return Msg.Message(Msg.CONFIRMATION, Msg.FILE_NOT_FOUND, message.details)
        
    def create_server_socket():
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Enable broadcasting mode
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.bind(("", 9999))
   
        return server

    def datagram_received(self, data, addr):
        received_message = Msg.Message.bytes_to_message(data)
        # print('Received message from {}:'.format(addr))
        # received_message.show_message() 
        received_message.log_message(addr)
        self.transport.sendto(self.handle(received_message).message_to_bytes(), addr)
        
    
    def runServer(self, loop):
        asyncio.run(self.serveServer(loop))

    async def serveServer(self, loop):
        print("Starting UDP server")

        # loop = asyncio.get_running_loop()

        # One protocol instance will be created to serve all
        # client requests.
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: UdpServer(),
            sock=UdpServer.create_server_socket())
        try:
            await asyncio.sleep(3600)  # Serve for 1 hour.
        finally:
            transport.close()