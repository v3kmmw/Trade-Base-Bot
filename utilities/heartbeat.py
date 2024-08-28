from flask import Flask, jsonify, Response, request
import time
from flask_cloudflared import run_with_cloudflared
import discord
import config
import asyncio
import logging
import os
import sys
from io import StringIO
import json, os, signal
import aiohttp
app = Flask(__name__)
bot = None

run_with_cloudflared(app, port=25571)

log_stream = StringIO()
logging.basicConfig(stream=log_stream, level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(message)s')

@app.route('/')
def status():
    if bot.is_ready():
        latency = bot.latency * 1000
        username = bot.user.name
        return jsonify({"username": username, "status": "online", "latency": latency}), 200
    else:
        return jsonify({"status": "offline"}), 503

@app.route('/logs', methods=['GET'])
def get_logs():
    log_stream.seek(0)  # Move the cursor to the beginning
    logs = log_stream.read()
    return Response(logs, mimetype='text/plain')

# test token
# 6813d506-25b8-461e-89ef-2975c08b861a
# main token
# a3881ccb-a8de-4319-9145-43382c3b10c4

def start():
    app.run(tunnel_id="a3881ccb-a8de-4319-9145-43382c3b10c4")
