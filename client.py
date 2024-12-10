import asyncio
from typing import List, Optional, Dict

from aiohttp import ClientSession

from crypto import generate_keypair, save_keys, load_keys, keys_exist


class RemoteClient:
    _nickname: str
    _host: str
    _port: int

    def __init__(self, nickname: str, host: str, port: int):
        self._nickname = nickname
        self._host = host
        self._port = port

    @property
    def nickname(self) -> str:
        return self._nickname

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port


class PGPChat:
    _public_key: str
    _private_key: str
    _connected_clients: List[RemoteClient]
    _coordinator_address: str = "127.0.0.1"
    _session: ClientSession

    def __init__(self, local_nickname: str, session: ClientSession):
        if not keys_exist(local_nickname):
            self._public_key, self._private_key = generate_keypair()
            save_keys(
                self._public_key,
                self._private_key,
                local_nickname
            )
            self._session = session

        else:
            self._public_key, self._private_key = load_keys(local_nickname)

    async def join_swarm(self):
        async with self._session.get(self.format_coordinator_url("join", args={})) as resp:
            body = await resp.text()

    def format_coordinator_url(self, endpoint: str, args: Optional[Dict[str, str]]) -> str:
        return f"http://{self._coordinator_address}/{endpoint}"


async def main():
    async with ClientSession() as session:
        chat = PGPChat("Otto", session)
        await chat.join_swarm()


if __name__ == "__main__":
    asyncio.run(main())
