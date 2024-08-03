from discord.ext import commands
import discord

class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        embed = discord.Embed(description="List of all commands:")
        count = 0
        for cog, commands in mapping.items():
            command_list = '\n'.join([command.name for command in commands][:9])  # Only get the first 9 commands
            if cog:
                embed.add_field(name=cog.qualified_name, value=command_list or "No commands", inline=True)
            else:
                embed.add_field(name="No Category", value=command_list or "No commands", inline=True)
            count += len(commands)
            if count >= 9:
                embed.set_author(name="Bot Commands", icon_url="https://jbtradebase.xyz/favicon.ico")
                channel = self.get_destination()
                await channel.send(embed=embed)
                break

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"{cog.qualified_name} Commands", description=cog.description)
        command_list = '\n'.join([command.name for command in cog.get_commands()])
        embed.add_field(name="Commands", value=command_list or "No commands", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"{group.qualified_name} Commands", description=group.short_doc)
        command_list = '\n'.join([command.name for command in group.commands])
        embed.add_field(name="Subcommands", value=command_list or "No subcommands", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=f"{command.qualified_name}", description=command.help)
        channel = self.get_destination()
        await channel.send(embed=embed)
