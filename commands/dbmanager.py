import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class DBManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_group(with_app_command=False)
    @commands.is_owner()
    async def db(self, ctx):
        """
        Command to modify the database from the bot.

        **DO NOT USE THESE IF YOU DON'T KNOW WHAT THEY DO**

        This command allows administrators to make direct modifications to the database. 
        Please use it with caution as improper usage can cause issues with the bot's operation.
        """


async def setup(bot):
    await bot.add_cog(DBManager(bot))