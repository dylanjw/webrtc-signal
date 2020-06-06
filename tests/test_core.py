import pytest
import json

from webrtc_signal.lib import setup_ws_connection_handler

from aiohttp import web

LOGGED_IN = {}

@pytest.fixture
async def app():
    global LOGGED_IN
    handler = setup_ws_connection_handler(LOGGED_IN)
    app = web.Application()
    app.router.add_get('/', handler)
    return app


@pytest.fixture
async def client1(app, aiohttp_client):
    client = await aiohttp_client(app)
    async with client.ws_connect('/') as conn:
        yield conn.send_json, conn.receive_json


@pytest.fixture
async def client2(app, aiohttp_client):
    client = await aiohttp_client(app)
    async with client.ws_connect('/') as conn:
        yield conn.send_json, conn.receive_json


async def test_ws_connection_handler(client1, client2, loop):
    send1, receive1 = client1
    send2, receive2 = client2

    await send1(
        {
            "action": "login",
            "data": "dwart",
        }
    )
    data = await receive1()
    assert data['status'] == "success"

    await send2(
        {
            "action": "login",
            "data": "blorgo",
        }
    )
    data = await receive2()
    assert data['status'] == "success"

    await send1({"action":"get_user_list"})
    data = await receive1()

    assert "blorgo" in data['data']
    assert "dwart" in data['data']

    await send1({
        "action": "talk",
        "target": "blorgo",
        "data": "Hello blorgo. <3 dwart"
    })
    data = await receive2()
    assert data['data'] == "Hello blorgo. <3 dwart"
    assert data['sender'] == "dwart"
