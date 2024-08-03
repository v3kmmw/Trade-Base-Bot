import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from utilities import database  # Assuming your database functions are in this module

class InviteManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Add or remove invites")
    @commands.is_owner()
    async def manageinvites(self, ctx: commands.Context, action: str = None, amount: int = None, user: discord.User = None):
        """
        Command to add or remove invites.
        Usage:
        - `invites add <amount>`: Adds the specified amount of invites to the command issuer.
        - `invites remove <amount>`: Removes the specified amount of invites from the command issuer.
        - `invites add <user> <amount>`: Adds the specified amount of invites to the mentioned user.
        - `invites remove <user> <amount>`: Removes the specified amount of invites from the mentioned user.
        """
        if action is None:
            usage_embed = discord.Embed(
                title="",
                description=(
                    "``manageinvites <add> <<user>> <amount>``"
                ),
                color= ctx.author.color,
            )
            usage_embed.set_footer(text="<<>> = Optional | <> = Required")
            usage_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.send(embed=usage_embed)
            return

        if action.lower() not in ["add", "remove"]:
            await ctx.send("Invalid action. Please use 'add' or 'remove'.")
            return

        if amount is None or amount <= 0:
            await ctx.send("Please specify a positive integer amount.")
            return

        # Determine the target user
        target_user = user if user else ctx.author
        bot_user = await database.get_user(self.bot.db, ctx.author)
        fake_invites = bot_user.get('fake_invites', 0)
        if action.lower() == "add":
            fake_invites += amount
        elif action.lower() == "remove":
            fake_invites -= amount

        await database.update_user(self.bot.db, ctx.author.id, fake_invites=fake_invites)
        # Create a message based on the action
        if action.lower() == "add":
            action_text = "added"
        else:
            action_text = "removed"

        embed = discord.Embed(
            title="Invite Update",
            description=f"Successfully {action_text} {amount} invites for {target_user.display_name}.",
            color=discord.Color.green(),
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InviteManagement(bot))
