from typing import List, Optional, Dict, Any

from quart import Quart, request


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
    _public_key: str

    def __init__(self, remote_address: str, public_key: str):
        self._remote_address = remote_address
        self._public_key = public_key

    def __hash__(self) -> int:
        return hash(self._public_key)

    @property
    def public_key(self) -> str:
        return self._public_key

    @property
    def remote_address(self) -> str:
        return self._remote_address


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

    def __init__(self, app_name: str):
        super().__init__(app_name)

    async def join(self):
        post_body = await request.json
        try:
            values = self.search_body(post_body, ["public_key"])
            public_key = values[0]
        except MissingField as e:
            return e.message

        if self._active_clients.search_for_client(public_key) is not None:
            return "Already in swarm"

        self._active_clients.add_client(
            ActiveClient(
                request.remote_addr,
                public_key
            )
        )

    async def find_user(self):
        post_body = await request.json
        try:
            values = self.search_body(post_body, ["public_key"])
            public_key = values[0]
        except MissingField as e:
            return e.message

        client = self._active_clients.search_for_client(public_key)
        if client is None:
            return "Public key not active"

    @staticmethod
    def search_body(body: Optional[Dict[str, Any]], required_keys: List[str]) -> List[Any]:
        if body is None:
            raise MissingField(f"Missing request body")

        o = []
        for rk in required_keys:
            val = body.get(rk)
            if val is None:
                raise MissingField(f"Missing {val}")

            o.append(val)

        return o

    def add_routes(self):
        self.route("/join", methods=["POST"])(self.join)
        self.route("/find-user", methods=["GET"])(self.find_user)


if __name__ == "__main__":
    sv = Coordinator("__main__")
    sv.add_routes()
    sv.run("0.0.0.0", 80)
