import discord
import asyncio
from bot import Bot
import threading
from utilities import database
from discord.ext import commands
from utilities import api
import aiosqlite
bot: Bot = Bot()

async def on_error(ctx, error: commands.CommandError):
    embed = discord.Embed(
        title=f"Error",
        color=discord.Color.dark_embed(),
    )
    embed.add_field(name="Reason", value=error)
    await ctx.send(embed=embed)

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