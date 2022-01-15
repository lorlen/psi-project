import socket
import asyncio
from psi_project.message import Message
import psi_project.message as Msg

class UdpClient:
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None
        
    def create_client_socket():
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,     socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Enable broadcasting mode
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        client.settimeout(0.2)

        return client
    
    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message, ('<broadcast>', 9999))
    
    def datagram_received(self, data, addr):
        print('\nReceived answer from {}:'.format(addr))
        msg = Msg.Message.bytes_to_message(data)
        msg.show_message()

        if msg.status == 201:
            print(f"File found on node: {addr!r}")
            # print(Msg.Message.bytes_to_message(self.message).actionCode)
        else:
            print("File found not found")

        print(Msg.Message.bytes_to_message(self.message).actionCode)
        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)
    
async def check_file(name):
    # How to retive data ?
    # We need to ignore our datagram
    message = Msg.Message(Msg.ASK_IF_FILE_EXISTS, Msg.NOT_APPLICABLE, name)
    await serveServer(message)

# async def get_file(name):
#     message = Msg.Message(Msg.ASK_IF_FILE_EXISTS, Msg.NOT_APPLICABLE, name)

async def serveServer(message):
    message = message.message_to_bytes()
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()
    transport, protocol = await loop.create_datagram_endpoint(
    lambda: UdpClient(message, on_con_lost),
    sock=UdpClient.create_client_socket())

    try:
        await asyncio.wait_for(on_con_lost, timeout=3.0)
    except asyncio.TimeoutError:
        print('no answer')