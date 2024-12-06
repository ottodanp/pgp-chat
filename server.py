import asyncio
import socket
from typing import Tuple, List

from db import DbHandler


class ActiveClient:
    _remote_address: Tuple[str, int]
    _client: socket.socket
    _username: str
    _loop: asyncio.AbstractEventLoop

    def __init__(self, remote_address: Tuple[str, int], client: socket.socket, username: str):
        self._remote_address = remote_address
        self._client = client
        self._username = username
        self._loop = asyncio.get_event_loop()

    async def send_message(self, message: str) -> bytes:
        self._client.sendall(message.encode("utf8"))
        return await self._loop.sock_recv(self._client, 8192)

    def __eq__(self, other: "ActiveClient") -> bool:
        return self._username == other._username


class Coordinator:
    _bind_address = ("localhost", 15555)
    _clients: List[ActiveClient] = []
    _server: socket.socket
    _loop: asyncio.AbstractEventLoop
    _db_handler: DbHandler

    def __init__(self, db_name: str = "coordinator.db"):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind(self._bind_address)
        self._server.setblocking(False)
        self._loop = asyncio.get_event_loop()
        self._db_handler = DbHandler(db_name)
        self._db_handler.up()

    async def handle_client(self, client: socket.socket):
        remote_address = client.getpeername()
        response = b""
        request = (await self._loop.sock_recv(client, 8192)).decode('utf8')
        if request.startswith("register"):
            print(request)
            _, username, public_key = request.split("::")
            ac = ActiveClient(remote_address, client, username)
            self._clients.append(ac)
            await ac.send_message("Registered\n")

        elif request.startswith("open"):
            print()
        else:
            response = b"Invalid command\n"

        await self._loop.sock_sendall(client, response)

        client.close()

    async def run_server(self):
        self._server.listen(8)

        while True:
            client, _ = await self._loop.sock_accept(self._server)
            await self._loop.create_task(self.handle_client(client))


async def main():
    c = Coordinator()
    await c.run_server()


if __name__ == "__main__":
    asyncio.run(main())
