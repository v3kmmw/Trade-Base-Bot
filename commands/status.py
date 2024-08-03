import discord
from discord.ext import commands

class Status(commands.Cog):
    """Cog for setting the bot's status"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(description="Set the bot's status")
    @commands.is_owner()
    async def status(self, ctx: commands.Context, activity_type: str = None, *, status: str = None):
        if not activity_type or not status:
            valid_activity_types = ['playing', 'streaming', 'listening', 'watching']
            await ctx.send(f"Usage: `status <activity_type> <status_message> [silent]`\nValid activity types: {', '.join(valid_activity_types)}")
            return
        
        # Check for silent flag
        silent = False
        if status.endswith("silent"):
            status = status[:-7].strip()  # Remove 'silent' from the end
            silent = True
            await ctx.message.delete()
        
        activity = None
        
        if activity_type.lower() == 'playing':
            activity = discord.Game(name=status)
        elif activity_type.lower() == 'streaming':
            activity = discord.Streaming(name=status, url="https://www.twitch.tv/joe_bartolozzi")  # Change the URL to your streaming channel
        elif activity_type.lower() == 'listening':
            activity = discord.Activity(type=discord.ActivityType.listening, name=status)
        elif activity_type.lower() == 'watching':
            activity = discord.Activity(type=discord.ActivityType.watching, name=status)
        else:
            await ctx.send(f"Invalid activity type. Valid activity types: ``{', '.join(valid_activity_types)}``")
            return
        
        await self.bot.change_presence(activity=activity)
        
        embed = discord.Embed(
            title="Status Set",
            description=f"**Activity Type:** {activity_type.capitalize()}\n**Status:** {status}",
            color=discord.Color.dark_embed()
        )
        if silent == False:
           await ctx.send(embed=embed)
        elif silent == True:
            print(f"Status set to {activity_type.capitalize()}: {status}")

async def setup(bot):
    await bot.add_cog(Status(bot))
