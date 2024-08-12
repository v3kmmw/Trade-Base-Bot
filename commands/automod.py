import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
from utilities import automod
import random

class Automod(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot



    @commands.hybrid_group(with_app_command=False, aliases=['automode'])
    async def automod(self, ctx: commands.Context):
        embed = discord.Embed(
            description="Automod is handled by OpenAI's moderation api by default.\n To switch this to just the filtered words, use the command: ```automod set filter```\n To switch back to OpenAI, use ```automod set ai```"
        )
        embed.set_author(name=f"Automod Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        """Automod commands"""
        if ctx.author.guild_permissions.manage_guild == False:
            return await ctx.send("You cant run this command.", ephemeral=True)
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=embed)

    @automod.command(with_app_command=False)
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            description="Automod is handled by OpenAI's moderation api by default.\n To switch this to just the filtered words, use the command: ```automod set filter```\n To switch back to OpenAI: ```automod set ai```\n To open the sensitivity configuration menu, use ```automod sensitivity```\n To disable or enable: ```automod enable/disable```"
        )
        embed.set_footer(text="AI automod will automatically filter the manually filtered words aswell.")
        if ctx.author.guild_permissions.manage_guild == False:
            return await ctx.send("You cant run this command.", ephemeral=True)
        embed.set_author(name=f"Automod Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)


    @automod.command(with_app_command=False)
    async def set(self, ctx: commands.Context, type: str):
        filters = ['AI', 'FILTER']
        if ctx.author.guild_permissions.manage_guild and type.upper() in filters:
            await automod.set_automod_type(self.bot.db, type.upper())
            await ctx.send(f"Automod type set to ``{type}``.")
        elif type.upper() not in filters:
            return await ctx.send("Invalid type. Please choose between ``ai`` or ``filter``.")

    @automod.command(with_app_command=False)
    async def test(self, ctx: commands.Context):
        """Disable a specific automod setting"""
        random_number = ''.join(str(random.randint(0, 9)) for _ in range(4))
        await automod.add_automod_log(self.bot.db, f"TEST-{random_number}", ctx.author.id, "TestFlag", "Testing", "The message content would be here", "Admin invoked test command.")
        embed = discord.Embed(
            description="``Automod Log Sent``"
        )
        embed.set_author(name=f"Automod Test | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @automod.command(with_app_command=False)
    async def toggle(self, ctx: commands.Context):
        """Disable a specific automod setting"""
        status = await automod.toggle_automod()
        embed = discord.Embed(
            description=f"``Automod {status}``"
        )
        embed.set_author(name=f"Automod | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Automod(bot))