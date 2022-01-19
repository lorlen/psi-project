import asyncio
import socket
from typing import Dict
import logging

from psi_project.core.message import ActionCode, StatusCode, Message
from psi_project.repo import FileManager
from psi_project.tcp import TcpServer

from psi_project.core import config
class UdpServer:
    def __init__(self, fp: FileManager, tcp: TcpServer):
        self.fp = fp
        self.tcp = tcp
        self.file_exists_futures: Dict[str, asyncio.Future] = {}
        logging.info("started UDP Server")

    def handle(self, message: Message, addr):
        logging.info(f"Received {message} from {addr}")
        if message.actionCode == ActionCode.ASK_IF_FILE_EXISTS:
            if self.fp.file_exists(message.details):
                owner_addr = self.fp.get_file_metadata(message.details)["owner_address"]
                logging.debug(f"File exists returning metadata {owner_addr}")
                return Message(
                    ActionCode.ANSWER_FILE_EXISTS,
                    StatusCode.FILE_EXISTS,
                    owner_addr,
                    message.details,
                )
            else:
                logging.debug(f"File doesn't exists")
                return Message(
                    ActionCode.ANSWER_FILE_EXISTS,
                    StatusCode.FILE_NOT_FOUND,
                    None,
                    message.details,
                )

        elif message.actionCode == ActionCode.ANSWER_FILE_EXISTS:
            if (
                message.status == StatusCode.FILE_EXISTS
                and message.details in self.file_exists_futures
            ):
                logging.debug(f"Finishing future {message.details}")
                self.file_exists_futures[message.details].set_result(addr[0])

        elif message.actionCode == ActionCode.REVOKE:
            meta = self.fp.get_file_metadata(message.details)
            if meta and meta["owner_address"] == addr[0]:
                if message.details in self.tcp.running_tasks:
                    logging.debug(f"Adding revoked callback to future: {message.details}")
                    self.tcp.running_tasks[message.details].add_done_callback(
                        lambda _: self._revoked_callback(message)
                    )
                else:
                    logging.debug(f"Removing file: {message.details}")
                    self.fp.remove_file(message.details)

    def _revoked_callback(self, message: Message):
        logging.info(f"Future done, removing file: {message.details}")
        self.fp.remove_file(message.details)

    def datagram_received(self, data, addr):
        logging.info(f"Received datagram: {data} from {addr}")

        received_message = Message.bytes_to_message(data)
        logging.debug(f"Decoed message {received_message}")

        answer = self.handle(received_message, addr)

        logging.debug(f"Answer after handling {answer}")
        if answer:
            logging.info(f"Sending return message {answer} to {addr}")
            self.transport.sendto(answer.message_to_bytes(), addr)

    async def find_file(self, filename, timeout: int = 10):
        logging.info(f"Finding file: {filename}")

        future = asyncio.get_event_loop().create_future()
        self.file_exists_futures[filename] = future

        message = Message(
            ActionCode.ASK_IF_FILE_EXISTS, StatusCode.NOT_APPLICABLE, None, filename
        )

        logging.debug(f"Created future and returning message: {message}")
        self.transport.sendto(message.message_to_bytes(), ("<broadcast>", config.UDP_PORT))

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            del self.file_exists_futures[filename]

    async def revoke_file(self, filename):
        logging.info(f"Revoking file: {filename}")
        message = Message(ActionCode.REVOKE, StatusCode.NOT_APPLICABLE, None, filename)
        self.transport.sendto(message.message_to_bytes(), ("<broadcast>", config.UDP_PORT))


class UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, server: UdpServer) -> None:
        self.server = server

    def connection_made(self, transport):
        pass

    def connection_lost(self, transport):
        pass

    def datagram_received(self, data, addr):
        self.server.datagram_received(data, addr)


async def serve_udp_server(server: UdpServer):
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UdpProtocol(server), local_addr=("0.0.0.0", config.UDP_PORT)
    )

    server.transport = transport
    sock = transport.get_extra_info("socket")
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
