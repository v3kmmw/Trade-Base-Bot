import json
import discord
from discord.ext import commands
from discord.ui import View, Button
from typing import Optional
class SendInviteEmbed(commands.Cog):
    """Send the invite rewards embed"""
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def embed(self, ctx: commands.Context):
        usage_embed = discord.Embed(
            title="Embed Command Usage",
            description=(
                "``embed <action> <embed_name>``\n\n"
                "**Actions:**\n"
                "`send <embed_name> [channel]`: Send the embed in the channel specified\n"
                "`save <message_link> <embed_name>`: Save an embed\n"
                "`list`: List all embeds\n"
                "`delete <embed_name>`: Delete an embed from the database"
            ),
            color=ctx.author.color,
        )
        usage_embed.set_footer(text="<> = Required | [] = Optional")
        usage_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=usage_embed)


    @embed.command()
    async def send(self, ctx: commands.Context, embed: Optional[str] = None):
        if embed is None:
            print("G")
            return

    @embed.command()
    async def save(self, ctx: commands.Context):
        print("")


    














async def setup(bot):
    await bot.add_cog(SendInviteEmbed(bot))
