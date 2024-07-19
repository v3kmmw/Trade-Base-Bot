import discord
from discord.ext import commands
from utilities import database
from discord.ui import View, Button
import shortuuid


class RewardsModal(discord.ui.Modal, title="Proof Codes"):
    def __init__(self):
        super().__init__()
        self.inviteamount = discord.ui.TextInput(label="Please Enter the proof codes.", placeholder="CODE HERE", required=True, min_length=12)
        self.add_item(self.inviteamount)


    async def on_submit(self, interaction: discord.Interaction):
        user_invites = "1"
        await interaction.response.send_message(f"You have {self.inviteamount.value} invites")
        

class ProofView(View):
    def __init__(self, author):
        super().__init__()
        self.author = author

    @discord.ui.button(label="Enter Proof Code(s)", style=discord.ButtonStyle.green, disabled=False, row=1)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("This isnt your report!", ephemeral=True)

        await interaction.response.send_modal(RewardsModal())





class Scammer(commands.Cog):
    """Command to report, search, or delete scammers."""
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(description="Report or manage scammers.")
    async def scammer(self, ctx: commands.Context, action: str = None, scammer: str = None):
        # Handle the base command with different actions
        if action is None:
            await ctx.send("Please specify an action. Use `scammer help` for more information.")
        elif action.lower() == "help":
            await self.send_help(ctx)
        elif action.lower() == "report":
            await self.report_scammer(ctx, scammer)
        elif action.lower() == "search":
            await self.search_scammer(ctx, scammer)
        elif action.lower() == "delete":
            await self.delete_scammer(ctx, scammer)
        else:
            await ctx.send("Unknown action. Use `scammer help` for a list of valid actions.")

    async def send_help(self, ctx: commands.Context):
        usage_embed = discord.Embed(
            title="Scammer Command Usage",
            description=(
                "``scammer <action> <scammer>``\n\n"
                "**Actions:**\n"
                "`help`: Show this help message\n"
                "`report <scammer>`: Report a scammer\n"
                "`search <scammer>`: Search for a scammer\n"
                "`delete <scammer>`: Delete a scammer report"
            ),
            color=ctx.author.color,
        )
        usage_embed.set_footer(text="<> = Required | [] = Optional")
        usage_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=usage_embed)

    async def report_scammer(self, ctx: commands.Context, scammer: str):
        if scammer is None:
            await ctx.send("Please specify a person to report.")
        else:
            embed = discord.Embed(
                description=f"- -----\nScammer: {scammer}",
                color=ctx.author.color,
            )
            proof_code = shortuuid.ShortUUID().random(length=12)
            view = ProofView(author=ctx.author)
            view.add_item(discord.ui.Button(label="Click Here to Upload",style=discord.ButtonStyle.link,url="https://v3kmmw.github.io/JBTB/upload.html", row=1))
            embed.set_footer(text=f"Please upload your proof on the website the button redirects you to.\nPROOF CODE: {proof_code}")
            embed.set_author(name=f"Scammer Report | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed, view=view)



    async def search_scammer(self, ctx: commands.Context, scammer: str):
        if scammer is None:
            await ctx.send("Please specify a scammer to search for.")
        else:
            await ctx.send(f"Searching for scammer '{scammer}'. This feature is under development.")

    async def delete_scammer(self, ctx: commands.Context, scammer: str):
        if not (ctx.author.guild_permissions.manage_guild or ctx.author.guild_permissions.administrator):
            await ctx.send("You don't have permission to use this command.")
            return
        elif scammer is None:
            await ctx.send("Please specify a scammer to delete.")
        
            

async def setup(bot):
    await bot.add_cog(Scammer(bot))
