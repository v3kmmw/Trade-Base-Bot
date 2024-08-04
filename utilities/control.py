from flask import Flask, send_from_directory, jsonify
import discord

app = Flask(__name__, static_folder='static')
bot = discord.AutoShardedClient

@app.route('/fetch_bot')
async def fetch_bot():
    username = bot.user.name
    return jsonify(username), 200

@app.route('/fetch_membercount')
async def fetch_membercount():
    guild = bot.get_guild(1216546896491843664)
    member_count = len(guild.members)
    return jsonify(member_count), 200

@app.route('/')
async def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
async def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

def start():
    app.run(host='0.0.0.0', port=25726)
