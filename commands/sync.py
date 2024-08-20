import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import asyncio
from utilities import database

class ConfirmationView(View):
    def __init__(self, role, ctx):
        super().__init__(timeout=60)  # Timeout after 60 seconds
        self.role = role
        self.ctx = ctx
        self.confirmed = False

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button,):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        
        self.confirmed = True
        await interaction.response.send_message(f"Role {self.role.name} has been deleted.", ephemeral=True)
        await self.role.delete()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return
        
        await interaction.response.send_message("Role deletion cancelled.", ephemeral=True)
        self.stop()

class RoleSelect(Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles
        ]
        super().__init__(placeholder="Select a role to remove...", options=options)

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        guild = interaction.guild
        role = guild.get_role(role_id)
        member = interaction.user

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"Removed role: {role.name}", ephemeral=True)
        else:
            await interaction.response.send_message(f"You do not have the role: {role.name}", ephemeral=True)

class RemoveRoles(View):
    def __init__(self, roles):
        super().__init__()
        self.add_item(RoleSelect(roles))

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Sync the bot | Owner only")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """
        This command is owner only.
        """
        await self.bot.tree.sync()
        embed = discord.Embed(
            title="Commands Synced!",
            description=f"**Synced in:**```{int(self.bot.latency * 1000)}ms```",
            color=ctx.author.color,
        )
        embed.set_footer(text="You may have to reload!", icon_url='https://images-ext-1.discordapp.net/external/rdU89nT2Hzp3k4H9r7muDFY2dy_9f9sYAt9zdZhwrZg/https/message.style/cdn/images/52d3a3e1279e5f9372d8c1ebd2f159f37e20232a6c61580254b6ce8b10aaba20.png')
        await ctx.send(embed=embed)

    @commands.hybrid_group(description="Create a message or unlockable role.")
    @commands.is_owner()
    async def role(self, ctx: commands.Context):
        if not ctx.author.guild_permissions.manage_guild:
            return await ctx.send("Usage: ``role claim``")
        embed = discord.Embed(
            description="Requirement types: ```balance/vouches/messages```\nUsage: ``role create/delete/claim``",
            color=ctx.author.color,
        )
        embed.set_author(name=f"Roles | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(description="Clear the chat | Owner only")
    @commands.is_owner()
    async def clearchat(self, ctx: commands.Context):
        await ctx.send("_\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n_")

    @role.command(description="Add an unlockable role | Owner only")
    @commands.is_owner()
    async def create(self, ctx: commands.Context, name: str = None, color: discord.Color = None, requirement: str = None, requirement_type: str = None):
        if name == "help" or not all([name, requirement, requirement_type]):
            return await ctx.send("Usage: `role create <name> <color> <requirement> <requirement_type>`")
        # Create the role in the database
        role = await database.create_unlockable_role(self.bot, self.bot.db, name, color or discord.Color.default(), requirement, requirement_type)
        if not role:
            return await ctx.send("Failed to create role.")
        await ctx.send(f"Role {role.mention} created successfully!")
    
    @role.command(description="Remove an unlockable role | Owner only")
    @commands.is_owner()
    async def delete(self, ctx: commands.Context, role: discord.Role = None):
        if not role:
            return await ctx.send("Please specify a role to delete.")
        
        # Send confirmation message
        confirmation_view = ConfirmationView(role, ctx)
        message = await ctx.send(f"Are you sure you want to delete the role {role.name}?", view=confirmation_view)
        
        # Wait for the user to interact with the buttons
        await confirmation_view.wait()
        
        # Optionally delete the message after the interaction
        await message.delete()
    @role.command(description="Claim your roles")
    async def claim(self, ctx: commands.Context):
        embed = discord.Embed(
            color=ctx.author.color,
        )
        embed.set_author(name=f"Role Claim | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.description = "Claiming your roles..."
        embed.set_footer(text="‎", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
        message = await ctx.send(embed=embed)

        roles = await database.handle_role_check(self.bot.db, ctx.author, self.bot)
        unlockable_roles = await database.get_unlockable_roles(self.bot.db)
        if not unlockable_roles:
            embed.description = "No unlockable roles found."
            embed.set_footer(icon_url=None)
            if ctx.author.guild_permissions.manage_guild:
                embed.set_footer(text="You can create one by using the `role create` command. [Admin]", icon_url=None)
            await asyncio.sleep(1)
            await message.edit(embed=embed)
            return
       
        if not roles:
            embed.description = "You have no roles to claim."
            embed.set_footer(text="Want to remove a role?", icon_url=None)
            await asyncio.sleep(1)
            await message.edit(embed=embed)
            all_roles = ctx.author.roles
            cleaned_roles = [role for role in all_roles if role.id in [ur['id'] for ur in unlockable_roles]]
            view = RemoveRoles(roles=cleaned_roles)
            await message.edit(view=view)
            return

        embed.description = "Roles claimed!\n\n"
        for index, role in enumerate(roles, start=1):
            unlockable_role = next((ur for ur in unlockable_roles if int(ur['id']) == role.id), None)
            if unlockable_role:
                requirement_txt = f"{unlockable_role['requirement']} {unlockable_role['requirement_type']}"
                embed.description += f"- {role.mention}:\n  - Requirement: {requirement_txt}\n"

        embed.set_footer(text="Want to remove a role?", icon_url=None)
        await asyncio.sleep(1)
        await message.edit(embed=embed)
        all_roles = ctx.author.roles
        cleaned_roles = [role for role in all_roles if role.id in [ur['id'] for ur in unlockable_roles]]
        view = RemoveRoles(roles=cleaned_roles)
        await message.edit(view=view)

async def setup(bot):
    await bot.add_cog(Sync(bot))
