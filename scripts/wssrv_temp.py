#!/bin/env python3

import asyncio
from websockets.server import serve

WS_HOST = '127.0.0.1'
WS_PORT = 8080


async def echo(websocket):
    async for message in websocket:
        print(f'RCV MSG: {message}')
        await websocket.send(message)

async def main():
    print(f'WS Server started at ws://{WS_HOST}:{WS_PORT}')
    async with serve(echo, WS_HOST, WS_PORT):
        await asyncio.Future()  # run forever

asyncio.run(main())
