import discord
from discord.ext import commands
from discord import app_commands
from utilities import database

class Invites(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="Get your invites")
    async def invites(self, ctx: commands.Context):
        invites = await ctx.guild.invites()
        embed = discord.Embed( color=discord.Color.dark_embed())
        embed.set_author(name=f"Invites | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        bot_user = await database.get_user(self.bot.db, ctx.author)
        total_invites = 0
        total_real_invites = 0
        fake_invites = bot_user.get('fake_invites', 0)
        for invite in invites:
            if ctx.author == invite.inviter:
                total_real_invites += invite.uses
                total_invites += invite.uses

        total_invites += fake_invites
        embed.add_field(name=f"Code Invites:", value=f"<:invite:1263623373112475800> {total_real_invites}", inline=True)
        embed.add_field(name=f"Fake (Added) Invites:", value=f"<:invite:1263623373112475800> {fake_invites}", inline=True)
        embed.set_footer(text=f"Total Invites: {total_invites}", icon_url='https://raw.githubusercontent.com/v3kmmw/JBTB/main/mdi--invite.png')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invites(bot))