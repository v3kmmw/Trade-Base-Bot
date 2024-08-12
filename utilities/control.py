from flask import Flask, send_from_directory, jsonify, request, redirect, session
import discord
import aioboto3
import aiofiles
import aiosqlite
app = Flask(__name__, static_folder="assets")
bot = discord.AutoShardedClient
from utilities import database
import requests
import httpx
import random
import aiohttp
import boto3
import os
from botocore.exceptions import NoCredentialsError
from flask_cloudflared import run_with_cloudflared
run_with_cloudflared(app, port=25726)
R2_ENDPOINT_URL = 'https://12fb2c45fdc4312604cd414c4ab48eae.r2.cloudflarestorage.com'
R2_BUCKET_NAME = 'database'
R2_ACCESS_KEY = '9ec17584e4d3e4b1dcea257ad2d7e4c4'
R2_SECRET_KEY = 'c7f2d50d444e2ee5327518c5b70b768b183cad04ee8dc40047fbe971e5c587f9'
DISCORD_CLIENT_ID = '1264696284795637770'
DISCORD_CLIENT_SECRET = 'MDF7kNdn8yAyx8slZazhpt6X_0P2ZXsD'
if os.cpu_count() == 24:
    DISCORD_REDIRECT_URI = 'https://20sg8n61-25726.use.devtunnels.ms/login'
else:
    DISCORD_REDIRECT_URI = 'https://control.jbtradebase.xyz/login'
DISCORD_AUTHORIZATION_BASE_URL = 'https://discord.com/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'
DISCORD_USER_URL = 'https://discord.com/api/v10/users/@me'
async def upload_to_r2(file_content, object_name):
    s3_client = boto3.client('s3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )
    try:
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=object_name,
            Body=file_content
        )
        file_url = f'https://database.jbtradebase.xyz/{object_name}'
        return 200, file_url
    except NoCredentialsError:
        return 500, "Credentials not available"
    except Exception as e:
        return 500, str(e)
        
@app.route('/loginredirect')
async def redirectlogin():
    if os.cpu_count() == 24:
        return redirect("https://discord.com/oauth2/authorize?client_id=1264696284795637770&response_type=code&redirect_uri=https%3A%2F%2F20sg8n61-25726.use.devtunnels.ms%2Flogin&scope=guilds+identify+connections")
    else:
        return redirect("https://discord.com/oauth2/authorize?client_id=1264696284795637770&response_type=code&redirect_uri=https%3A%2F%2Fcontrol.jbtradebase.xyz%2Flogin&scope=guilds+identify+connections")

@app.route('/auth')
async def auth():
    code = request.args.get('code')
    if not code:
        return "No code provided", 400

    async with aiohttp.ClientSession() as session:
        try:
            # Exchange the authorization code for an access token
            token_response = await session.post(DISCORD_TOKEN_URL, data={
                'client_id': DISCORD_CLIENT_ID,
                'client_secret': DISCORD_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': DISCORD_REDIRECT_URI,
                'scope': 'identify'
            }, headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            })

            # Log the response status and text for debugging
            response_text = await token_response.text()
            print(f"Token response status: {token_response.status}")
            print(f"Token response text: {response_text}")

            if token_response.status != 200:
                return "Failed to get access token", 400

            token_data = await token_response.json()
            access_token = token_data.get('access_token')
            if not access_token:
                return "No access token provided", 400

            # Fetch user info using the access token
            user_response = await session.get(DISCORD_USER_URL, headers={
                'Authorization': f'Bearer {access_token}'
            })

            if user_response.status != 200:
                return "Failed to fetch user info", 400

            user_info = await user_response.json()
            avatar = user_info.get('avatar')
            if avatar:
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_info.get('id')}/{avatar}.png"
                user_info['avatar'] = avatar_url
            return jsonify(user_info)
        
        except Exception as e:
            return f"An error occurred: {e}", 500

@app.route('/uploadr2', methods=['POST'])
async def upload():
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400
    
    files = request.files.getlist('files')
    for file in files:
        content = file.read()
        print(f"Uploading {file.filename} to R2...")
        status_code, link = await upload_to_r2(content, file.filename)
        print(status_code, link)
        return jsonify(link)
    
@app.route('/setpreferences')
async def updatepreferences():
    print(request.args)
    return jsonify(request.args), 200


@app.route('/dailymessages')
async def dailymessages():
    messages = await database.get_daily_messages(bot.db)
    return jsonify(messages), 200

@app.route('/dailymembers')
async def dailymembers():
    messages = await database.get_daily_members(bot.db)
    return jsonify(messages), 200

@app.route('/update_user', methods=['GET'])
async def update_user():
    user_id = request.args.get('user_id').strip('"')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    kwargs = {key: value for key, value in request.args.items() if key != 'user_id'}
    
    if not kwargs:
        return jsonify({"error": "No fields to update"}), 400

    success = await database.update_user(bot.db, user_id, **kwargs)
    if success:
        return jsonify({"message": "User updated successfully"}), 200
    else:
        return jsonify({"error": "Failed to update user"}), 500



@app.route('/fetch_commands')
async def commands_route():
    commands_list = [{'name': cmd.name, 'description': cmd.help} for cmd in bot.commands]
    return jsonify(commands_list), 200
        
@app.route('/fetch_bot')
async def fetch_bot():
    username = bot.user.name
    return jsonify(username), 200

@app.route('/fetch_preferences')
async def fetch_preferences():
    user_id = request.args.get('user_id').strip('"')

    user = bot.get_user(int(user_id))
    if not user:
        return jsonify({"error": "User not found (Discord)"}), 404
    user_data = await database.get_user(bot.db, user)
    print(user_data)
    if not user_data:
        return jsonify({"error": "User not found (Database)"}), 404
    else:
        return jsonify(user_data), 200

@app.route('/fetch_membercount')
async def fetch_membercount():
    guild = bot.get_guild(1216546896491843664)
    member_count = len(guild.members)
    return jsonify(member_count), 200


@app.route('/topmessagers')
async def topmessagers():
    leaderboard = await database.get_top_messagers(bot.db)
    for entry in leaderboard:
        entry['roblox_username'] = bot.get_user(entry['id']).name
    return jsonify(leaderboard), 200


@app.route('/')
async def index():
    return send_from_directory('dashboard', 'dashboard.html')

@app.route('/icons')
async def icons():
    return send_from_directory('dashboard', 'icons.html')

@app.route('/login')
async def login():
    return send_from_directory('dashboard', 'login.html')

@app.route('/user')
async def user():
    return send_from_directory('dashboard', 'user.html')

@app.route('/economy')
async def economy():
    return send_from_directory('dashboard', 'economy.html')

@app.route('/giveaways')
async def giveaways():
    return send_from_directory('dashboard', 'giveaways.html')

@app.route('/commands')
async def commands():
    return send_from_directory('dashboard', 'commands.html')

@app.route('/restart')
async def restart():
    return "Server Restarted."

@app.route('/<path:filename>')
async def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

def start():
    app.run(tunnel_id="e01d44e5-26e6-416f-a092-8d571034d969")
