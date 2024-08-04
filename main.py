import subprocess
import sys
import discord
import asyncio
from bot import Bot
from utilities import database
from discord.ext import commands
import aiosqlite
from discord.ui import View, Button
import config
import threading
import time
from utilities.heartbeat import bot_status
from discord.ext import tasks
from utilities import automod
def install_requirements():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

install_requirements()

bot = Bot()

class ProofView(View):
    def __init__(self):
        super().__init__()

async def on_error(ctx, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    embed = discord.Embed(
        description="There was an error running this command",
        color=ctx.author.color,
    )
    embed.set_footer(text="If you are an administrator, check the logs for more information")
    embed.set_author(name=f"Error | {ctx.author.display_name}")
    await ctx.send(embed=embed)
    error_channel = ctx.channel
    user = ctx.author
    log_channel = config.LOG_CHANNEL
    channel = await bot.fetch_channel(log_channel)
    embed = discord.Embed(
        title=f"Error",
        color=discord.Color.dark_embed(),
    )
    embed.add_field(name="Reason", value=error, inline=False)
    embed.add_field(name="Channel", value=f"{error_channel.mention}", inline=False)
    embed.add_field(name="User", value=user.mention, inline=False)
    view = ProofView()
    message_link = ctx.message.jump_url
    view.add_item(discord.ui.Button(label="Jump to error", style=discord.ButtonStyle.link, url=f"{message_link}", row=1))
    await channel.send(embed=embed, view=view)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await database.add_user(message.author.id, None, None)
    await automod.check_message(message)
    await database.count_message(message.author.id)
    await bot.process_commands(message)

async def run_bot():
    bot.on_command_error = on_error
    await bot.start()

def start_api():
    from utilities import api
    api.start()

def start_control_panel():
    from utilities import control
    control.start()

def start_heartbeat():
    from utilities import heartbeat
    heartbeat.start()

if __name__ == "__main__":
    # Start the API server in a separate thread
    api_thread = threading.Thread(target=start_api)
    api_thread.start()

    # Start the heartbeat server in another separate thread
    heartbeat_thread = threading.Thread(target=start_heartbeat)
    heartbeat_thread.start()

    # Start the control panel in a separate thread
    control_panel_thread = threading.Thread(target=start_control_panel)
    control_panel_thread.start()

    # Run the bot in the main thread
    asyncio.run(run_bot())
