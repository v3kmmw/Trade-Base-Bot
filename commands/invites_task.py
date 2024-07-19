import discord
from discord.ext import commands

class InviteSync(commands.Cog):
    """Basic Sync commands"""

    def __init__(self, bot):
        self.bot = bot
        # Code to run when the cog is initialized
        self.bot.loop.create_task(self.on_cog_load())

    async def on_cog_load(self):
        guild = self.bot.get_guild(1260356563965841491)
        invites = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(member):
       print(member)

# Define the setup function to add the cog
async def setup(bot):
    await bot.add_cog(InviteSync(bot))
