import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class Invites(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="Get your invites")
    async def invites(self, ctx: commands.Context, user: discord.Member = None):
        if user is None:
            user = ctx.author
        invites = await ctx.guild.invites()
        embed = discord.Embed(color=user.color)
        if not user.avatar:
            user_avatar = "https://raw.githubusercontent.com/v3kmmw/JBTB/main/flowbite--discord-solid.png"
        else:
            user_avatar = user.avatar.url

        embed.set_author(name=f"Invites | {user.display_name}", icon_url=user_avatar)

        # Fetch user information from the database
        bot_user = await database.get_user(self.bot.db, user)
        if bot_user is None:
            bot_user = {'fake_invites': 0}

        total_invites = 0
        total_real_invites = 0
        fake_invites = bot_user.get('fake_invites', 0)

        for invite in invites:
            if user == invite.inviter:
                total_real_invites += invite.uses
                total_invites += invite.uses

        total_invites += fake_invites

        embed.add_field(name=f"Code Invites:", value=f"<:invite:1263623373112475800> {total_real_invites}", inline=True)
        embed.add_field(name=f"Fake (Added) Invites:", value=f"<:invite:1263623373112475800> {fake_invites}", inline=True)
        embed.set_footer(text=f"Total Invites: {total_invites}", icon_url='https://raw.githubusercontent.com/v3kmmw/JBTB/main/mdi--invite.png')

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))