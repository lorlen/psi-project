import asyncio
import struct
import udp_client
import message as msg
import sys


message = msg.Message(msg.ASK_IF_FILE_EXISTS, msg.NOT_APPLICABLE, sys.argv[1])
asyncio.run(udp_client.main(message))

