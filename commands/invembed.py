import json
import discord
from discord.ext import commands
from discord.ui import View, Button


class RewardsModal(discord.ui.Modal, title="Rewards Claim"):
    def __init__(self):
        super().__init__()
        self.inviteamount = discord.ui.TextInput(label="How many invites do you have?", placeholder="20", required=True, min_length=1)
        self.add_item(self.inviteamount)


    async def on_submit(self, interaction: discord.Interaction):
        user_invites = "1"
        await interaction.response.send_message(f"You have {self.inviteamount.value} invites")
        





class InviteRewardsView(View):
    def __init__(self):
        super().__init__()



    @discord.ui.button(label="Claim Rewards", style=discord.ButtonStyle.green, disabled=False, row=1)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RewardsModal())



    @discord.ui.button(label="Dont know how to make a custom invite?", style=discord.ButtonStyle.gray, disabled=True, row=1)
    async def disabled_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("you werent supposed to click this!!")




class SendInviteEmbed(commands.Cog):
    """Send the invite rewards embed"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(description="Send the invite rewards embed")
    async def invembed(self, ctx: commands.Context):
        with open('./embeds/invites.json', 'r') as file:
            data = json.load(file)
            
            # Extracting the embed data
            embed_data = data['embeds'][0]
            embed = discord.Embed.from_dict(embed_data)

            # Extracting the components data
            view = InviteRewardsView()
            view.add_item(discord.ui.Button(label="Click Here",style=discord.ButtonStyle.link,url="https://v3kmmw.github.io/JBTB/custominvite.html", row=1))
            
            await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SendInviteEmbed(bot))
