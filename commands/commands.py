import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
from discord.ui import View, Button

class SupportView(View):
    def __init__(self, bot, author, message, origin):
        super().__init__()
        self.author = author
        self.bot = bot
        self.message = message
        self.origin = origin or None
        self.add_buttons()

    def get_color(self, command):
        if self.origin is None:
            return discord.ButtonStyle.gray
        elif self.origin == "commands" and command == "Commands":
            return discord.ButtonStyle.green
        elif self.origin == "moderation" and command == "Moderation":
            return discord.ButtonStyle.green
        elif self.origin == "tickets" and command == "Tickets":
            return discord.ButtonStyle.green
        elif self.origin == "server" and command == "Server Support":
            return discord.ButtonStyle.green
        elif command == "Owner":
            return discord.ButtonStyle.red
        else:
            return discord.ButtonStyle.gray  # Default color if none of the conditions match

    def add_buttons(self):
        commands_button = Button(
            label="Commands",
            style=self.get_color("Commands"),
            row=1,
            emoji='<:list:1264028674592608327>'
        )
        moderation_button = Button(
            label="Moderation",
            style=self.get_color("Moderation"),
            row=1,
            emoji='<:police:1264028673561067592>'
        )
        server_button = Button(
            label="Server Support",
            style=self.get_color("Server Support"),
            row=2,
            emoji='<:computer:1264028672302776452>'
        )
        tickets_button = Button(
            label="Tickets",
            style=self.get_color("Tickets"),
            row=2,
            emoji='<:ticket:1263266801568055419>'
        )
        owner_commands = Button(
            label="Owner Commands",
            style=self.get_color("Owner"),
            row=3,
            emoji='<:tbcrown:1269223158708437154>'
        )
        commands_button.callback = self.commands
        moderation_button.callback = self.moderation
        server_button.callback = self.serversupport
        tickets_button.callback = self.ticket
        owner_commands.callback = self.owner_commands
        self.add_item(commands_button)
        self.add_item(moderation_button)
        self.add_item(server_button)
        self.add_item(tickets_button)
        if self.author.id in self.bot.owner_ids:
            self.add_item(owner_commands)
    async def commands(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description=f"### Commands:\n\n",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

        for command in self.bot.commands:
            # Check if the command has the is_owner check            
            # Add the command to the embed description
            pfx = await database.get_prefix(self.bot.db)
            if command.checks or command.name == "jishaku" or command.name == "automod":
                pass
            else:
                embed.description += f"- ``{pfx}{command.name}``\n"
        await interaction.response.edit_message(embed=embed)

    async def moderation(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        embed = discord.Embed(
            description=f"### Moderator Commands:\n\n",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed)

    async def serversupport(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        # Your server support handling logic here
        await interaction.response.send_message("Server Support button clicked!", ephemeral=True)

    async def ticket(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        embed = discord.Embed(
            description="### Tickets\n\nYou can open a ticket in <#1266799483182780457>"
        )
        embed.set_author(name=f"Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed)

    async def owner_commands(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        embed = discord.Embed(
            description=f"### Owner Commands:\n\n",
            color=interaction.user.color,
        )
        embed.set_author(name=f"Help | {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

        for command in self.bot.commands:
            # Check if the command has the is_owner check            
            # Add the command to the embed description
            pfx = await database.get_prefix(self.bot.db)
            if command.checks or command.name == "jishaku" or command.name == "automod":
                embed.description += f"- ``{pfx}{command.name}``\n"
        await interaction.response.edit_message(embed=embed)


class BotHelp(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot



    @commands.hybrid_command(description="Get help with moderation")
    async def moderation(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"What do you need assistance with?",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        message = await ctx.send(embed=embed, view=None)
        view = SupportView(author=ctx.author, bot=self.bot, message=message, origin="moderation")
        await message.edit(view=view)

    @commands.hybrid_command(description="Get help with the server")
    async def support(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"What do you need assistance with?",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        message = await ctx.send(embed=embed, view=None)
        view = SupportView(author=ctx.author, bot=self.bot, message=message, origin="server")
        await message.edit(view=view)

    @commands.hybrid_command(description="Get help with tickets")
    async def tickets(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"What do you need assistance with?",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        message = await ctx.send(embed=embed, view=None)
        view = SupportView(author=ctx.author, bot=self.bot, message=message, origin="tickets")
        await message.edit(view=view)

    @commands.hybrid_command(description="Get a list of commands")
    async def commands(self, ctx: commands.Context):
        embed = discord.Embed(
            description=f"What do you need assistance with?",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Help | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        message = await ctx.send(embed=embed, view=None)
        view = SupportView(author=ctx.author, bot=self.bot, message=message, origin="commands")
        await message.edit(view=view)


async def setup(bot):
    await bot.add_cog(BotHelp(bot))