import asyncio


async def tcp_echo_client(fileName):
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 8888)

    print(f'Started reading file')
    await asyncio.sleep(7)
    with open(fileName, "rb") as f:
        data = f.read()

    print(f'Send: ')
    writer.write(data)
    await  writer.drain()

    print('Close the connection')
    writer.close()

asyncio.run(tcp_echo_client('testFile.test'))