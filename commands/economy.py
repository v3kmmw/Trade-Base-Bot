import discord
from discord.ext import commands, tasks
from discord import app_commands
from utilities import database
from discord.ui import Button, View, Select
import random
import asyncio
import uuid
import re
import config
import datetime
from datetime import timedelta

MAX_BANK = 100000000, "100,000,000"
TTT_MAX_AMOUNT = 10000, "10,000"
TTT_MULTIPLIER = 1.50
TTT_MULTIPLIER_MP = 1.25
ACTIVE_GAMES = set()
GAME_LINKS = {}
MM_GAMES = {}
MM_MULTIPLIER = 1.50
ROB_CHANCE = 0.5
ACTIVE_MM_GAMES = {}
MM_TIMEOUT_TIME = 600
MM_TIMEOUT_DELTA = timedelta(seconds=MM_TIMEOUT_TIME)
ROB_COOLDOWN = 60
WORK_COOLDOWN = 30
MINIMUM_WORK = 100
MAXIMUM_WORK = 500
class TicTacToeBot(View):
    def __init__(self, bot, author, amount, user_data, message):
        super().__init__(timeout=None)
        self.author = author
        self.amount = amount
        self.user_data = user_data
        self.message = message
        self.bot = bot
        self.turn = author
        self.available_positions = set(range(1, 10))
        self.add_buttons()

    async def log_game(self, author, opponent, result, message):
        log_channel = await self.bot.fetch_channel(config.LOG_CHANNEL)
        embed = discord.Embed(
            description=f"### Tic Tac Toe Game Log",
            timestamp=datetime.datetime.now(),
            color=author.color
        )
        embed.add_field(name="Player:", value=f"{author.mention}")
        embed.add_field(name="Opponent:", value=f"{opponent.mention}")
        embed.add_field(name="Result:", value=f"{result}")
        view = View()
        view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{message.jump_url}", row=1))
        await log_channel.send(embed=embed, view=view)

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
                amount_earned = int(self.amount) * max(float(TTT_MULTIPLIER), 1)
                print(amount_earned)
                balance = self.user_data.get('balance', 0)
                new_balance = balance + amount_earned
                await database.update_user(self.bot.db, self.author.id, balance=int(new_balance))
                embed = discord.Embed(
                    color=self.author.color
                )
                embed.add_field(name="Opponent:", value=f"Bot", inline=False)
                embed.add_field(name="Amount earned:", value=f"``{amount_earned:,}``", inline=True)
                embed.add_field(name="Balance:", value=f"``{new_balance:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content=f"Winner: {self.author.mention}", embed=embed, view=self)
                ACTIVE_GAMES.remove(self.author.id)
                await self.log_game(self.author, self.bot.user, f"{self.author.mention} won", self.message)
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
                ACTIVE_GAMES.remove(self.author.id)
                await self.log_game(self.author, self.bot.user, f"{self.bot.mention} won", self.message)
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
        super().__init__(timeout=None)
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

    async def log_game(self, author, opponent, result, message):
        log_channel = await self.bot.fetch_channel(config.LOG_CHANNEL)
        embed = discord.Embed(
            description=f"### Tic Tac Toe Game Log",
            timestamp=datetime.datetime.now(),
            color=author.color
        )
        embed.add_field(name="Player:", value=f"{author.mention}")
        embed.add_field(name="Opponent:", value=f"{opponent.mention}")
        embed.add_field(name="Result:", value=f"{result}")
        view = View()
        view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{message.jump_url}", row=1))
        await log_channel.send(embed=embed, view=view)

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
                amount_earned = int(self.amount) * max(float(TTT_MULTIPLIER_MP), 1)
                print(amount_earned)
                balance = user_data.get('balance', 0)
                new_balance = balance + int(amount_earned) + self.amount
                opponent_balance = opponent_data.get('balance', 0)
                new_opponent_balance = opponent_balance
                await database.update_user(self.bot.db, self.author.id, balance=new_opponent_balance)
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                embed = discord.Embed(
                    color=self.author.color,
                )
                
                embed.set_author(name=f"{self.author.display_name} | Tic Tac Toe", icon_url=self.author.avatar.url)
                embed.add_field(name=f"", value=f"{self.author.mention} | <:circle:1274093009952051271>:\n``+{amount_earned:,}``", inline=True)
                embed.add_field(name=f"", value=f"{self.opponent.mention} | <:x_:1274093008261873795>:\n``-{self.amount:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content=f"Winner: {self.author.mention}", embed=embed, view=self)
                await self.log_game(self.author, self.opponent, f"{self.author.mention} won", self.message)
                return True
            elif all(str(button.emoji) == "<:x_:1273874576136208414>" for button in buttons):
                balance = user_data.get('balance', 0)
                new_balance = balance 
                opponent_balance = opponent_data.get('balance', 0)
                amount_earned = int(self.amount) * max(float(TTT_MULTIPLIER_MP), 1)
                new_opponent_balance = opponent_balance + int(amount_earned) + self.amount
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                await database.update_user(self.bot.db, self.opponent.id, balance=new_opponent_balance)
                embed = discord.Embed(
                    color=self.author.color,
                )
                embed.set_author(name=f"{self.author.display_name} | Tic Tac Toe", icon_url=self.author.avatar.url)
                embed.add_field(name=f"", value=f"{self.opponent.mention} | <:x_:1274093008261873795>:\n``+{amount_earned:,}``", inline=True)
                embed.add_field(name=f"", value=f"{self.author.mention} | <:circle:1274093009952051271>:\n``-{self.amount:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(content=f"Winner: {self.opponent.mention}", embed=embed, view=self)
                await self.log_game(self.author, self.opponent, f"{self.opponent.mention} won", self.message)
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
        try:
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
            if argument.lower() == "self":
                return ctx.author

            # Check if the argument is a username
            members = [member for member in ctx.guild.members if argument.lower() in member.name.lower() or argument.lower() in member.display_name.lower()]
            if members:
                return members[0]

            # If no user was found, return None
            return None
        except Exception as e:
            return None


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
    def __init__(self, bot, author, game_id, message, participants=None, participant_roles=None):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        self.roles = {}
        self.available_roles = ["Murderer", "Innocent", "Sheriff"]
        self.participants = participants if participants else set()
        self.participant_roles = participant_roles



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
        await interaction.response.send_message(embed=embed, delete_after=5, ephemeral=True)

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

class MurderMysteryVote(View):
    def __init__(self, bot, author, game_id, message, participants=None, murdered_participants=None, participant_roles=None, alive_participants=None, murderer=None, wave=None):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        self.participants = participants
        self.murdered_participants = murdered_participants
        self.participant_roles = participant_roles
        self.alive_participants = alive_participants
        self.murderer = murderer
        self.wave = wave
        self.votes = {}
        self.voted_users = set()
        print(f"Alive participants: {self.alive_participants}")
        print(f"Murdered participants: {self.murdered_participants}")

        options = [
            discord.SelectOption(label=participant.display_name, value=str(participant.id), description=participant.id)
            for participant in self.alive_participants
        ]
        select = Select(
            placeholder="Who is the murderer?",
            options=options,
            custom_id="murderer_vote_select",
            max_values=1
        )
        select.callback = self.select_member
        self.add_item(select)



    async def select_member(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=interaction.user.color
        )
        role = self.participant_roles.get(interaction.user.id)
        if interaction.user.id in self.murdered_participants:
            embed.description = "You are dead, you can't vote."
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        if role.lower() == "murderer":
            embed.description = "You are the murderer. You can't vote."
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        selected_member_id = interaction.data['values'][0]
        selected_member = discord.utils.get(self.participants, id=int(selected_member_id))
        if selected_member == interaction.user:
            embed.description = "You can't vote for yourself."
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        if interaction.user in self.voted_users:
            embed.description = "You have already voted."
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        if selected_member and selected_member not in self.murdered_participants:
            if selected_member not in self.votes:
                self.votes[selected_member] = 1
            else:
                self.votes[selected_member] += 1
            embed.description = f"You have voted for {selected_member.mention}."
            embed.add_field(name="Votes", value=f"{self.votes[selected_member]}/{len(self.alive_participants) - 1}", inline=True)
            await interaction.response.send_message(embed=embed, delete_after=5, ephemeral=True)
            self.voted_users.add(interaction.user)
            if len(self.voted_users) == len(self.alive_participants) - 1:
                mm_embed = discord.Embed(
                    color=self.author.color,
                )
                mm_embed.description = f"### Votes:\n"
                sorted_votes = sorted(self.votes.items(), key=lambda x: x[1], reverse=True)
                for participant, vote_count in sorted_votes: 
                    mm_embed.description += f"- {participant.mention}: {vote_count}/{len(self.alive_participants) - 1}\n"
                mm_embed.set_author(name=f"Murder Mystery Vote | {self.wave}/{len(self.participants) - 1}", icon_url=self.author.avatar.url)
                await self.message.edit(embed=mm_embed, view=None)
                most_voted_participant = sorted_votes[0][0]
                role = self.participant_roles.get(most_voted_participant.id)
                if role.lower() == "murderer":
                    mm_embed.description = f"{most_voted_participant.mention} was the murderer!"
                    mm_embed.add_field(name="Votes:", value=f"``{self.votes[most_voted_participant]}/{len(self.alive_participants) - 1}``\n")
                else:
                    self.alive_participants.remove(most_voted_participant)
                    self.murdered_participants.add(most_voted_participant.id)
                    mm_embed.set_author(name=f"Murder Mystery Vote | {self.wave}/{len(self.participants) - 1}", icon_url=self.author.avatar.url)
                    mm_embed.description = f"{most_voted_participant.mention} was not the murderer!\nThe murderer is picking again..."
                    murderer_view = MurderMysteryMurderer(self.bot, self.author, self.game_id, self.message, self.participants, self.participant_roles, self.murderer, self.alive_participants, self.wave)
                    murderer = self.murderer
                    murderer_embed = discord.Embed(
                        color=murderer.color,
                    )
                    murderer_embed.description = f"### You survived!\nThere are still {len(self.alive_participants) - 1} participant(s) alive."
                    await murderer.send(embed=murderer_embed, view=murderer_view)
                await asyncio.sleep(3)
                await self.message.edit(embed=mm_embed, view=None)
            
        else:
            embed.description = "There was an error voting for this participant."
            await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True) 



    @discord.ui.button(emoji="<:question:1265591751809302621>", style=discord.ButtonStyle.gray, custom_id="help_mm", row=2)
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



    @discord.ui.button(emoji="<:gun:1275625126620168267>", style=discord.ButtonStyle.gray, custom_id="shoot", row=2)
    async def shoot(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        if interaction.user.id not in MM_GAMES[self.game_id]:
            embed.description = "You are not in the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        role = self.participant_roles.get(interaction.user.id)
        if role.lower() != "sheriff":
            embed.description = "Only the Sheriff can shoot!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        if interaction.user not in self.alive_participants:
            embed.description = "You are already dead!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        embed.description = "Choose a participant to shoot."
        view = Sheriff(self.bot, self.author, interaction.user, self.game_id, self.message, self.alive_participants, self.participant_roles)
        await interaction.response.send_message(embed=embed, view=view, delete_after=10, ephemeral=True)


class Sheriff(View):
    def __init__(self, bot, author, sheriff, game_id, message, alive_participants, participant_roles):
        super().__init__()
        self.bot = bot
        self.author = author
        self.sheriff = sheriff
        self.game_id = game_id
        self.message = message
        self.alive_participants = alive_participants
        self.participant_roles = participant_roles

        # Create select options dynamically based on participants
        options = [
            discord.SelectOption(label=participant.display_name, value=str(participant.id), description=participant.id)
            for participant in self.alive_participants if participant.id!= self.sheriff.id
        ]
        # Add the select menu to the view
        select = Select(
            placeholder="Select a participant to shoot",
            options=options,
            custom_id="sheriff_select",
            max_values=1
        )
        select.callback = self.select_member
        self.add_item(select)

    async def select_member(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        selected_member_id = interaction.data["values"][0]
        selected_member = discord.utils.get(self.alive_participants, id=int(selected_member_id))
        if selected_member:
            role = self.participant_roles.get(selected_member.id)
            embed.description = f"### You shot {selected_member.mention}!\n"
            if role.lower() == "murderer":
                embed.description += "||They were the murderer!||"
                mm_embed = discord.Embed(
                    color=self.author.color,
                )
                mm_embed.set_author(name="Murder Mystery", icon_url=self.author.avatar.url)
                mm_embed.description = f"{selected_member.mention} was the murderer!"
                mm_embed.add_field(name="Sheriff:", value=interaction.user.mention, inline=False)
                self.murdered_participants.add(selected_member.id)
                self.alive_participants.remove(selected_member)
            else:
                embed.description += "||They were not the murderer!||"
                self.murdered_participants.add(selected_member.id)
                self.alive_participants.remove(selected_member)
                self.murdered_participants.add(self.sheriff.id)
                self.alive_participants.remove(self.sheriff)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            if mm_embed:
                await asyncio.sleep(2)
                await self.message.edit(embed=mm_embed, view=None)
        else:
            embed.description = "Invalid participant!\nAre they dead already?"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
            



class MurderMysteryMurderer(View):
    def __init__(self, bot, author, game_id, message, participants=None, participant_roles=None, murderer=None, alive_participants=None, wave=None):
        super().__init__()
        self.bot = bot
        self.author = author
        self.game_id = game_id
        self.message = message
        self.roles = {}
        self.participants = participants
        self.participant_roles = participant_roles
        self.murderer = murderer
        self.murdered_participants = set()
        self.alive_participants = participants.copy() if alive_participants is None else alive_participants
        self.wave = wave if wave else 1
        # Create select options dynamically based on participants
        options = [
            discord.SelectOption(label=participant.display_name, value=str(participant.id), description=participant.id)
            for participant in self.alive_participants if participant.id != self.murderer.id
        ]

        # Add the select menu to the view
        select = Select(
            placeholder="Select a participant to murder",
            options=options,
            custom_id="murderer_select",
            max_values=1
        )
        select.callback = self.select_member
        self.add_item(select)

    async def select_member(self, interaction: discord.Interaction):
        selected_member_id = interaction.data['values'][0]
        selected_member = discord.utils.get(self.participants, id=int(selected_member_id))
        if selected_member and selected_member.id not in self.murdered_participants:
            self.murdered_participants.add(selected_member.id)
            self.alive_participants.remove(selected_member)
            await interaction.response.send_message(f"You Murdered {selected_member.mention}.")
            embed = discord.Embed(
                color=self.author.color
            )
            embed.set_author(name=f"Murder Mystery | {self.wave}/{len(self.participants) - 1}", icon_url=self.author.avatar.url)
            self.wave += 1
            view = MurderMysteryVote(self.bot, self.author, self.game_id, self.message, self.participants, self.murdered_participants, self.participant_roles, self.alive_participants, self.murderer, self.wave)
            if len(self.alive_participants) <= 1:
                embed.set_author(name=f"Murder Mystery | {self.wave}/{len(self.participants) - 1}", icon_url=self.author.avatar.url)
                embed.description = f"All participants have been murdered. The murderer wins!\n### Murderer: {self.murderer.mention}"
                return await self.message.edit(embed=embed, view=None)
            else:
                embed.description = f"{selected_member.mention} has been murdered."
                await self.message.edit(embed=embed, view=view)
        else:
            await interaction.response.send_message("There was an error murdering this participant.")\
            



    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # This method checks if the interaction is from the game author
        return interaction.user == self.murderer


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
        if len(self.participant_roles) == len(self.participants) - 2:
            if "Murderer" not in self.participant_roles.values():
                role = "Murderer"
            elif "Sheriff" not in self.participant_roles.values():
                role = "Sheriff"
            else:
                role = random.choice(self.available_roles)
        else:
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
            embed.description = "All participants have claimed their roles!\nThe game will begin shortly.\n"
            for participant in self.participants:
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
                    view = MurderMysteryMurderer(self.bot, self.author, self.game_id, self.message, self.participants, self.participant_roles, participant, None, 1)
                elif self.participant_roles.get(participant.id).lower() == "sheriff":
                    dm_embed.description = (
                        "### You are the Sheriff!\n\n"
                        "- You have been chosen to investigate the murderer.\n"
                        "- Work along with the other participants to find out who the murderer is.\n"
                        "- Be careful, the murderer is among the participants.\n"
                        "- You can choose to shoot someone, but if you pick wrong, you will be eliminated with them.\n"
                    )
                    view = None
                elif self.participant_roles.get(participant.id).lower() == "innocent":
                    dm_embed.description = (
                        "### You are Innocent!\n\n"
                        "- Your objective is to survive.\n"
                        "- Try to avoid getting killed and vote on who you think the murderer is.\n"
                        "- If you are killed, you will be temporarily muted."
                    )
                    view=None
                await participant.send(embed=dm_embed, view=view)
            gameview = MurderMysteryGame(self.bot, self.author, self.game_id, self.message, self.participants, self.participant_roles)
            await self.message.edit(embed=embed, view=gameview)

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
        super().__init__(timeout=300)
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
            game_link = GAME_LINKS[interaction.user.id]
            view = View()
            view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{game_link}", row=1))
            embed.description = f"You are already in a game."
            await interaction.response.send_message(embed=embed, view=view, delete_after=3, ephemeral=True)
            return
        MM_GAMES[self.game_id].add(interaction.user.id)
        GAME_LINKS[interaction.user.id] = self.message.jump_url
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
        if len(MM_GAMES[self.game_id]) >= 4:
            embed.description += "The game can be started!"
            embed.add_field(name="Start Command (Host):", value=f"```{prefix}mm start {self.game_id}```")
        self.startvote.label = f"Start {self.start_count}/{len(self.participants)}"
        await self.message.edit(embed=embed, view=self)
        await interaction.response.send_message("Click again to leave.", ephemeral=True, delete_after=3)
    
        
    @discord.ui.button(label="Start | 0/0", style=discord.ButtonStyle.red, custom_id="start_vote")
    async def startvote(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            color=interaction.user.color,
        )
        if len(self.participants) < 4:
            embed.description = "Not enough participants to start the game!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        if interaction.user.id in self.voted:
            embed.description = "You have already voted!"
            return await interaction.response.send_message(embed=embed, delete_after=2, ephemeral=True)
        self.start_count += 1
        button.label = f"Start | {self.start_count}/{len(self.participants)}"
        self.voted.add(interaction.user.id)
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        if self.start_count == len(self.participants):
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

class Economy(commands.Cog):
    """Commands for managing balance and bank."""

    def __init__(self, bot):
        self.bot = bot
        self.max_bank = MAX_BANK
    





    async def log_transaction(self, user: discord.User, amount: int, transaction_type: str):
        log_channel = await self.bot.fetch_channel(config.LOG_CHANNEL)
        embed = discord.Embed(
            color=user.color,
        )
        embed.set_author(name=f"{user.display_name} | {transaction_type}", icon_url=user.avatar.url)
        embed.add_field(name="Amount", value=f"``{amount:,}``", inline=True)
        user_data = await database.get_user(self.bot.db, user)
        embed.add_field(name="Balance", value=f"``{user_data.get('balance', 0):,}``", inline=True)
        embed.add_field(name="Bank", value=f"``{user_data.get('bank', 0):,}``", inline=True)
        embed.timestamp = datetime.datetime.now()
        await log_channel.send(embed=embed)

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
        if not type:
            type = "total"
        embed.set_author(name=f"Leaderboard | {type.capitalize()} | {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.description = "Fetching leaderboard..."
        message = await ctx.send(embed=embed)

        if type.lower() == "balance" or type.lower() == "bank" or type.lower() == "total":
            leaderboard = await database.get_bal_leaderboard(self.bot.db, type.lower())
            if leaderboard:
                description = ""
                for index, entry in enumerate(leaderboard):
                    if index >= 10:
                        break
                    user = ctx.guild.get_member(entry['id'])
                    user_name = user.mention if user else "``unknown``"
                    amount = entry['amount']
                    description += f"{index + 1}. {user_name}: ``{amount:,}``\n"
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
        await self.log_transaction(ctx.author, dep_amount, "Deposit")
        
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
        await self.log_transaction(ctx.author, with_amount, "Withdrawal")
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
    async def addmoney(self, ctx: commands.Context, recipient: UserConverter = None, amount: int = None, type: str = None):
        if not recipient:
            return await ctx.send("Please specify a user.")
        if not amount:
            return await ctx.send("Please specify an amount to add.")
        if amount <= 0:
            return await ctx.send("To remove money, use ``remove-money``.")
        if not type:
            type = "balance"
        if type not in ["balance", "bank"]:
            return await ctx.send("Invalid type. Use either ``balance`` or ``bank``.")
        
        
        user_data = await database.get_user(self.bot.db, recipient)
        user_amount = user_data.get(type, 0) + amount
        await database.update_user(self.bot.db, recipient.id, **{type: user_amount})
        await self.log_transaction(ctx.author, amount, "Add")
        await ctx.send(f"{amount} has been added to {recipient.display_name}'s {type}.")
        


    @commands.command(name= "reset-money", description="Reset money", aliases=["reset-funds"])
    @commands.is_owner()
    async def resetmoney(self, ctx: commands.Context, recipient: UserConverter = None):
        if not recipient:
            return await ctx.send("Please specify a user.")

        new_bal = 0
        await database.update_user(self.bot.db, recipient.id, balance=new_bal)
        await self.log_transaction(ctx.author, 0, "Reset")
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
            game_link = GAME_LINKS[ctx.author.id]
            view = View()
            view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{game_link}", row=1))
            embed.description = f"You are already in a game."
            return await ctx.send(embed=embed, view=view)
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
            GAME_LINKS[ctx.author.id] = message.jump_url
        else:
            if user.id in ACTIVE_GAMES:
                embed.description = f"{user.display_name} is already in a game."
                game_link = GAME_LINKS[user.id]
                view = View()
                view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{game_link}", row=1))
                return await ctx.send(embed=embed, view=view)
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

    @commands.hybrid_group(name="murder-mystery",description="Host a game of murder mystery!", aliases=["mm"])
    async def murder_mystery(self, ctx: commands.Context):
        """Usage: ``mm <subcommand>``"""
        embed = discord.Embed(
            color=ctx.author.color
        )
        if ctx.author.id in ACTIVE_GAMES:
            game_id = GAME_LINKS[ctx.author.id]
            view = View()
            view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{game_id}", row=1))
            embed.description = f"You are already in a game."
            return await ctx.send(embed=embed, view=view)
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
        GAME_LINKS[ctx.author.id] = message.jump_url
        ACTIVE_MM_GAMES[game_id] = game



    @murder_mystery.command(name="start", description="Start the game")
    async def start_game(self, ctx: commands.Context, game_id: str = None):
        """### Usage: ``mm start <game_id``\n
        - Manually start a game by providing the game ID.
        - To Host a game, use the ``mm`` command.
        -# **This command is host only.**
        """
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
        if len(participants) <= 4:
            embed.description += "Not enough participants. Please wait for more players to join."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        for participant in participants:
            embed.description += "- " + participant.mention + "\n"

        embed.set_author(name=f"Murder Mystery | Host: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        view = MurderMysteryRoleClaim(self.bot, ctx.author, game_id, message, participants)
        await message.edit(embed=embed, view=view)

    @murder_mystery.command(name="join", description="Join a game")
    async def join_game(self, ctx: commands.Context, game_id: str = None):
        """
        ### Usage: ``mm join <game_id>``\n
        - Join a game by providing the game ID.
        """
        embed = discord.Embed(
            color=ctx.author.color
        )
        if not game_id:
            embed.description = "Please provide the game ID."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        game = ACTIVE_MM_GAMES.get(game_id)
        if not game:
            embed.description = "Game not found."
            return await ctx.send(embed=embed, delete_after=2, ephemeral=True)
        message = game.message
        view = View()
        embed.set_author(name=f"Murder Mystery | Host: {game.author.display_name}", icon_url=game.author.avatar.url)
        embed.description = "Click the button below to join the game."
        view.add_item(discord.ui.Button(label="View Message", style=discord.ButtonStyle.link, url=f"{message.jump_url}", row=1))
        await ctx.send(embed=embed, view=view)


    @murder_mystery.command(name="end", description="End the game")
    async def end_game(self, ctx: commands.Context, game_id: str = None):
        """### Usage: ``mm end <game_id>``\n
        - End the game manually. 
        - You will not receive any rewards.
        -# **This command is host only.**
        """
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
        participants = game.participants
        for participant in participants:
            ACTIVE_GAMES.remove(participant.id)
        ACTIVE_MM_GAMES.pop(game_id)
        embed.set_author(name=f"Murder Mystery | Host: {game.author.display_name}", icon_url=game.author.avatar.url)
        embed.description = "Game has been ended by host."
        await message.edit(embed=embed, view=None)
        await ctx.defer()
    

    @commands.hybrid_command(description="Rob a member")
    @commands.cooldown(1, ROB_COOLDOWN, commands.BucketType.user)
    async def rob(self, ctx: commands.Context, user: UserConverter = None):
        """### Usage: ``rob <user>``\n
        - Rob another member.
        - You will receive a random amount of money if successful.
        """
        if user == ctx.author:
            return await ctx.send("You cannot rob yourself.")
        if not user:
            return await ctx.send("Please specify a user.")
        if random.random() < ROB_CHANCE:
            response = await database.get_failed_rob_response(self.bot.db, user)
            embed = discord.Embed(color=ctx.author.color)
            embed.set_author(name=f"Robbery Attempt", icon_url=ctx.author.avatar.url)
            embed.description = response
            embed.add_field(name="Amount Lost", value="``0``", inline=False)
            await ctx.send(embed=embed)
            return
        else:
            user_data = await database.get_user(self.bot.db, user)
            user_balance = user_data.get("balance", 0)
            
            if user_balance <= 0:
                return await ctx.send(f"{user.display_name} has no money to rob!")
            max_steal_amount = int(user_balance * 0.8)
            stolen_amount = random.randint(1, max_steal_amount)
            new_user_balance = user_balance - stolen_amount
            await database.update_user(self.bot.db, user.id, balance=new_user_balance)
            robber_data = await database.get_user(self.bot.db, ctx.author)
            new_robber_balance = robber_data.get("balance", 0) + stolen_amount
            await database.update_user(self.bot.db, ctx.author.id, balance=new_robber_balance)
            await ctx.send("You robbed " + user.mention + "!")

    @commands.group(name="rob-response")
    @commands.is_owner()
    async def robresponse(self, ctx: commands.Context):
        """
        Robresponse manager, for more info use ``help rob-response <subcommand>``
        """
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @robresponse.command()
    async def remove(self, ctx: commands.Context, response_id: int = None):
        """
        Remove a rob failure response by its ID.
        Usage:
        - `robresponse remove <response_id>`: Removes the rob failure response with the specified ID.
        """
        embed = discord.Embed(color=ctx.author.color)
        embed.set_author(name=f"Remove Failed Robbery Response", icon_url=ctx.author.avatar.url)
        if not response_id:
            await ctx.send_help(ctx.command)
        result = await database.remove_failed_rob_response(self.bot.db, response_id)
        if result == False:
            embed.description = "Failed to remove robbery response."
            return await ctx.send(embed=embed)
        embed.description = "Robbery response removed."
        await ctx.send(embed=embed)

    @robresponse.command()
    async def list(self, ctx: commands.Context):
        """
        List all rob failure responses.
        Usage:
        - `robresponse list`: Lists all rob failure responses.
        """
        responses = await database.get_failed_rob_responses(self.bot.db)
        embed = discord.Embed(color=ctx.author.color)
        embed.set_author(name=f"Failed Robbery Responses", icon_url=ctx.author.avatar.url)
        for i, response in enumerate(responses, start=1):
            if i > 10:
                embed.description = f"Showing 10/{len(responses)}"
                break
            embed.add_field(name=f"{i}.", value=response, inline=False)
        await ctx.send(embed=embed)
    
    @robresponse.command()
    async def add(self, ctx: commands.Context, response: str = None):
        """
        Add a new rob failure response.
        Usage:
        - `robresponse add <response>`: Adds a new rob failure response.
        """
        embed = discord.Embed(color=ctx.author.color)
        embed.set_author(name=f"Add Failed Robbery Response", icon_url=ctx.author.avatar)
        if not response:
            await ctx.send_help(ctx.command)
        if len(response) > 250:
            embed.description = "Response too long. Maximum length is 250 characters."
            return await ctx.send(embed=embed)
        if len(response) < 15:
            embed.description = "Response too short. Minimum length is 15 characters."
            return await ctx.send(embed=embed)
        result = await database.add_failed_rob_response(self.bot.db, response)
        if result == False:
            embed.description = "Failed to add robbery response."
            return await ctx.send(embed=embed)
        embed.description = "Response added."
        embed.add_field(name="Response", value=response, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description="Work for money.")
    @commands.cooldown(1, WORK_COOLDOWN, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        """### Usage: ``work``\n
        - Work for money.
        - You will receive a random amount of money. 
        """
        user_data = await database.get_user(self.bot.db, ctx.author)
        user_balance = user_data.get("balance", 0)
        earnings = random.randint(MINIMUM_WORK, MAXIMUM_WORK)
        new_user_balance = user_balance + earnings
        await database.update_user(self.bot.db, ctx.author.id, balance=new_user_balance)
        await ctx.send(f"You worked and earned {earnings}!")

    @commands.hybrid_command(description="Learn how to use the economy commands.")
    async def economy(self, ctx: commands.Context):
        """### Usage: ``economy``\n
        - Learn how to use the economy commands.
        """
        embed = discord.Embed(color=ctx.author.color)
        embed.set_author(name=f"Economy Commands", icon_url=ctx.author.avatar.url)
        embed.add_field(name="work", value=f"Work for balance. ({WORK_COOLDOWN}s cooldown)", inline=True)
        embed.add_field(name="rob", value=f"Rob a member. ({ROB_COOLDOWN}s cooldown)", inline=True)
        embed.add_field(name="balance", value="Check your balance.", inline=True)
        embed.add_field(name="transfer", value="Transfer balance to another user.", inline=True)
        embed.add_field(name="deposit", value="Deposit balance into your bank account.", inline=True)
        embed.add_field(name="withdraw", value="Withdraw balance from your bank account.", inline=True)
        embed.add_field(name="tictactoe", value="Play tic tac toe against the bot or another user.", inline=True)
        embed.add_field(name="murder-mystery", value="Host a game of murder mystery", inline=True)
        await ctx.send(embed=embed)

        
            

async def setup(bot):
    await bot.add_cog(Economy(bot))
