import asyncio
from typing import Tuple, Dict, Any, Union

import websockets
from quart import Quart, jsonify, Response
from websockets.asyncio.server import ServerConnection, Server


class CoordinatorServer(Quart):
    _websocket: ServerConnection
    _server: Server

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def hello(self) -> Tuple[Response, int]:
        data = self.format_message("Hello, world!")
        return self.response(data)

    async def initialize(self) -> None:
        # Add routes for the quart server
        self.route("/", methods=["GET"])(self.hello)

        # Run the http and websocket servers concurrently
        await asyncio.gather(
            self.run_http_server(),
            self.run_ws_server()
        )

    async def run_http_server(self):
        self.run()

    async def run_ws_server(self):
        self._server = await websockets.serve(self._server_handler, "localhost", 8765)
        await self._server.wait_closed()

    @staticmethod
    async def _server_handler(websocket: ServerConnection) -> None:
        try:
            async for message in websocket:
                print(f"Received: {message}")
                response = f"Echo: {message}"
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")

    @staticmethod
    def response(data: Dict[str, Any], status: int = 200) -> Tuple[Response, int]:
        # Return a response with the given data and status code
        return jsonify(data), status

    @staticmethod
    def format_message(message: Union[str, Dict[str, Any]], success: bool = True) -> Dict[str, str]:
        # Format a message with the given success status
        result = "success" if success else "error"
        return {result: message}


async def main():
    app = CoordinatorServer(__name__)
    await app.initialize()


if __name__ == '__main__':
    asyncio.run(main())
