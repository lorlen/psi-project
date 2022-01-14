import socket
import time
import struct
import sys
import threading
import asyncio
#from message import Message
import message as msg
class EchoClientProtocol:
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
        msg.Message.bytes_to_message(data).show_message()
        
        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)


async def main(message):
    message = message.message_to_bytes()
    loop = asyncio.get_running_loop()
    on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(message, on_con_lost),
        sock=EchoClientProtocol.create_client_socket())
    try:
        await asyncio.wait_for(on_con_lost, timeout=3.0)
        #await asyncio.sleep(5)
    except asyncio.TimeoutError:
        print('no answer')
    #finally:
     #   transport.close()

