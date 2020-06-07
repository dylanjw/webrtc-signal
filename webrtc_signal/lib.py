#!/usr/bin/env python3
import aiohttp
from toolz import curry


def init_session_data():
    return {
        "login": None,
        "LOGGED_IN": None,
        "talk_fn": None,
    }


async def handle_login(session, msg):
    new_login = msg['data']

    if new_login in session['LOGGED_IN']:
        await session['talk_fn'](
            {
                "status": "error",
                "reason": "That login is taken. Try another"
            }
        )
        return

    # logout if previously logged in
    try:
        del session['LOGGED_IN'][session['login']]
    except KeyError:
        pass

    session['LOGGED_IN'][new_login] = session['talk_fn']
    session['login'] = new_login
    await session['talk_fn']({"action":"login", "status": "success"})


@curry
async def handle_ws_msg(session, msg):
    if 'action' in msg:
        action = msg['action']
        if action == 'login':
            await handle_login(session, msg)

        if action == 'get_user_list':
            await session['talk_fn']({
                "action": "get_user_list",
                "status": "success",
                "data": list(session['LOGGED_IN']),
            })

        if action == 'talk':
            target = msg['target']
            talk_to_peer = session['LOGGED_IN'].get(target)
            if talk_to_peer is not None:
                await talk_to_peer({
                    "action": "talk",
                    "data": msg['data'],
                    "sender": session['login']
                })


def setup_ws_connection_handler(LOGGED_IN):
    async def handler(request):
        nonlocal LOGGED_IN

        session = init_session_data()

        ws = aiohttp.web.WebSocketResponse(autoping=True, heartbeat=15)
        await ws.prepare(request)

        async def talk_fn(data):
            nonlocal ws
            await ws.send_json(data)

        session['talk_fn'] = talk_fn
        session['LOGGED_IN'] = LOGGED_IN

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == 'close':
                        LOGGED_IN[session["login"]] = talk_fn
                        await ws.close()
                    else:
                        await handle_ws_msg(session, msg.json())
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    try:
                        del LOGGED_IN[session["login"]]
                    except KeyError:
                        pass
                    print(
                        'ws connection closed with exception %s' % ws.exception())
        finally:
            try:
                del LOGGED_IN[session["login"]]
            except KeyError:
                pass


        print('websocket connection closed')

        return ws
    return handler
