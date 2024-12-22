import asyncio
import socket
from typing import List, Optional, Dict, Any, Tuple

from quart import Quart, request, jsonify, Response


class ClientAlreadyExists(Exception):
    def __init__(self):
        super().__init__("Client already exists in swarm")


class MissingField(Exception):
    _message: str

    def __init__(self, message: str):
        self._message = message
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message


class ActiveClient:
    _remote_address: str
    _listen_port: int
    _public_key: str

    def __init__(self, remote_address: str, listen_port: int, public_key: str):
        self._remote_address = remote_address
        self._listen_port = listen_port
        self._public_key = public_key

    def __hash__(self) -> int:
        return hash(self._public_key)

    async def handle_client(self, client):
        loop = asyncio.get_event_loop()
        rq = None
        while rq != 'quit':
            rq = (await loop.sock_recv(client, 255)).decode('utf8')
            response = str(eval(rq)) + '\n'
            await loop.sock_sendall(client, response.encode('utf8'))
        client.close()

    # port will signify which client is being targeted by the message
    async def run_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', self._listen_port))
        server.listen(8)
        server.setblocking(False)

        loop = asyncio.get_event_loop()
        print("running server")
        while True:
            client, _ = await loop.sock_accept(server)
            await loop.create_task(self.handle_client(client))

    @property
    def public_key(self) -> str:
        return self._public_key

    @property
    def remote_address(self) -> str:
        return self._remote_address

    @property
    def listen_port(self) -> int:
        return self._listen_port


class ClientList:
    _clients: Dict[int, ActiveClient]

    def __init__(self):
        self._clients = {}

    def add_client(self, client: ActiveClient):
        if self.search_for_client(client.public_key) is not None:
            raise ClientAlreadyExists()

        self._append(client)

    def search_for_client(self, public_key: str) -> Optional[ActiveClient]:
        return self._clients.get(hash(public_key))

    def _append(self, client: ActiveClient):
        self._clients[hash(client)] = client

    def __iter__(self) -> ActiveClient:
        for pkey_hash, client in self._clients:
            yield client


class Coordinator(Quart):
    _active_clients: ClientList
    _port_range: Tuple[int, int]
    _available_ports: List[int]
    _listener_tasks: Optional[asyncio.Queue[asyncio.Task]]

    def __init__(self, app_name: str, port_range: Tuple[int, int] = (5000, 6000)):
        self._active_clients = ClientList()
        self._port_range = port_range
        self._available_ports = list(range(*self._port_range))
        self._listener_tasks = None
        super().__init__(app_name)

    async def join(self) -> Tuple[Response, int]:
        post_body = await request.json
        try:
            values = self.search_body(post_body, ["public_key"])
            public_key = values[0]
        except MissingField as e:
            return jsonify({
                "success": False,
                "error": e.message
            }), 400

        client = self._active_clients.search_for_client(public_key)
        if client is not None:
            return jsonify({
                "success": False,
                "error": "Client already exists in swarm",
                "listen_port": client.listen_port
            }), 400

        listen_port = self._available_ports.pop(0)
        client = ActiveClient(
                request.remote_addr,
                listen_port,
                public_key
            )

        listen_task = asyncio.create_task(client.run_server())
        self._active_clients.add_client(client)

        if self._listener_tasks is None:
            self._listener_tasks = asyncio.Queue()

        await self._listener_tasks.put(listen_task)

        return jsonify({
            "success": True,
            "listen_port": listen_port
        }), 200

    async def find_user(self) -> Tuple[str, int]:
        post_body = await request.json
        try:
            values = self.search_body(post_body, ["public_key"])
            public_key = values[0]
        except MissingField as e:
            return e.message, 400

        client = self._active_clients.search_for_client(public_key)
        if client is None:
            return "Public key not active", 400

        return client.remote_address, 200

    @staticmethod
    def search_body(body: Optional[Dict[str, Any]], required_keys: List[str]) -> List[Any]:
        if body is None:
            raise MissingField(f"Missing request body")

        o = []
        for rk in required_keys:
            val = body.get(rk)
            if val is None:
                raise MissingField(f"Missing {rk}")

            o.append(val)

        return o

    def add_routes(self):
        self.route("/join", methods=["POST"])(self.join)
        self.route("/find-user", methods=["GET"])(self.find_user)


if __name__ == "__main__":
    sv = Coordinator("__main__")
    sv.add_routes()
    sv.run("0.0.0.0", 80)
