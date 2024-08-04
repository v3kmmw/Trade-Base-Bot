import json
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from typing import Optional


class EmbedManagerView(View):
    def __init__(self, ctx, author, displaying):
        super().__init__(timeout=None)
        author = author
        self.displaying = displaying
        self.content = f"-# **Displaying: {displaying}**"
        self.embed = discord.Embed(color=ctx.author.color)
        self.embed.set_author(name=f"Embed Manager | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        self.add_buttons()

    def add_buttons(self):
        previous_button = Button(
            label="",
            style=discord.ButtonStyle.gray,
            row=1,
            emoji='<:leftarrow:1265591889059385345>'
        )
        send_button = Button(
            label="Send",
            style=discord.ButtonStyle.gray,
            row=1,
            emoji='<:send:1265591864023846982>'
        )
        next_button = Button(
            label="",
            style=discord.ButtonStyle.gray,
            row=1,
            emoji='<:rightarrow:1265591909787635742>'
        )
        help_button = Button(
            label="",
            style=discord.ButtonStyle.gray,
            row=1,
            emoji='<:question:1265591751809302621>'
        )
        select_menu = Select(
            options=[
                discord.SelectOption(label="No")
            ],
            placeholder="Administrator Options:",
            row=3,
            disabled=True,
            min_values=1,
            max_values=1
        )
        add_button = Button(
            label="Add",
            style=discord.ButtonStyle.gray,
            row=4,
            emoji='<:add:1265591836278259752>'
        )
        remove_button = Button(
            label="Remove",
            style=discord.ButtonStyle.gray,
            row=4,
            emoji='<:remove:1265591794507190363>'
        )
        help_admin_button = Button(
            label="",
            style=discord.ButtonStyle.gray,
            row=4,
            emoji='<:question:1265591751809302621>'
        )
        previous_button.callback = self.previous
        send_button.callback = self.send
        next_button.callback = self.next
        help_button.callback = self.help
        self.add_item(previous_button)
        self.add_item(send_button)
        self.add_item(next_button)
        self.add_item(help_button)
        self.add_item(select_menu)
        self.add_item(add_button)
        self.add_item(remove_button)
        self.add_item(help_admin_button)


    async def previous(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        
    async def send(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        
    async def next(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        
    async def help(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

class EmbedManager(commands.Cog):
    """Send the invite rewards embed"""
    def __init__(self, bot):
        self.bot = bot


    @commands.group()
    @commands.is_owner()
    async def embed(self, ctx: commands.Context):
        """
        Command to add or remove embeds from the bot.
        """
        usage_embed = discord.Embed(
            title="Embed Command Usage",
            description=(

            ),
            color=ctx.author.color,
        )
        usage_embed.set_footer(text="<> = Required | [] = Optional")
        usage_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=usage_embed)


    @embed.command()
    @commands.is_owner()
    async def manager(self, ctx: commands.Context):
        view = EmbedManagerView(ctx, ctx.author, displaying="None")
        embed = view.embed
        content = view.content
        await ctx.send(content=content, embed=embed, view=view)


    @embed.command()
    @commands.is_owner()
    async def send(self, ctx: commands.Context, embed: Optional[str] = None):
        if embed is None:
            print("G")
            return

    @embed.command()
    @commands.is_owner()
    async def delete(self, ctx: commands.Context):
        print("")


    














async def setup(bot):
    await bot.add_cog(EmbedManager(bot))
