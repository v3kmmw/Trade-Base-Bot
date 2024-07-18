import discord
import asyncio
from bot import Bot
from discord.ext import commands

bot: Bot = Bot()

async def on_error(ctx, error: commands.CommandError):
    embed = discord.Embed(
        title=f"Error",
        color=discord.Color.dark_embed(),
    )
    embed.add_field(name="Reason", value=error)
    await ctx.send(embed=embed)

async def run_bot() -> None:
    bot.on_command_error = on_error
    await bot.start()
    

if __name__ == "__main__":
    asyncio.run(run_bot())