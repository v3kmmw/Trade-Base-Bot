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
        usage_embed = discord.Embed(
            title="DB Command Usage",
            description=(
            ),
            color=ctx.author.color,
        )
        usage_embed.set_footer(text="<> = Required | [] = Optional")
        usage_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=usage_embed)

    @db.command()
    async def query(self, ctx, query):
        """
        Execute a raw SQL query on the bot's database.
        This command can be useful for debugging or performing maintenance tasks.
        **WARNING: This command is destructive and should only be used when necessary.**
        """
        try:
        # Adjust database.query function if needed
            result = await database.query(ctx.bot.db, query)
            if isinstance(result, str):
                await ctx.send(result)  # Send success message
            else:
                await ctx.send(f"Query executed successfully.\nResults: {result}")
        except Exception as e:
            await ctx.send(f"An error occurred while executing the query: {e}")

        

async def setup(bot):
    await bot.add_cog(DBManager(bot))