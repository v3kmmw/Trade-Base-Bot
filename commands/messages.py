import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
from typing import Optional

class Messages(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_group(aliases=["m"])
    async def messages(self, ctx, user: Optional[discord.Member] = None):
        if user is None:
            user = ctx.author
        messages = await database.get_messages(self.bot.db, user.id)
        embed = discord.Embed(
            description=f"```{messages}```",
            color=ctx.author.color
        )
        embed.set_author(name=f"Messages | {user.display_name}", icon_url = user.avatar.url)
        await ctx.send(embed=embed)

    @messages.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        leaderboard = await database.get_top_messagers(self.bot.db)
    
        if leaderboard is None:
            await ctx.send("Failed to retrieve the leaderboard.")
            return
    
        embed = discord.Embed(
            description="",
            color=ctx.author.color
        )

    
        for idx, user in enumerate(leaderboard, start=1):
            embed.description += f"<@{user['id']}> ``| Messages: {user['messages']}``\n"

        embed.description += ""
        embed.set_author(name=f"Leaderboard | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Messages(bot))