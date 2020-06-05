#!/usr/bin/env python3
import argparse
from aiohttp import web
import aiohttp
import socket
import os

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--path')
parser.add_argument('--port')

LOGGED_IN = dict()


def init_session_data():
    return {"login": None}


async def websocket_handle(request):

    session_data = init_session_data()

    ws = web.WebSocketResponse(autoping=True, heartbeat=15)
    await ws.prepare(request)


    async def talk_fn(data):
        nonlocal ws
        await ws.send_json(data)


    async def handle_ws_msg(msg_json):
        nonlocal session_data
        nonlocal ws
        global LOGGED_IN

        if 'action' in msg_json:
            action = msg_json['action']
            if action == 'login':
                login = msg_json['data']
                if login in LOGGED_IN:
                    await ws.send_json({"status":"error", "reason":"That login is taken. Try another"})
                    return

                # logout if previously logged in
                try:
                    del LOGGED_IN[session_data['login']]
                except KeyError:
                    pass

                LOGGED_IN[login] = talk_fn
                session_data['login'] = login
                await ws.send_json({"status":"success"})

            if action == 'get_user_list':
                await ws.send_json({
                    "status":"success",
                    "data":f"{list(LOGGED_IN)}"
                })
            if action == 'talk':
                target = msg_json['data']
                _talk = LOGGED_IN.get(target)
                if _talk is not None:
                    await _talk({"data": "Hi"})



    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                LOGGED_IN[session_data["login"]] = talk_fn
                await ws.close()
            else:
                await handle_ws_msg(msg.json())
        elif msg.type == aiohttp.WSMsgType.ERROR:
            try:
                del LOGGED_IN[session_data["login"]]
            except KeyError:
                pass
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
