import asyncio
from typing import Optional

import websockets
from aiohttp import ClientSession
from websockets.asyncio.client import ClientConnection


class ChatClient:
    _coordinator_host: str
    _coordinator_port: int
    _websocket: Optional[ClientConnection]
    _http_session: Optional[ClientSession]

    def __init__(self, host: str, port: int):
        self._coordinator_host = host
        self._coordinator_port = port

    async def connect(self):
        async with ClientSession() as self._http_session, websockets.connect(
                self._format_ws_uri(1, "/")) as self._websocket:
            pass

    async def test_http(self):
        async with self._http_session.get(self._format_http_uri("/")) as response:
            return await response.text()

    def _format_ws_uri(self, port: int, path: str) -> str:
        return f"ws://{self._coordinator_host}:{port}/{path}"

    def _format_http_uri(self, path: str) -> str:
        return f"http://{self._coordinator_host}:{self._coordinator_port}/{path}"


async def main():
    client = ChatClient("localhost", 8080)
    await client.connect()


if __name__ == '__main__':
    asyncio.run(main())
