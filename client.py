import asyncio
from typing import Optional, Tuple

from crypto import generate_keypair


class PGPChat:
    _public_key: Optional[str]
    _private_key: Optional[str]
    _username: Optional[str]

    _coordinator_address: Tuple[str, int]
    _coordinator_writer: asyncio.StreamWriter
    _coordinator_reader: asyncio.StreamReader

    def __init__(self, coordinator_address: Tuple[str, int]):
        self._coordinator_address = coordinator_address

    async def connect(self):
        self._coordinator_reader, self._coordinator_writer = await asyncio.open_connection(*self._coordinator_address)

    async def register(self, username: str):
        self._username = username
        self._public_key, self._private_key = generate_keypair()

        self._coordinator_writer.write(f"register::{username}::{self._public_key}\n".encode('utf8'))
        response = await self._coordinator_reader.read(100)

        if response != b"Registered\n":
            print("Registration failed")
            return

        print("Registration successful")


async def main():
    chat = PGPChat(("localhost", 15555))
    await chat.connect()
    await chat.register("Alice")


if __name__ == "__main__":
    asyncio.run(main())
