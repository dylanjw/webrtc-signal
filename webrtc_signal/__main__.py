#!/usr/bin/env python3
import argparse
from aiohttp import web
import aiohttp
import socket
import os

from .lib import setup_ws_connection_handler

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--path')
parser.add_argument('--port')

LOGGED_IN = dict()

ws_connection_handler = setup_ws_connection_handler(LOGGED_IN)

args = parser.parse_args()

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    os.unlink(args.path)
except FileNotFoundError:
    pass
s.bind(args.path)
os.chown(args.path, 33, 33)

app = web.Application()
app.add_routes([web.get('/ws', ws_connection_handler)])


web.run_app(app, sock=s)
