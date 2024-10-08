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
from utilities import heartbeat
from discord.ext import tasks
from utilities import automod
import aiomysql
import json
import aiofiles
import datetime
current_timestamp = time.time()
current_time = time.localtime(current_timestamp)

script_started_at_str = time.strftime("%H:%M:%S", current_time)
def install_requirements():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])


bot = Bot()

class ProofView(View):
    def __init__(self):
        super().__init__()

async def on_error(ctx, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.NotOwner):
        return await ctx.send(f"This is an owner only command!", delete_after=5)
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(color=ctx.author.color)
        embed.set_author(name="Cooldown", icon_url=ctx.author.avatar.url)
        remaining_time = round(error.retry_after)
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=remaining_time)
        end_timestamp = int(end_time.timestamp())
        embed.description = f"Try again <t:{end_timestamp}:R>."
        return await ctx.send(embed=embed, delete_after=remaining_time)
    embed = discord.Embed(
        description="There was an error running this command",
        color=ctx.author.color,
    )
    embed.set_footer(text="This error has been logged.")
    embed.set_author(name=f"Error | {ctx.author.display_name}")
    await ctx.send(embed=embed, delete_after=2)
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
    if message.content == f"{bot.user.mention}":
        prefix = await database.get_prefix(bot.db)
        await message.channel.send(f"Hello {message.author.mention}.\nFor more commands, use {prefix}commands.", delete_after=5)
    await database.add_user(message.author.id, None, None)
    await automod.check_message(message)
    await database.count_message(message)
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    with open("stats.json", "r") as file:
        data = json.load(file)
        data["commands_ran"] += 1
        with open("stats.json", "w") as file:
            json.dump(data, file)



@bot.event
async def on_member_join(member):
    await database.add_user(member.id, None, None)

async def run_bot():
    bot.on_command_error = on_error
    await bot.start()

if __name__ == "__main__":

    # Run the bot in the main thread
    asyncio.run(run_bot())
