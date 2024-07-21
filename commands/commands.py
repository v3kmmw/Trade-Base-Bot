import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
from discord.ui import View, Button

class SupportView(View):
    def __init__(self, author):
        super().__init__()
        self.author = author



    



    @discord.ui.button(label="Commands", style=discord.ButtonStyle.gray, disabled=False, row=1, emoji='<:list:1264028674592608327>')
    async def commands(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This isnt your command!", ephemeral=True)

        embed = discord.Embed(
            description=f"This isnt done yet",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Commands | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.gray, disabled=False, row=1, emoji='<:police:1264028673561067592>')
    async def moderation(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This isnt your command!", ephemeral=True)
        embed = discord.Embed(
            description=f"This isnt done yet",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Moderation Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Server Support", style=discord.ButtonStyle.gray, disabled=False, row=2, emoji='<:computer:1264028672302776452>')
    async def server(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This isnt your command!", ephemeral=True)
        embed = discord.Embed(
            description=f"This isnt done yet",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Server Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Tickets", style=discord.ButtonStyle.gray, disabled=False, row=2, emoji='<:ticket:1263266801568055419>')
    async def tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This isnt your command!", ephemeral=True)
        embed = discord.Embed(
            description=f"This isnt done yet",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Tickets Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)



class Help(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(description="Shows the latency of the bot")
    async def help(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"What do you need assistance with?",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        view = SupportView(author=ctx.author)

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(description="Get a list of commands")
    async def commands(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"What do you need assistance with?",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        view = SupportView(author=ctx.author)

        await ctx.send(embed=embed, view=view)
async def setup(bot):
    await bot.add_cog(Help(bot))