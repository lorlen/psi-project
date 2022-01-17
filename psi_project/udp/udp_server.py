import socket
import message as msg
import asyncio


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport


    def create_server_socket():
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # Enable broadcasting mode
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        server.bind(("", 9999))
   
        return server

    def datagram_received(self, data, addr):
        list_of_available_files = ["pierwszy", "drugi", "trzeci"]    # testowo
        received_message = msg.Message.bytes_to_message(data)
        print('Received message from {}:'.format(addr))
        
        received_message.show_message()   
        
        if (received_message.details in list_of_available_files):
            answer_message = msg.Message(msg.ANSWER_FILE_EXISTS, msg.FILE_EXISTS, received_message.details)
        else:
            answer_message = msg.Message(msg.ANSWER_FILE_EXISTS, msg.FILE_NOT_FOUND, received_message.details)
        self.transport.sendto(answer_message.message_to_bytes(), addr)


async def main():
    print("Starting UDP server")

    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all
    # client requests.
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        sock=EchoServerProtocol.create_server_socket())
    try:
        await asyncio.sleep(3600)  # Serve for 1 hour.
    finally:
        transport.close()


asyncio.run(main())
