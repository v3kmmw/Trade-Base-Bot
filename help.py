from discord.ext import commands
import discord

class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"{cog.qualified_name} Commands", description=cog.description)
        command_list = '\n'.join([command.name for command in cog.get_commands()])
        embed.add_field(name="Commands", value=command_list or "No commands", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"{group.help}")
        command_list = '\n'.join([f"- **{command.name.capitalize()}**" for command in group.commands])
        embed.add_field(name="Subcommands", value=command_list or "No subcommands", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(description=command.help)
        channel = self.get_destination()
        await channel.send(embed=embed)
