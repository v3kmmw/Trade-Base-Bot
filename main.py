import subprocess
import sys

def install_requirements():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])


install_requirements()

import discord
import asyncio
from bot import Bot
import threading
from utilities import database
from discord.ext import commands
from utilities import api
import aiosqlite
from discord.ext import tasks
from discord.ui import View, Button
import config
bot: Bot = Bot()



class ProofView(View):
    def __init__(self):
        super().__init__()

async def on_error(ctx, error: commands.CommandError):
    embed = discord.Embed(
        title=f"Error",
        color=discord.Color.dark_embed(),
    )
    embed.add_field(name="Reason", value=error)
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
    # Print each message
    if message.author.bot:
        return
    db = await aiosqlite.connect("./data/database.db")
    await database.add_user(db, message.author.id)

    # Process commands if the message is not from the bot itself
    if not message.author.bot:
        await bot.process_commands(message)


async def run_bot() -> None:
    bot.on_command_error = on_error
    await bot.start()
    

if __name__ == "__main__":
    flask_thread = threading.Thread(target=api.start)
    flask_thread.start()
    asyncio.run(run_bot())