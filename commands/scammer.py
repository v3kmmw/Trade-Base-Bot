import discord
from discord.ext import commands, tasks
from utilities import database
from discord.ui import View, Button
import shortuuid
import asyncio
import config 
import time

class SendReport(View):
    def __init__(self, bot, author, message, code):
        super().__init__()
        self.bot = bot
        self.author = author
        self.message = message
        self.code = code

    @discord.ui.button(label="Send Report", style=discord.ButtonStyle.green, disabled=False, row=1)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button):
        await database.create_report(self.bot.db, self.code)
        log_channel = config.LOG_CHANNEL
        log_channel = await self.bot.fetch_channel(log_channel)
        unix_timestamp = int(time.time())
        embed = discord.Embed(
            description=f"Creation date: <t:{unix_timestamp}>\n\n",
            color=interaction.user.color
        )
        embed.add_field(name="Reporter:", value=interaction.user.mention)
        embed.add_field(name="Code:", value=self.code)
        embed.add_field(name="Message:", value=self.message.jump_url)

        embed.set_author(name=f"Scam Report Created", icon_url=interaction.user.avatar.url)
        await log_channel.send(embed=embed)
        await self.message.edit(view=None)
        await interaction.response.send_message("Report sent!")

class ProofView(View):
    def __init__(self, author, code):
        super().__init__()
        self.author = author
        self.code = code

class ConfirmReport(View):
    def __init__(self, bot, author, message, code):
        super().__init__()
        self.bot = bot
        self.author = author
        self.message = message
        self.code = code

    async def update_embed(self, message, code):
        report = await database.get_report_verification(self.bot.db, code)
        if report is None:
            print("No report found")
            return

        embeds = message.embeds
        if len(embeds) < 2:
            print("Message does not have two embeds")
            return

        code_embed = embeds[0]
        status_embed = embeds[1]
        description = status_embed.description or ""

        new_description_parts = []

        lines_to_update = {
            "Proof Status:": f"Proof Status: ``{report['status']}``",
            "Public:": f"Public: ``{'True' if report['public'] == 1 else 'False'}``",
        }

        description_lines = description.split("\n")

        for line in description_lines:
            for key, new_value in lines_to_update.items():
                if line.startswith(key):
                    new_description_parts.append(new_value)
                    del lines_to_update[key]
                    break
            else:
                new_description_parts.append(line)

        for key, new_value in lines_to_update.items():
            new_description_parts.append(new_value)

        updated_description = "\n".join(new_description_parts)
        status_embed.description = updated_description
        status_embed.set_footer(text="Scammer Report Overview")

        await message.edit(embeds=[code_embed, status_embed], view=SendReport(bot=self.bot, author=self.author, message=message, code=self.code))

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, row=1)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await database.update_pending_proof_public(self.bot.db, self.code, 1)
        await self.update_embed(self.message, self.code)
        await interaction.response.send_message("The report has been made public.", ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, row=1)
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await database.update_pending_proof_public(self.bot.db, self.code, 0)
        await self.update_embed(self.message, self.code)
        await interaction.response.send_message("You chose not to make this report public.", ephemeral=True)

