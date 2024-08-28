import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
import json
class Prefix(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="View or set the bot's prefix", aliases=["pfx"])
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        """
        Command to set or view the bots prefix.
        """
        await ctx.defer()
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

    @commands.hybrid_command(description="View the bot stats", aliases=["statistics"])
    async def stats(self, ctx: commands.Context, prefix: str = None):
        with open("stats.json", "r") as f:
            stats = json.load(f)
        if not stats:
            stats['commands_ran'] = 1
        commands_ran = stats.get("commands_ran", 0)
        membercount = await database.get_total_members(self.bot.db)
        embed = discord.Embed(
            description=f"- **Total commands ran:** ```{commands_ran}```\n- **Total members (DB):** ```{membercount}```\n- **Total members (Guild):** ```{ctx.guild.member_count}```",
            color=ctx.author.color
        )
        embed.set_author(name=f"Stats | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Prefix(bot))