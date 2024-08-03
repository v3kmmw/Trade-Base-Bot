from flask import Flask, jsonify
import time

app = Flask(__name__)
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
    app.run(host='0.0.0.0', port=25571)
