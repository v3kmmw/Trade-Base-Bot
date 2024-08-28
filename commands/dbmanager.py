import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class DBManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(with_app_command=False)
    @commands.is_owner()
    async def db(self, ctx):
        """
        Command to modify the database from the bot.

        **DO NOT USE THESE IF YOU DON'T KNOW WHAT THEY DO**

        This command allows administrators to make direct modifications to the database. 
        Please use it with caution as improper usage can cause issues with the bot's operation.
        """
        usage_embed = discord.Embed(
            description="Click the button below to access the database manager.",
            color=ctx.author.color,
        )
        usage_embed.set_author(name=f"Database Manager | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Manage Database", style=discord.ButtonStyle.link, url="https://control.jbtradebase.xyz/dbmanager"))
        await ctx.send(embed=usage_embed, view=view)
        

async def setup(bot):
    await bot.add_cog(DBManager(bot))