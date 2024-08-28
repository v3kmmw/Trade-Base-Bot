import discord
from discord.ext import commands
from discord import app_commands
from utilities import database
from typing import Optional
from discord.ui import Select, Button, View, button, Modal, TextInput

class GoToPage(Modal):
    def __init__(self, pagination_view):
        super().__init__(title="Go To Page")
        self.pagination_view = pagination_view
        self.page_number = TextInput(label="Page Number", placeholder="Enter a page number")
        self.add_item(self.page_number)

    async def on_submit(self, interaction: discord.Interaction):
        # Validate page number input
        try:
            page_number = int(self.page_number.value) - 1  # Convert to 0-based index
            max_page = (len(self.pagination_view.leaderboard) - 1) // self.pagination_view.showing
            if 0 <= page_number <= max_page:
                self.pagination_view.current_page = page_number
                await self.pagination_view.update_embed()
                await interaction.response.defer()
            else:
                await interaction.response.send_message(f"Invalid page number. Please enter a number between 1 and {max_page + 1}.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)

class Pagination(View):
    def __init__(self, message, leaderboard, showing: int = 10):
        super().__init__(timeout=None)
        self.message = message
        self.leaderboard = leaderboard
        self.showing = showing
        self.current_page = 0

        # Update the embed with the initial page
    async def async_init(self):
        await self.update_embed()

    async def update_embed(self):
        # Create the embed for the current page
        embed = discord.Embed(
            description="",
            color=self.message.author.color
        )
        start = self.current_page * self.showing
        end = start + self.showing
        for idx, user in enumerate(self.leaderboard[start:end], start=start + 1):
            embed.description += f"``{idx}.``  <@{user['id']}> ``| Messages: {user['messages']}``\n"
        footer_start = start + 1
        footer_end = min(end, len(self.leaderboard))
        embed.set_footer(text=f"Showing {footer_start}-{footer_end} of {len(self.leaderboard)}")
        embed.set_author(name=f"Leaderboard | {self.message.author.display_name}", icon_url=self.message.author.avatar.url)
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:left:1276406729659387944>")
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = (len(self.leaderboard) - 1) // self.showing
        await self.update_embed()
        await interaction.response.defer()

    @discord.ui.button(label="Go to Page", style=discord.ButtonStyle.secondary)
    async def go_to_page(self, interaction: discord.Interaction, button: Button):
        modal = GoToPage(pagination_view=self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="", style=discord.ButtonStyle.secondary, emoji="<:right:1276406730867085385>")
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if (self.current_page + 1) * self.showing < len(self.leaderboard):
            self.current_page += 1
        else:
            self.current_page = 0
        
        await self.update_embed()
        await interaction.response.defer()

class Messages(commands.Cog):
    """Basic ping command"""
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_group(aliases=["m"])
    async def messages(self, ctx, user: Optional[discord.Member] = None):
        if user is None:
            user = ctx.author
        messages = await database.get_messages(self.bot.db, user.id)
        embed = discord.Embed(
            description=f"```{messages}```",
            color=ctx.author.color
        )
        embed.set_author(name=f"Messages | {user.display_name}", icon_url = user.avatar.url)
        await ctx.send(embed=embed)
        

    @messages.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        leaderboard = await database.get_top_messagers(self.bot.db)
    
        if leaderboard is None:
            await ctx.send("Failed to retrieve the leaderboard.")
            return
    
        embed = discord.Embed(
            description="",
            color=ctx.author.color
        )

        showing = 10

        embed.set_footer(text=f"Showing: {showing}/{len(leaderboard)}")
        for idx, user in enumerate(leaderboard[:10], start=1):
            embed.description += f"``{idx}.``  <@{user['id']}> ``| Messages: {user['messages']}``\n"

        embed.description += ""
        embed.set_author(name=f"Leaderboard | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        view = Pagination(message=await ctx.send(embed=embed), leaderboard=leaderboard)
        await view.async_init()
        await view.update_embed()


async def setup(bot):
    await bot.add_cog(Messages(bot))