class Scammer(commands.Cog):
    """Command to report, search, or delete scammers."""
    def __init__(self, bot):
        self.bot = bot
        self.updated_reports = set()
        self.check_reports.start()

    async def update_embed(self, message, code):
        report = await database.get_report_verification(self.bot.db, code)
        if report is None:
            print("No report found")
            return

        proof = report.get('proof', [])
        cleaned_proof = [url.strip().strip('[]').strip('"') for url in proof if isinstance(url, str)]

        embeds = message.embeds
        if len(embeds) < 2:
            print("Message does not have two embeds")
            return

        code_embed = embeds[0]
        status_embed = embeds[1]
        embed_description_lines = status_embed.description.split("\n") if status_embed.description else []
        privacy = report['public'] == 1

        embed_description_lines.append(f"Public: ``{privacy}``")

        for i, line in enumerate(embed_description_lines):
            if line.startswith("###Proof:"):
                embed_description_lines[i] = "###Proof:"
                break
        else:
            embed_description_lines.append("### Proof")

        for index, proof_url in enumerate(cleaned_proof, start=1):
            embed_description_lines.append(f"[Proof {index}]({proof_url})")

        updated_description = "\n".join(embed_description_lines)
        status_embed.description = updated_description
        status_embed.set_footer(text=f"Would you like this report to be public?")
        await message.edit(embeds=[code_embed, status_embed], view=ConfirmReport(bot=self.bot, author=message.author, message=message, code=report['code']))

    @tasks.loop(seconds=1)
    async def check_reports(self):
        reports_to_check = list(self.updated_reports)
        for code in reports_to_check:
            report = await database.get_report_verification(self.bot.db, code)
            if report is None:
                continue

            message_link = report['message_link']
            parts = message_link.split('/')
            channel_id = int(parts[5])
            message_id = int(parts[6])
            if not message_id:
                continue

            try:
                message = await self.bot.get_channel(channel_id).fetch_message(message_id)
                if len(message.embeds) < 2:
                    print("Message does not have two embeds")
                    continue

                status_embed = message.embeds[1]
                if 'Proof Status' not in status_embed.description:
                    status_embed.description += "\nProof Status: " + f"``{report['status']}``"
                else:
                    lines = status_embed.description.split("\n")
                    lines = [line for line in lines if not line.startswith("Proof Status:")]
                    lines.append("Proof Status: " + f"``{report['status']}``")
                    status_embed.description = "\n".join(lines)

                await message.edit(embeds=message.embeds)

                if report['status'] == "Proof Uploaded!":
                    status_embed.set_footer(text="Please wait.", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
                    await message.edit(embed=status_embed)
                    await asyncio.sleep(1)
                    status_embed.set_footer(text="Please wait..", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
                    await message.edit(embed=status_embed)
                    await asyncio.sleep(1)
                    status_embed.set_footer(text="Please wait...", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
                    await message.edit(embed=status_embed)
                    self.updated_reports.remove(code)
                    await self.update_embed(message, code)
                    await message.edit(embeds=message.embeds, view=ConfirmReport(bot=self.bot, author=message.author, message=message, code=report['code']))
            except discord.NotFound:
                self.updated_reports.remove(code)

    @commands.hybrid_group()
    async def scammer(self, ctx: commands.Context):
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

    @scammer.command()
    async def help(self, ctx: commands.Context):
        await self.scammer(ctx)

    @scammer.command()
    async def report(self, ctx: commands.Context, scammer: str):
        if not scammer:
            await ctx.send("Please specify a valid scammer.")
            return
        proof_code = shortuuid.ShortUUID().random(length=12)  # Generate a unique report code

        code_embed = discord.Embed(
            description=f"Report Code: ```{proof_code}```",
            color=ctx.author.color,
        )
        code_embed.set_author(name=f"Scammer Report | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)


        embed = discord.Embed(
            description=f"Scammer: ``{scammer}``",
            color=ctx.author.color,
        )
        view = ProofView(author=ctx.author, code=proof_code)
        view.add_item(discord.ui.Button(label="Click Here to Upload", style=discord.ButtonStyle.link, url="https://jbtradebase.xyz/upload", row=1))
        embed.set_footer(text=f"Please upload your proof on the website the button redirects you to.")
        embed.set_author(name=f"Scammer Report | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embeds = [code_embed, embed]
        message = await ctx.send(embeds=embeds, view=view)
        await database.create_report_verification(self.bot.db, code=proof_code, status="Pending Upload", reporter=ctx.author.id, scammer=scammer, public=False, message_link=message.jump_url)

        self.updated_reports.add(proof_code)  # Add the report code to track

    @scammer.command()
    async def search(self, ctx: commands.Context, search_by: str = None, search: str = None):
        embed = discord.Embed(
            description=None,
            color=ctx.author.color
        )
        embed.set_author(name=f"Scammer search | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        if search_by not in ["code", "name"]:
            embed.description = "**Invalid filter type**\n Choose between ``code`` or ``name``"
            await ctx.send(embed=embed)
            return
        if search_by == "code":
            if not search:
                embed.description = "Please provide a report code"
                await ctx.send(embed=embed)
                return
            embed.description = "Searching by code..."
            embed.set_footer(text="For a more broad search, try searching the name of the scammer.", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
            message = await ctx.send(embed=embed)
            await asyncio.sleep(2)
            report = await database.get_report(self.bot.db, search_by)
            if not report:
                embed.description = "No results found for this code"
                embed.set_footer(text=None, icon_url=None)
                await message.edit(embed=embed)
                return
            embed.description = "Report found!"
            embed.set_footer(text="Please wait...", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
            await message.edit(embed=embed)
            await asyncio.sleep(2)
        elif search_by == "name":
            if not search:
                embed.description = "Please provide a scammers name"
                await ctx.send(embed=embed)
                return
            embed.description = "Searching by scammer..."
            embed.set_footer(text="Please note: This will return all reports for this scammer.", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
            message = await ctx.send(embed=embed)
            await asyncio.sleep(2)
            reports = await database.get_scammer(self.bot.db, search)
            if not reports:
                embed.description = "No reports found for this scammer."
                embed.set_footer(text=None, icon_url=None)
                await message.edit(embed=embed)
                return
            embed.description = "Report(s) found!"
            embed.set_footer(text="Please wait...", icon_url="https://cdn.discordapp.com/attachments/1263603660261429511/1264337093820154019/Rolling1x-1.0s-200px-200px.gif?ex=669d812d&is=669c2fad&hm=4457abe52511b8120f0d3eff113a6dee1c1ef64a35d65179d175988b45a3f9f1&")
            await message.edit(embed=embed)
            await asyncio.sleep(2)

    @scammer.command(with_app_command=False)
    @commands.is_owner()
    async def delete(self, ctx: commands.Context, scammer: str):
        if not scammer:
            await ctx.send("Please specify a valid scammer.")
            return

async def setup(bot):
    await bot.add_cog(Scammer(bot))
