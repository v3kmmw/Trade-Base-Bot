import discord
from discord.ext import commands, tasks
from discord import app_commands
from utilities import database
from discord.ui import Button, View
import random
import asyncio
import uuid
import re

MAX_BANK = 100000000, "100,000,000"
TTT_MAX_AMOUNT = 10000, "10,000"
TTT_MULTIPLIER = 0.5
TTT_MULTIPLIER_MP = 0.25
ACTIVE_GAMES = set()
MM_GAMES = {}
MM_MULTIPLIER = 0.50
ACTIVE_MM_GAMES = {}

class TicTacToeBot(View):
    def __init__(self, bot, author, amount, user_data, message):
        super().__init__()
        self.author = author
        self.amount = amount
        self.user_data = user_data
        self.message = message
        self.bot = bot
        self.turn = author
        self.available_positions = set(range(1, 10))
        self.add_buttons()

    def add_buttons(self):
        positions = [
            ("1", 1), ("2", 1), ("3", 1),
            ("4", 2), ("5", 2), ("6", 2),
            ("7", 3), ("8", 3), ("9", 3)
        ]

        for pos, row in positions:
            button = Button(
                style=discord.ButtonStyle.gray,
                row=row,
                emoji='<:dash:1273874566665474150>',  # Initial emoji
                custom_id=pos
            )
            button.callback = self.on_button_click
            self.add_item(button)

    async def check_winner(self):
        winning_combinations = [
            ["1", "2", "3"],  # Row 1
            ["4", "5", "6"],  # Row 2
            ["7", "8", "9"],  # Row 3
            ["1", "4", "7"],  # Column 1
            ["2", "5", "8"],  # Column 2
            ["3", "6", "9"],  # Column 3
            ["1", "5", "9"],  # Diagonal 1
            ["3", "5", "7"],  # Diagonal 2
        ]

        for combo in winning_combinations:
        # Retrieve the buttons corresponding to the current winning combination
            buttons = [button for button in self.children if button.custom_id in combo]
            if all(str(button.emoji) == "<:circle:1273874589604380817>" for button in buttons):
                amount_earned = int(self.amount) * int(TTT_MULTIPLIER)
                balance = self.user_data.get('balance', 0)
                new_balance = balance + amount_earned - self.amount
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                embed = discord.Embed(
                    color=self.author.color
                )
                embed.add_field(name="Opponent:", value=f"Bot", inline=False)
                embed.add_field(name="Amount earned:", value=f"``{amount_earned:,}``", inline=True)
                embed.add_field(name="Balance:", value=f"``{new_balance:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content=f"Winner: {self.author.mention}", embed=embed, view=self)
                return True
            elif all(str(button.emoji) == "<:x_:1273874576136208414>" for button in buttons):
                balance = self.user_data.get('balance', 0)
                new_balance = balance - int(self.amount)
            
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                embed = discord.Embed(
                    color=self.author.color
                )
                embed.add_field(name="Opponent:", value=f"{self.author.mention}", inline=False)
                embed.add_field(name="Amount lost:", value=f"``{self.amount:,}``", inline=True)
                embed.add_field(name="Balance:", value=f"``{new_balance:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content="Winner: Bot", embed=embed, view=self)
                return True

        if not self.available_positions:
            await self.message.edit(content="It's a tie!", view=self)
            return True

        return False

    async def pick_spot(self):
        position = random.choice(list(self.available_positions))
        self.available_positions.remove(position)

        for item in self.children:
            if item.custom_id == str(position):
                item.emoji = "<:x_:1273874576136208414>"  # Bot plays with X
                item.disabled = True
                break

        if await self.check_winner():
            ACTIVE_GAMES.remove(self.author.id)
            return 

        self.turn = self.author
        await self.message.edit(content=f"{self.turn.mention}'s turn", view=self)

    async def on_button_click(self, interaction: discord.Interaction):
        button_clicked = interaction.data["custom_id"]

        if int(button_clicked) not in self.available_positions:
            return await interaction.response.send_message("Invalid position!", ephemeral=True, delete_after=2)
        if interaction.user != self.bot and interaction.user != self.author:
            return await interaction.response.send_message("This isnt your game!", ephemeral=True, delete_after=2)
        if interaction.user != self.turn:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True, delete_after=2)

        self.available_positions.remove(int(button_clicked))

        for item in self.children:
            if item.custom_id == button_clicked:
                item.emoji = "<:circle:1273874589604380817>"  # User plays with O
                item.disabled = True
                break

        if await self.check_winner():
            try:
                ACTIVE_GAMES.remove(self.author.id)
            except KeyError:
                pass
            return await interaction.response.defer()

        await self.pick_spot()

        await interaction.response.defer()

        

class TicTacToe(View):
    def __init__(self, bot, author, opponent, amount, message):
        super().__init__()
        self.author = author
        self.opponent = opponent
        self.amount = amount
        self.message = message
        self.bot = bot
        self.turn = opponent
        self.available_positions = set(range(1, 10))
        self.add_buttons()

    def add_buttons(self):
        positions = [
            ("1", 1), ("2", 1), ("3", 1),
            ("4", 2), ("5", 2), ("6", 2),
            ("7", 3), ("8", 3), ("9", 3)
        ]

        for pos, row in positions:
            button = Button(
                style=discord.ButtonStyle.gray,
                row=row,
                emoji='<:dash:1273874566665474150>',  # Initial emoji
                custom_id=pos
            )
            button.callback = self.on_button_click
            self.add_item(button)

    async def check_winner(self):
        winning_combinations = [
            ["1", "2", "3"],  # Row 1
            ["4", "5", "6"],  # Row 2
            ["7", "8", "9"],  # Row 3
            ["1", "4", "7"],  # Column 1
            ["2", "5", "8"],  # Column 2
            ["3", "6", "9"],  # Column 3
            ["1", "5", "9"],  # Diagonal 1
            ["3", "5", "7"],  # Diagonal 2
        ]
        user_data = await database.get_user(self.bot.db, self.author)
        opponent_data = await database.get_user(self.bot.db, self.opponent)
        for combo in winning_combinations:
        # Retrieve the buttons corresponding to the current winning combination
            buttons = [button for button in self.children if button.custom_id in combo]
            if all(str(button.emoji) == "<:circle:1273874589604380817>" for button in buttons):
                amount_earned = int(self.amount) * TTT_MULTIPLIER_MP
                balance = user_data.get('balance', 0)
                new_balance = balance + amount_earned - self.amount
                opponent_balance = opponent_data.get('balance', 0)
                new_opponent_balance = opponent_balance - self.amount
                await database.update_user(self.bot.db, self.author.id, balance=new_opponent_balance)
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                embed = discord.Embed(
                    color=self.author.color,
                )
                
                embed.set_author(name=f"{self.author.display_name} | Tic Tac Toe", icon_url=self.author.avatar.url)
                embed.add_field(name=f"", value=f"{self.author.mention} | <:circle:1274093009952051271>:\n``+{self.amount:,}``", inline=True)
                embed.add_field(name=f"", value=f"{self.opponent.mention} | <:x_:1274093008261873795>:\n``-{self.amount:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content=f"Winner: {self.author.mention}", embed=embed, view=self)
                return True
            elif all(str(button.emoji) == "<:x_:1273874576136208414>" for button in buttons):
                balance = user_data.get('balance', 0)
                new_balance = balance - int(self.amount)
                opponent_balance = opponent_data.get('balance', 0)
                amount_earned = int(self.amount) * TTT_MULTIPLIER_MP
                new_opponent_balance = opponent_balance + int(amount_earned) - self.amount
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                await database.update_user(self.bot.db, self.opponent.id, balance=new_opponent_balance)
                embed = discord.Embed(
                    color=self.author.color,
                )
                embed.set_author(name=f"{self.author.display_name} | Tic Tac Toe", icon_url=self.author.avatar.url)
                embed.add_field(name=f"", value=f"{self.opponent.mention} | <:x_:1274093008261873795>:\n``+{self.amount:,}``", inline=True)
                embed.add_field(name=f"", value=f"{self.author.mention} | <:circle:1274093009952051271>:\n``-{self.amount:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content=f"Winner: {self.opponent.mention}", embed=embed, view=self)
                return True

        if not self.available_positions:
            await self.message.edit(content="It's a tie!", view=self)
            return True

        return False

    async def on_button_click(self, interaction: discord.Interaction):
        button_clicked = interaction.data["custom_id"]
        if int(button_clicked) not in self.available_positions:
            return await interaction.response.send_message("Invalid position!", ephemeral=True, delete_after=2)
        if interaction.user != self.opponent and interaction.user != self.author:
            return await interaction.response.send_message("This isnt your game!", ephemeral=True, delete_after=2)
        if interaction.user != self.turn:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True, delete_after=2)
        embed = discord.Embed(
            color=interaction.user.color,
            description=f"{self.opponent.mention} VS {interaction.user.mention}"
        )
        self.available_positions.remove(int(button_clicked))

        for item in self.children:
            if item.custom_id == button_clicked:
                if self.turn == self.opponent:
                    item.emoji = "<:x_:1273874576136208414>"  # Opponent plays with O
                elif self.turn == self.author:
                    item.emoji = "<:circle:1273874589604380817>"  # User plays with X
                item.disabled = True
                break
        if await self.check_winner():
            ACTIVE_GAMES.remove(self.author.id)
            ACTIVE_GAMES.remove(self.opponent.id)
            return await interaction.response.defer()
        
        self.turn = self.opponent if self.turn == self.author else self.author
        await self.message.edit(content=f"{self.turn.mention}'s turn", view=self)
        await interaction.response.defer()


class UserConverter(commands.Converter):
    async def convert(self, ctx, argument):
        # Check if the argument is a mention
        mention_match = re.match(r'<@!?(\d+)>', argument)
        if mention_match:
            user_id = int(mention_match.group(1))
            user = ctx.guild.get_member(user_id) or await ctx.bot.fetch_user(user_id)
            if user:
                return user

        # Check if the argument is a user ID
        if argument.isdigit():
            user = ctx.guild.get_member(int(argument)) or await ctx.bot.fetch_user(int(argument))
            if user:
                return user

        # If the argument is "self", return the command author
        if argument == "self":
            return ctx.author

        # Check if the argument is a username
        members = [member for member in ctx.guild.members if argument.lower() in member.name.lower() or argument.lower() in member.display_name.lower()]
        if members:
            return members[0]
        
        # Raise an error if no user was found
        raise commands.BadArgument(f"User '{argument}' not found")


class LeaveMurderMystery(View):
    def __init__(self, bot, author, game_id, message, participants):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        self.participants = participants if participants else []

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, custom_id="leave_game")
    async def leavegame(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed = discord.Embed(
                color=self.author.color,
            )
            embed.description = f"You are not in the game!"
            await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
            return
        
        # Remove the user from the game and active games
        MM_GAMES[self.game_id].remove(interaction.user.id)
        ACTIVE_GAMES.remove(interaction.user.id)
        self.participants.remove(interaction.user)

        # Update the embed's description to remove the user's mention
        embed = self.message.embeds[0]
        mention_to_remove = f"- {interaction.user.mention}\n"
        embed.description = embed.description.replace(mention_to_remove, "")
        
        await self.message.edit(embed=embed)
        await interaction.response.send_message("You have left the game.", delete_after=2, ephemeral=True)


class MurderMysteryGame(View):
    def __init__(self, bot, author, game_id, message, participants=None):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        self.roles = {}
        self.available_roles = ["Murderer", "Innocent", "Sheriff"]
        self.participants = participants if participants else set()
        self.participant_roles = {}



    @discord.ui.button(label="View Participants", style=discord.ButtonStyle.green, custom_id="view_participants_mm")
    async def viewparticipants(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=self.author.color,
        )
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed.description = "You are not in the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        
        embed.description = f"### Participants:\n"
        for participant in self.participants:
            embed.description += f"- {participant.mention}\n"

    @discord.ui.button(emoji="<:question:1265591751809302621>", style=discord.ButtonStyle.gray, custom_id="help_mm")
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed.description = "You are not in the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)

        role = self.participant_roles.get(interaction.user.id)
        if role:
            if role.lower() == "murderer":
                embed.description = (
                    "### Murderer\n"
                    "- The bot will DM you with a select menu.\n"
                    "- Select one of the participants to murder them.\n"
                    "- The bot will temporarily mute the chosen member.\n"
                    "- After each kill, the remaining members get a chance to vote on who they think the murderer is."
                )
            elif role.lower() == "sheriff":
                embed.description = (
                    "### Sheriff\n"
                    "- The bot will DM you with a select menu.\n"
                    "- You can choose to shoot someone, but if you pick wrong, you will be eliminated as well.\n"
                    "- After you are eliminated, the bot will DM a random member, offering them the chance to become the new sheriff.\n"
                    "- If you correctly identify the murderer, the game ends and the innocent people win."
                )
            elif role.lower() == "innocent":
                embed.description = (
                    "### Innocent\n"
                    "- Your objective is to survive.\n"
                    "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                    "- If you are killed, you will be temporarily muted."
                )
        else:
            embed.description = (
                "### Murderer\n"
                "- The bot will DM you with a select menu.\n"
                "- Select one of the participants to murder them.\n"
                "- The bot will temporarily mute the chosen member.\n"
                "- After each kill, the remaining members get a chance to vote on who they think the murderer is.\n"
                "### Sheriff\n"
                "- The bot will DM you with a select menu.\n"
                "- You can choose to shoot someone, but if you pick wrong, you will be eliminated as well.\n"
                "- After you are eliminated, the bot will DM a random member, offering them the chance to become the new sheriff.\n"
                "- If you correctly identify the murderer, the game ends and the innocent people win.\n"
                "### Innocent\n"
                "- Your objective is to survive.\n"
                "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                "- If you are killed, you will be temporarily muted."
            )

        embed.set_author(name="Murder Mystery Help", icon_url=self.author.avatar.url)
        await interaction.response.send_message(embed=embed, delete_after=10, ephemeral=True)

class MurderMysteryRoleClaim(View):
    def __init__(self, bot, author, game_id, message, participants=None):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        self.roles = {}
        self.available_roles = ["Murderer", "Innocent", "Sheriff"]
        self.participants = participants if participants else set()
        self.participant_roles = {}

    @discord.ui.button(label="View Role", style=discord.ButtonStyle.green, custom_id="claim_role")
    async def claimrole(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=self.author.color,
        )
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed.description = "You are not in the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)

        if self.participant_roles.get(interaction.user.id):
            embed.description = f"Your role is ``{self.participant_roles[interaction.user.id].lower()}``."
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)

        role = random.choice(self.available_roles)
        if role in ["Murderer", "Sheriff"]:
            self.available_roles.remove(role)
        self.participant_roles[interaction.user.id] = role
        embed.description = f"You have been assigned the ``{role.lower()}`` role."
        await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)

        all_claimed = True
        for participant in self.participants:
            if not self.participant_roles.get(participant.id):
                all_claimed = False
                break

        if all_claimed:
            embed.set_author(name="Murder Mystery", icon_url=self.author.avatar.url)
            embed.description = "All participants have claimed their roles!\nThe game will begin shortly.\n### Participants:\n"
            for participant in self.participants:
                embed.description += f"- {participant.mention}\n"
                dm_embed = discord.Embed(
                    color=participant.color
                )
                if self.participant_roles.get(participant.id).lower() == "murderer":
                    dm_embed.description = (
                        "### You are the Murderer!\n\n"
                        "- You must murder everyone to win the game.\n"
                        "- When you murder someone, they will be muted for the duration of the game.\n"
                        "- If you die, you lose.\n"
                    )
                elif self.participant_roles.get(participant.id).lower() == "sheriff":
                    dm_embed.description = (
                        "### You are the Sheriff!\n\n"
                        "- You have been chosen to investigate the murderer.\n"
                        "- Work along with the other participants to find out who the murderer is.\n"
                        "- Be careful, the murderer is among the participants.\n"
                        "- You can choose to shoot someone, but if you pick wrong, you will be eliminated with them.\n"
                    )
                elif self.participant_roles.get(participant.id).lower() == "innocent":
                    dm_embed.description = (
                        "### You are Innocent!\n\n"
                        "- Your objective is to survive.\n"
                        "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                        "- If you are killed, you will be temporarily muted."
                    )
                await participant.send(embed=dm_embed)
            await self.message.edit(content="This game is still a work in progress, there is no more.", embed=embed, view=None)

    @discord.ui.button(emoji="<:question:1265591751809302621>", style=discord.ButtonStyle.gray, custom_id="help_mm")
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed.description = "You are not in the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)

        role = self.participant_roles.get(interaction.user.id)
        if role:
            if role.lower() == "murderer":
                embed.description = (
                    "### Murderer\n"
                    "- The bot will DM you with a select menu.\n"
                    "- Select one of the participants to murder them.\n"
                    "- The bot will temporarily mute the chosen member.\n"
                    "- After each kill, the remaining members get a chance to vote on who they think the murderer is."
                )
            elif role.lower() == "sheriff":
                embed.description = (
                    "### Sheriff\n"
                    "- The bot will DM you with a select menu.\n"
                    "- You can choose to shoot someone, but if you pick wrong, you will be eliminated as well.\n"
                    "- After you are eliminated, the bot will DM a random member, offering them the chance to become the new sheriff.\n"
                    "- If you correctly identify the murderer, the game ends and the innocent people win."
                )
            elif role.lower() == "innocent":
                embed.description = (
                    "### Innocent\n"
                    "- Your objective is to survive.\n"
                    "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                    "- If you are killed, you will be temporarily muted."
                )
        else:
            embed.description = (
                "### Murderer\n"
                "- The bot will DM you with a select menu.\n"
                "- Select one of the participants to murder them.\n"
                "- The bot will temporarily mute the chosen member.\n"
                "- After each kill, the remaining members get a chance to vote on who they think the murderer is.\n"
                "### Sheriff\n"
                "- The bot will DM you with a select menu.\n"
                "- You can choose to shoot someone, but if you pick wrong, you will be eliminated as well.\n"
                "- After you are eliminated, the bot will DM a random member, offering them the chance to become the new sheriff.\n"
                "- If you correctly identify the murderer, the game ends and the innocent people win.\n"
                "### Innocent\n"
                "- Your objective is to survive.\n"
                "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                "- If you are killed, you will be temporarily muted."
            )

        embed.set_author(name="Murder Mystery Help", icon_url=self.author.avatar.url)
        await interaction.response.send_message(embed=embed, delete_after=10, ephemeral=True)

                
        
