import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class Ping(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="Shows the latency of the bot")
    async def ping(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"```{int(self.bot.latency * 1000)}ms```",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Ping | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Throw a random error")
    @commands.is_owner()
    async def error(self, ctx: commands.Context):
        raise ValueError("An error occurred")
        await ctx.send("Error Thrown")


async def setup(bot):
    await bot.add_cog(Ping(bot))