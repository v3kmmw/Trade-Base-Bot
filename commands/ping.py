import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
from discord.ui import View, Button

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
        view = View()
        view.add_item(discord.ui.Button(label="Status Page", style=discord.ButtonStyle.link, url="https://status.jbtradebase.xyz", row=1))
        embed.set_author(name=f"Ping | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(description="Throw a random error")
    @commands.is_owner()
    async def error(self, ctx: commands.Context):
        await ctx.send("Error Thrown")
        raise ValueError("Staff Invoked")


async def setup(bot):
    await bot.add_cog(Ping(bot))