class MurderMystery(View):
    def __init__(self, bot, author, game_id, message, participants=None):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        MM_GAMES[self.game_id] = set()
        MM_GAMES[self.game_id].add(self.author.id)
        self.cached_members = {}
        self.participants = participants if participants else set()
        self.participant_roles = {}
        self.start_count = 0
        self.startvote.label = f"Start 0/{len(participants)}"
        self.voted = set()


    @discord.ui.button(label="Join", style=discord.ButtonStyle.green, custom_id="join_game")
    async def joingame(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=self.author.color,
        )
        if interaction.user.id == self.author.id:
            embed.description = f"You cannot leave your own game!"
            await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
            return
        if interaction.user.id in MM_GAMES[self.game_id]:
            embed.description = f"Would you like to leave?"
            view = LeaveMurderMystery(self.bot, interaction.user, self.game_id, self.message, self.participants)
            await interaction.response.send_message(embed=embed, view=view, delete_after=5, ephemeral=True)
            return
        if interaction.user.id in ACTIVE_GAMES:
            embed.description = f"You are already in a game!"
            await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
            return
        MM_GAMES[self.game_id].add(interaction.user.id)
        embed.set_author(name=f"Murder Mystery | Host: {self.author.display_name}", icon_url=self.author.avatar.url)
        embed.set_footer(text="Game ID: " + str(self.game_id))
        embed.description = "\n### Participants:\n"

        for participant in MM_GAMES[self.game_id]:
            if participant in self.cached_members:
                user = self.cached_members[participant]
            else:
                user = self.bot.get_user(participant)
            self.cached_members[participant] = user
            embed.description += f"- {user.mention}\n"
        ACTIVE_GAMES.add(interaction.user.id)
        self.participants.append(interaction.user)
        prefix = await database.get_prefix(self.bot.db)
        embed.add_field(name="Start Command (Host):", value=f"```{prefix}mm start {self.game_id}```")
        self.startvote.label = f"Start {self.start_count}/{len(self.participants)}"
        await self.message.edit(embed=embed, view=self)
        await interaction.response.send_message("You have joined the game\nClick this again to leave.", ephemeral=True, delete_after=3)
    
        
    @discord.ui.button(label="Start | 0/0", style=discord.ButtonStyle.red, custom_id="start_vote")
    async def startvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        if interaction.user.id in self.voted:
            embed.description = "You have already voted!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        self.start_count += 1
        button.label = f"Start | {self.start_count}/{len(self.participants)}"
        self.voted.add(interaction.user.id)
        await interaction.message.edit(view=self)
        await interaction.response.send_message("Vote counted.", ephemeral=True, delete_after=3)
        if self.start_count == len(self.participants) and  self.start_count >= 2:
            embed.color = self.author.color
            embed.description = "### Game is starting!\nClick the button below to view your role.\n### Participants:\n"
            for participant in self.participants:
                embed.description += "- " + participant.mention + "\n"
            
            embed.set_author(name=f"Murder Mystery | Host: {self.author.display_name}", icon_url=self.author.avatar.url)
            view = MurderMysteryRoleClaim(self.bot, self.author, self.game_id, self.message, self.participants)
            await self.message.edit(embed=embed, view=view)
    @discord.ui.button(emoji="<:question:1265591751809302621>", style=discord.ButtonStyle.gray, custom_id="help_mm")
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed.description = "You are not in the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)

        role = self.participant_roles.get(interaction.user.id)
        if role:
            if role.lower() == "murderer":
                embed.description = (
                    "### Murderer\n"
                    "- The bot will DM you with a select menu.\n"
                    "- Select one of the participants to murder them.\n"
                    "- The bot will temporarily mute the chosen member.\n"
                    "- After each kill, the remaining members get a chance to vote on who they think the murderer is."
                )
            elif role.lower() == "sheriff":
                embed.description = (
                    "### Sheriff\n"
                    "- The bot will DM you with a select menu.\n"
                    "- You can choose to shoot someone, but if you pick wrong, you will be eliminated as well.\n"
                    "- After you are eliminated, the bot will DM a random member, offering them the chance to become the new sheriff.\n"
                    "- If you correctly identify the murderer, the game ends and the innocent people win."
                )
            elif role.lower() == "innocent":
                embed.description = (
                    "### Innocent\n"
                    "- Your objective is to survive.\n"
                    "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                    "- If you are killed, you will be temporarily muted."
                )
        else:
            embed.description = (
                "### Murderer\n"
                "- The bot will DM you with a select menu.\n"
                "- Select one of the participants to murder them.\n"
                "- The bot will temporarily mute the chosen member.\n"
                "- After each kill, the remaining members get a chance to vote on who they think the murderer is.\n"
                "### Sheriff\n"
                "- The bot will DM you with a select menu.\n"
                "- You can choose to shoot someone, but if you pick wrong, you will be eliminated as well.\n"
                "- After you are eliminated, the bot will DM a random member, offering them the chance to become the new sheriff.\n"
                "- If you correctly identify the murderer, the game ends and the innocent people win.\n"
                "### Innocent\n"
                "- Your objective is to survive.\n"
                "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                "- If you are killed, you will be temporarily muted."
            )

        embed.set_author(name="Murder Mystery Help", icon_url=self.author.avatar.url)
        await interaction.response.send_message(embed=embed, delete_after=10, ephemeral=True)

