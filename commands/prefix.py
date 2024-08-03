import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class Prefix(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="View or set the bot's prefix", aliases=["pfx"])
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        embed = discord.Embed(description="### Prefix\n\n", color=ctx.author.color)
        if prefix and len(prefix) > 3 and ctx.author.guild_permissions.manage_guild: 
            embed.description += "The prefix can't be longer than 3 characters!"
            return await ctx.send(embed=embed)
        if prefix and len(prefix) < 5 and ctx.author.guild_permissions.manage_guild:
            await database.set_prefix(self.bot.db, prefix)
            embed.description += f"The prefix has been set to ``{prefix}``"
            return await ctx.send(embed=embed)
        elif prefix is None or ctx.guild.author.guild_permissions.manage_guild is None:
            prefix = await database.get_prefix(self.bot.db)
            if prefix:
                embed.description += f"The prefix is currently set to ``{prefix}``"
            else:
                embed.description += f"The prefix is currently set to ``=``"
        await ctx.send(embed=embed)
        

async def setup(bot):
    await bot.add_cog(Prefix(bot))