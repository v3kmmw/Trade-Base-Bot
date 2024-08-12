from flask import Flask, jsonify
import time
from flask_cloudflared import run_with_cloudflared

app = Flask(__name__)
run_with_cloudflared(app, port=25571)
bot_status = {
    "status": "Initializing...",
    "latency": None,
    "start_time": time.time()
}

@app.route('/')
def status():
    uptime = time.time() - bot_status["start_time"]
    response = {
        "status": bot_status["status"],
        "latency": bot_status["latency"],
        "uptime": uptime
    }
    return jsonify(response), 200
def start():
    app.run(tunnel_id="434329d4-3c1f-483f-b2f1-12978aa336f3")
