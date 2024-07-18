import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class Sync(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="Sync the bot")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        embed = discord.Embed(
            title="Commands Syned!",
            description=f"**Synced in:**```{int(self.bot.latency * 1000)}ms```",
            color=discord.Color.dark_embed(),
        )
        embed.set_footer(text="You may have to reload!", icon_url='https://images-ext-1.discordapp.net/external/rdU89nT2Hzp3k4H9r7muDFY2dy_9f9sYAt9zdZhwrZg/https/message.style/cdn/images/52d3a3e1279e5f9372d8c1ebd2f159f37e20232a6c61580254b6ce8b10aaba20.png')

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Sync(bot))