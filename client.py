import asyncio
from typing import List, Optional, Dict

from aiohttp import ClientSession

from crypto import generate_keypair, save_keys, load_keys, keys_exist


class RemoteClient:
    _nickname: str
    _public_key: str
    _host: str
    _port: int

    def __init__(self, nickname: str, public_key: str, host: str, port: int):
        self._nickname = nickname
        self._public_key = public_key
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

    @property
    def public_key(self) -> str:
        return self._public_key


class PGPChat:
    _public_key: str
    _private_key: str
    _connected_clients: List[RemoteClient]
    _coordinator_address: str = "127.0.0.1"
    _listen_port: int
    _session: ClientSession

    def __init__(self, local_nickname: str, session: ClientSession):
        if not keys_exist(local_nickname):
            self._public_key, self._private_key = generate_keypair()
            save_keys(
                self._public_key,
                self._private_key,
                local_nickname
            )

        else:
            self._public_key, self._private_key = load_keys(local_nickname)

        self._session = session

    async def join_swarm(self):
        data = {
            "public_key": self._public_key
        }

        async with self._session.post(self.format_coordinator_url("join", args={}), json=data) as resp:
            body = await resp.json()
            listen_port = body.get("listen_port")
            if listen_port is None:
                print("Failed to join swarm")
                return

            self._listen_port = listen_port
            print(body, resp.status)

    async def client_handshake(self, target_public_key: str):
        url = self.format_coordinator_url("find-user", args=None)

        async with self._session.post(url, json={"public_key": target_public_key}) as resp:
            body = await resp.json()
            print(body)
            if resp.status != 200:
                return

    async def send_message(self, recipient: RemoteClient, message: str):
        pass

    def format_coordinator_url(self, endpoint: str, args: Optional[Dict[str, str]]) -> str:
        qs = ""
        if args is not None:
            qs = "?" + "&".join([f"{k}={v}" for k, v in args.items()])
            if len(args) == 0:
                qs = ""

        return f"http://{self._coordinator_address}/{endpoint}{qs}"

    @property
    def public_key(self) -> str:
        return self._public_key


async def main():
    async with ClientSession() as session:
        chat = PGPChat(input("Enter your nickname: "), session)
        await chat.join_swarm()
        await chat.client_handshake(chat.public_key)


if __name__ == "__main__":
    asyncio.run(main())
