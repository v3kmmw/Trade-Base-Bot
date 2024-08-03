import discord
from discord.ext import commands
from discord.ext import tasks
import aiosqlite
from utilities import database
class InviteSync(commands.Cog):

    """Basic Sync commands"""

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=1)
    async def sync_invites(self):
       guild = self.bot.get_guild(1260356563965841491)
       invites = await guild.invites()
       db = await aiosqlite.connect("./data/database.db")
       await database.sync_invites(db, invites)
       await db.close()
       print(f"Current invites: {len(invites)}")

    @commands.command()
    @commands.is_owner()
    async def syncinvites(self, ctx: commands.Context):
        await ctx.send("Syncing invites...")
        self.sync_invites.start()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = self.bot.get_guild(1260356563965841491)
        invites = await guild.invites()

# Define the setup function to add the cog
async def setup(bot):
    await bot.add_cog(InviteSync(bot))