class Balance(commands.Cog):
    """Commands for managing balance and bank."""

    def __init__(self, bot):
        self.bot = bot
        self.max_bank = MAX_BANK
    
    @commands.hybrid_command(description="View your balance", aliases=["bal"])
    async def balance(self, ctx: commands.Context, user: discord.User = None):
        if not user:
            user = ctx.author

        user_data = await database.get_user(self.bot.db, user)
        balance = user_data.get('balance', 0)
        bank = user_data.get('bank', 0)
        embed = discord.Embed(
            color=user.color,
        )
        balance_str = f"{balance:,}"
        bank_str = f"{bank:,}"
        total_balance = balance + bank
        total_balance_str = f"{total_balance:,}"
        embed.add_field(name="Balance", value=f"``{balance_str}``", inline=True)
        embed.add_field(name="Bank", value=f"``{bank_str}``", inline=True)
        embed.set_author(name=f"Balance | {user.display_name}", icon_url=user.avatar.url)
        embed.set_footer(text=f"Total Balance: {total_balance_str}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="View the leaderboard of users", aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context, type: str = None):
        embed = discord.Embed(
            color=ctx.author.color,
        )
        embed.set_author(name=f"Leaderboard | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.description = "Fetching leaderboard..."
        message = await ctx.send(embed=embed)
        if not type:
            embed.description = "Type not specified, fetching balance leaderboard instead."
            embed.set_footer(text=f"This is because the leaderboard for total balance is not complete yet.")
            type = "balance"
            await message.edit(content="-# Want to see someones total balance? do ``bal (user)``", embed=embed)
            await asyncio.sleep(1)
        embed.set_footer(text=None)


        if type.lower() == "balance" or type.lower() == "bank":
            leaderboard = await database.get_bal_leaderboard(self.bot.db, type.lower())
            if leaderboard:
                description = ""
                for index, entry in enumerate(leaderboard):
                    if index >= 10:
                        break
                    user = ctx.guild.get_member(entry['id'])
                    user_name = user.mention if user else "``unknown``"
                    description += f"{index + 1}. {user_name}: ``{entry['balance']:,}``\n"
                embed.description = description
            else:
                embed.description = "No data found for the specified type."

        else:
            embed.description = "Invalid type specified.\n``leaderboard(lb) balance/bank/none``"

        await message.edit(content="", embed=embed)


    @commands.hybrid_command(description="Deposit your balance", aliases=["dep"])
    async def deposit(self, ctx: commands.Context, amount: str = None):
        embed = discord.Embed(
            color=ctx.author.color,
        )
        embed.set_author(name=f"Deposit | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        if not amount:
            embed.description = "Please specify an amount to deposit."
            await ctx.send(embed=embed)
            return
        
        user_data = await database.get_user(self.bot.db, ctx.author)
        balance = user_data.get('balance', 0)
        bank = user_data.get('bank', 0)
        if balance == 0:
            embed.description = "You don't have any balance to deposit."
            return await ctx.send(embed=embed)        
        # Default values for deposit amount
        dep_amount = 0
        max_bank_exceeded = False
        
        if amount == "all":
            dep_amount = balance
        elif amount == "half":
            dep_amount = balance // 2
        elif amount.isdigit():
            dep_amount = int(amount)
            if dep_amount > balance:
                embed.description = "Deposit amount cannot exceed your balance."
                return await ctx.send(embed=embed)
        else:
            embed.description = "Invalid deposit amount. Please use 'all' or 'half' or a positive"
            return await ctx.send(embed=embed)

        # Update balance and bank
        new_balance = balance - dep_amount
        bank += dep_amount
        
        # Check if bank exceeds maximum limit
        max_bank_int, _ = self.max_bank
        if bank > max_bank_int:
            excess_amount = bank - max_bank_int
            new_balance += excess_amount  # Adjust the balance
            bank = max_bank_int  # Set bank to the maximum limit
            max_bank_exceeded = True

        # Check for sufficient balance
        if new_balance < 0:
            embed.description = "Insufficient funds in your balance."
            return await ctx.send(embed=embed)
        
        # Update user data in the database
        await database.update_user(self.bot.db, ctx.author.id, balance=new_balance, bank=bank)
        
        # Notify user
        dep_amount_str = f"{dep_amount:,}"
        new_balance_str = f"{new_balance:,}"
        if max_bank_exceeded:
            embed.description = f"Deposited ``{dep_amount_str}``\nNew balance: ``{new_balance_str}``"
            embed.set_footer(text=f"Maximum bank limit exceeded by {excess_amount:,}")
            await ctx.send(embed=embed)
        else:
            embed.description = f"Deposited ``{dep_amount_str}``"
            await ctx.send(embed=embed)

    @commands.hybrid_command(description="Withdraw from your bank", aliases=["with"])
    async def withdraw(self, ctx: commands.Context, amount: str = None):
        embed = discord.Embed(
            color=ctx.author.color,
        )
        embed.set_author(name=f"Withdraw | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        if not amount:
            embed.description = "Please specify an amount to withdraw."
            await ctx.send(embed=embed)
            return
        
        user_data = await database.get_user(self.bot.db, ctx.author)
        balance = user_data.get('balance', 0)
        bank = user_data.get('bank', 0)
        
        if amount == "all":
            with_amount = bank
        elif amount == "half":
            with_amount = bank // 2
        elif amount.isdigit():
            with_amount = int(amount)
            if with_amount > bank:
                embed.description = "Withdrawal amount cannot exceed your bank balance."
                return await ctx.send(embed=embed)
        else:
            embed.description = "Invalid withdrawal amount. Please use 'all' or 'half' or a number."
            return await ctx.send(embed=embed)

        
        new_balance = balance + with_amount
        bank -= with_amount
        
        if new_balance < 0:
            embed.description = "Insufficient funds in your bank."
            return await ctx.send(embed=embed)
        
        # Update user data in the database
        await database.update_user(self.bot.db, ctx.author.id, balance=new_balance, bank=bank)
        embed.description = f"Withdrew ``{with_amount:,}``"
        await ctx.send(embed=embed)


    @commands.hybrid_command(description="Transfer money from one user to another", aliases=["transfer", "send"])
    async def give(self, ctx: commands.Context, recipient: UserConverter = None, amount: str = None):
        embed = discord.Embed(
            color=ctx.author.color,
        )
        if recipient == ctx.author:
            embed.description = "You cannot give yourself money."
            return await ctx.send(embed=embed)
        embed.set_author(name=f"Transfer | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        if not recipient:
            embed.description = "Please specify a recipient."
            return await ctx.send(embed=embed)
        if not amount:
            embed.description = "Please specify an amount to transfer."
            return await ctx.send(embed=embed)
        
        user_data = await database.get_user(self.bot.db, ctx.author)
        rescipient_data = await database.get_user(self.bot.db, recipient)
        balance = user_data.get('balance', 0)
        recipient_balance = rescipient_data.get('balance', 0)
        
        if amount == "all":
            trans_amount = balance
        elif amount == "half":
            trans_amount = balance // 2
        elif amount.isdigit():
            trans_amount = int(amount)
        new_balance = balance - trans_amount
        new_recipient_balance = recipient_balance + trans_amount
        
        if new_balance < 0:
            embed.description = "Insufficient funds in your balance."
            return await ctx.send(embed=embed)
        
        # Update user data in the database
        await database.update_user(self.bot.db, ctx.author.id, balance=new_balance)
        await database.update_user(self.bot.db, recipient.id, balance=new_recipient_balance)
        
        embed.description = f"Transferred ``{trans_amount:,}`` to {recipient.mention}"
        await ctx.send(embed=embed)
        



    @commands.command(name= "add-money", description="Add money", aliases=["add-funds", "add"])
    @commands.is_owner()
    async def addmoney(self, ctx: commands.Context, recipient: UserConverter = None, amount: int = None):
        if not recipient:
            return await ctx.send("Please specify a user.")
        if not amount:
            return await ctx.send("Please specify an amount to add.")
        if amount <= 0:
            return await ctx.send("To remove money, use ``remove-money``.")
        
        
        user_data = await database.get_user(self.bot.db, recipient)
        new_bal = user_data.get("balance", 0) + amount
        await database.update_user(self.bot.db, recipient.id, balance=new_bal)
        await ctx.send(f"{amount} has been added to {recipient.display_name}.")
        


    @commands.command(name= "reset-money", description="Reset money", aliases=["reset-funds"])
    @commands.is_owner()
    async def resetmoney(self, ctx: commands.Context, recipient: UserConverter = None):
        if not recipient:
            return await ctx.send("Please specify a user.")

        user_data = await database.get_user(self.bot.db, recipient)
        new_bal = 0
        await database.update_user(self.bot.db, recipient.id, balance=new_bal)
        await ctx.send(f"User {recipient.display_name}'s balance has been reset to 0")
        









    @commands.hybrid_command(description="Play Tic Tac Toe", aliases=["ttt"])
    async def tictactoe(self, ctx: commands.Context, amount: str = None, user: UserConverter = None):
        embed = discord.Embed(
            color=ctx.author.color
        )
        max_bet, max_bet_str = TTT_MAX_AMOUNT
        if user == ctx.author:
            embed.description = "You cannot play against yourself."
            return await ctx.send(embed=embed)
        if ctx.author.id in ACTIVE_GAMES:
            embed.description = f"You are already in a game."
            return await ctx.send(embed=embed)
        if not amount and not user:
            embed.description = "### Usage:\n ``tictactoe(ttt) [amount] [user](None to play against the bot)``"
            return await ctx.send(embed=embed)
        user_data = await database.get_user(self.bot.db, ctx.author)

        balance = user_data.get('balance', 0)
        if amount == "all":
            amount = int(balance)
        elif amount == "half":
            amount = int(balance // 2)
        elif amount.isdigit():
            amount = int(amount)
        else:
            embed.description = "Invalid amount. Please use 'all', 'half' or a number.\n``tictactoe(ttt) [amount] [user](None to play against the bot)``"
            return await ctx.send(embed=embed)
        if not user:
            embed.description = "Playing against the bot..."
            message = await ctx.send(embed=embed)
            
            balance = user_data.get('balance', 0)
            if balance < amount:
                embed.description = "Insufficient funds for this game."
                return await message.edit(embed=embed)
            if int(amount) > max_bet:
                embed.description = f"Maximum bet is {max_bet_str}"
                return await message.edit(embed=embed)
            view = TicTacToeBot(self.bot, ctx.author, amount, user_data, message)
            await message.edit(content=f"{view.turn.mention}'s turn", view=view)
            await database.update_user(self.bot.db, ctx.author.id, balance=balance - amount)
            ACTIVE_GAMES.add(ctx.author.id)
        else:
            if user.id in ACTIVE_GAMES:
                embed.description = f"{user.display_name} is already in a game."
                return await ctx.send(embed=embed)
            opponent_data = await database.get_user(self.bot.db, user)
            opponent_balance = opponent_data.get('balance', 0)
            if opponent_balance < amount:
                embed.description = f"{user.mention} does not have enough funds for this game."
                return await ctx.send(embed=embed)
            elif balance < amount:
                embed.description = "Insufficient funds for this game."
                return await ctx.send(embed=embed)
            if int(amount) > max_bet:
                embed.description = f"Maximum bet is {max_bet_str}"
                return await ctx.send(embed=embed)
            embed.description = f"{user.mention} VS {ctx.author.mention}"
            message = await ctx.send(embed=embed)
            
            balance = user_data.get('balance', 0)

            view = TicTacToe(self.bot, ctx.author, user, amount, message)
            await message.edit(content=f"{view.turn.mention}'s turn", view=view)
            await database.update_user(self.bot.db, ctx.author.id, balance=balance - amount)
            await database.update_user(self.bot.db, user.id, balance=opponent_balance - amount)
            ACTIVE_GAMES.add(ctx.author.id)
            ACTIVE_GAMES.add(user.id)

    @commands.hybrid_group(description="Host a game of murder mystery!", aliases=["mm"])
    async def murder_mystery(self, ctx: commands.Context):
        embed = discord.Embed(
            color=ctx.author.color
        )
        if ctx.author.id in ACTIVE_GAMES:
            embed.description = f"You are already in a game."
            return await ctx.send(embed=embed)
        game_id = str(uuid.uuid4())
        game_id = game_id[:8]
        embed.description = "A game of murder mystery has been started!\nClick below to join the game."
        embed.description += "\n### Participants:\n" + "- " + ctx.author.mention
        embed.set_footer(text="Game ID: " + str(game_id))
        embed.set_author(name=f"Murder Mystery | Host: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)        
        message = await ctx.send(embed=embed)
        game = MurderMystery(self.bot, ctx.author, game_id, message, participants=[ctx.author])
        await message.edit(view=game, embed=embed)
        ACTIVE_GAMES.add(ctx.author.id)
        ACTIVE_MM_GAMES[game_id] = game


    @murder_mystery.command(name="start", description="Start the game")
    async def start_game(self, ctx: commands.Context, game_id: str = None):
        embed = discord.Embed(
            color=ctx.author.color
        )
        if ctx.author.id not in ACTIVE_GAMES:
            embed.description = "You are not in a game."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        if not game_id:
            embed.description = "Please provide the game ID."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        game = ACTIVE_MM_GAMES.get(game_id)
        if not game:
            embed.description = "Game not found."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        message = game.message
        if ctx.author.id!= game.author.id:
            embed.description = "You are not the host of this game."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        embed.description = "### Game is starting!\nClick the button below to view your role.\n### Participants:\n"
        participants = game.participants
        if len(participants) <= 1:
            embed.description += "Not enough participants. Please wait for more players to join."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        for participant in participants:
            embed.description += "- " + participant.mention + "\n"

        embed.set_author(name=f"Murder Mystery | Host: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        view = MurderMysteryRoleClaim(self.bot, ctx.author, game_id, message, participants)
        await message.edit(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Balance(bot))
