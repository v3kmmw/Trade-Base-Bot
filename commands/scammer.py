import discord
from discord.ext import commands, tasks
from utilities import database
from discord.ui import View, Button
import shortuuid
import asyncio



class SendReport(View):
    def __init__(self, author):
        super().__init__()
        self.author = author


    @discord.ui.button(label="Send Report", style=discord.ButtonStyle.green, disabled=False, row=1)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user!= self.author:
            await interaction.response.send_message("This isnt your report!", ephemeral=True)
        await interaction.response.send_message("Report sent!")


class ProofView(View):
    def __init__(self, author):
        super().__init__()
        self.author = author


class ConfirmReport(View):
    def __init__(self, bot, author, message, code):
        super().__init__()
        self.bot = bot
        self.author = author
        self.message = message
        self.code = code

    async def update_embed(self, message, code):
        # Fetch the report details from the database
        report = await database.get_report_verification(self.bot.db, code)
        if report is None:
            print("No report found")
            return

        proof = report.get('proof', [])
        cleaned_proof = [url.strip().strip('[]').strip('"') for url in proof if isinstance(url, str)]

        if not message.embeds:
            print("Message has no embed")
            return

        embed = message.embeds[0]
        description = embed.description or ""

        # Build new description parts
        new_description_parts = []

        # Create a mapping of lines to update
        lines_to_update = {
            "Proof Status:": f"Proof Status: ``{report['status']}``",
            "Report Code:": f"Report Code: ``{report['code']}``",
            "Public:": f"Public: ``{'Public' if report['public'] == 1 else 'Private'}``",
        }

        # Split existing description into lines
        description_lines = description.split("\n")

        # Update or add the new lines
        for line in description_lines:
            # Update if it's a line that needs to be changed
            for key, new_value in lines_to_update.items():
                if line.startswith(key):
                    new_description_parts.append(new_value)
                    del lines_to_update[key]
                    break
            else:
                # Preserve lines that don't need to be updated
                new_description_parts.append(line)

        # Append remaining lines that need to be added
        for key, new_value in lines_to_update.items():
            new_description_parts.append(new_value)

        # Set the new description
        updated_description = "\n".join(new_description_parts)
        embed.description = updated_description
        embed.set_footer(text="Scammer Report Overview")

        # Edit the message with the updated embed and view
        await message.edit(embed=embed, view=self)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, row=1)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await database.update_pending_proof_public(self.bot.db, self.code, 1)
        await self.update_embed(self.message, self.code)
        await interaction.response.send_message("The report has been made public.", ephemeral=True)
        # Optionally, remove the buttons or update the view
        self.clear_items()
        await self.message.edit(view=self)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, row=1)
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You chose not to make this report public.", ephemeral=True)
        # Optionally, remove the buttons or update the view
        self.clear_items()
        await self.message.edit(view=self)


class Scammer(commands.Cog):
    """Command to report, search, or delete scammers."""
    def __init__(self, bot):
        self.bot = bot
        self.updated_reports = set()
        self.check_reports.start()  # Start the task loop, but don't pass parameters

    async def update_embed(self, message, code):
        report = await database.get_report_verification(self.bot.db, code)
        if report is None:
            print("No report found")
            return

        proof = report.get('proof', [])
        cleaned_proof = [url.strip().strip('[]').strip('"') for url in proof if isinstance(url, str)]

        if not message.embeds:
            print("Message has no embed")
            return

        embed = message.embeds[0]
        embed_description_lines = embed.description.split("\n") if embed.description else []
        privacy = False
        if report['public'] == 0:
            privacy = False
        elif report['public'] == 1:
            privacy = True
        
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
        embed.description = updated_description
        embed.set_footer(text=f"Would you like this report to be public?")
        await message.edit(embed=embed, view=ConfirmReport(bot=self.bot, author=message.author, message=message, code=report['code']))

    @tasks.loop(seconds=1)
    async def check_reports(self):

        reports_to_check = list(self.updated_reports)
        for code in  reports_to_check:
            report = await database.get_report_verification(self.bot.db, code)
            if report is None:
                continue

            message_link = report['message_link']
            parts = message_link.split('/')
            server_id = parts[4]
            channel_id = parts[5]
            message_id = parts[6]
            channel_id = int(channel_id)
            message_id = int(message_id)
            if not message_id:
                continue

            try:
                message = await self.bot.get_channel(channel_id).fetch_message(message_id)
                embed = message.embeds[0]
                if 'Proof Status' not in embed.description:
                    embed.description += "\nProof Status: " + f"``{report['status']}``"
                else:
                    lines = embed.description.split("\n")
                    lines = [line for line in lines if not line.startswith("Proof Status:")]
                    lines.append("Proof Status: " + f"``{report['status']}``")
                    embed.description = "\n".join(lines)

                await message.edit(embed=embed)

                if report['status'] == "Proof Uploaded!":
                    self.updated_reports.remove(code)
                    await self.update_embed(message, code)
                    await message.edit(embed=embed, view=ConfirmReport(bot=self.bot, author=message.author, message=message, code=report['code']))
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

        embed = discord.Embed(
            description=f"Scammer: ``{scammer}``\nReport Code: ```{proof_code}```",
            color=ctx.author.color,
        )
        view = ProofView(author=ctx.author)
        view.add_item(discord.ui.Button(label="Click Here to Upload", style=discord.ButtonStyle.link, url="https://v3kmmw.github.io/JBTB/upload.html", row=1))
        embed.set_footer(text=f"Please upload your proof on the website the button redirects you to.")
        embed.set_author(name=f"Scammer Report | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        message = await ctx.send(embed=embed, view=view)
        await database.create_report_verification(self.bot.db, code=proof_code, status="Pending Upload", reporter=ctx.author.id, scammer=scammer, public=False, message_link=message.jump_url)

        self.updated_reports.add(proof_code)  # Add the report code to track

    @scammer.command()
    async def search(self, ctx: commands.Context, scammer: str):
        if not scammer:
            await ctx.send("Please specify a valid scammer.")
            return

    @scammer.command()
    async def delete(self, ctx: commands.Context, scammer: str):
        if not scammer:
            await ctx.send("Please specify a valid scammer.")
            return

async def setup(bot):

    await bot.add_cog(Scammer(bot))
