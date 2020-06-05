#!/usr/bin/env python3
import argparse
from aiohttp import web
import aiohttp
import socket
import os

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--path')
parser.add_argument('--port')

async def websocket_handle(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        print(msg)
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

args = parser.parse_args()

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    os.unlink(args.path)
except FileNotFoundError:
    pass
s.bind(args.path)
os.chown(args.path, 33, 33)

app = web.Application()
app.add_routes([web.get('/ws', websocket_handle)])


web.run_app(app, sock=s)
