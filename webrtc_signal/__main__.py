#!/usr/bin/env python3
import argparse
from aiohttp import web
import aiohttp
import socket
import os

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--path')
parser.add_argument('--port')

LOGGED_IN = set()


def init_session_data():
    return {"login": None}


async def websocket_handle(request):

    session_data = init_session_data()

    async def handle_ws_msg(ws, msg_json):
        nonlocal session_data
        global LOGGED_IN

        if 'action' in msg_json:
            action = msg_json['action']
            if action == 'login':
                login = msg_json['data']
                if login in LOGGED_IN:
                    ws.send_str("That login is taken. Try another")
                    return

                LOGGED_IN.add(login)
                session_data['login'] = login
                ws.send_str(f"Logged in as: {login}")


    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        print(msg)
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                LOGGED_IN.remove(session_data["login"])
                await ws.close()
            else:
                await handle_ws_msg(ws, msg.json())
        elif msg.type == aiohttp.WSMsgType.ERROR:
            LOGGED_IN.remove(session_data["login"])
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
