import discord
from discord.ext import commands, tasks
from discord import app_commands
from utilities import database
from discord.ui import Button, View
import random

MAX_BANK = 100000000, "100,000,000"
MULTIPLIER = 2
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
            if all(str(button.emoji) == "⭕" for button in buttons):
                amount_earned = int(self.amount) * int(MULTIPLIER)
                balance = self.user_data.get('balance', 0)
                new_balance = balance + amount_earned
                await database.update_user(self.bot.db, self.author.id, balance=new_balance)
                embed = discord.Embed(
                    color=self.author.color
                )
                embed.add_field(name="Amount earned:", value=f"``{amount_earned:,}``", inline=True)
                embed.add_field(name="Balance:", value=f"``{new_balance:,}``", inline=True)
                for button in self.children:
                    button.disabled = True
                await self.message.edit(embed=embed, view=self)
                return True
            elif all(str(button.emoji) == "❌" for button in buttons):
                await self.message.edit(content="Game over! The bot wins!", view=self)
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
                item.emoji = "❌"  # Bot plays with X
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
        if interaction.user != self.turn:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True, delete_after=2)

        self.available_positions.remove(int(button_clicked))

        for item in self.children:
            if item.custom_id == button_clicked:
                item.emoji = "⭕"  # User plays with O
                item.disabled = True
                break

        if await self.check_winner():
            return await interaction.response.defer()

        await self.pick_spot()

        await interaction.response.defer()

        

class TicTacToe(View):
    def __init__(self, opponent):
        super().__init__(timeout=120)
        self.winner = None



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
        embed.add_field(name="Balance", value=f"``{balance_str}``", inline=True)
        embed.add_field(name="Bank", value=f"``{bank_str}``", inline=True)
        embed.set_author(name=f"Balance | {user.display_name}", icon_url=user.avatar.url)
        await ctx.send(embed=embed)

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





    @commands.command(name= "add-money", description="Add money", aliases=["add-funds"])
    @commands.is_owner()
    async def addmoney(self, ctx: commands.Context, recipient: discord.User = None, amount: int = None):
        if not recipient:
            return await ctx.send("Please specify a recipient.")
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
    async def resetmoney(self, ctx: commands.Context, recipient: discord.User = None):
        if not recipient:
            return await ctx.send("Please specify a recipient.")

        user_data = await database.get_user(self.bot.db, recipient)
        new_bal = 0
        await database.update_user(self.bot.db, recipient.id, balance=new_bal)
        await ctx.send(f"User {recipient.display_name}'s balance has been reset to 0")
        









    @commands.hybrid_command(description="Play Tic Tac Toe", aliases=["ttt"])
    async def tictactoe(self, ctx: commands.Context, amount: str = None, user: discord.User = None):
        if not amount and not user:
            return await ctx.send("Usage: ``tictactoe(ttt) [amount] [user](None to play against the bot)``")
        embed = discord.Embed(
            color=ctx.author.color
        )
        user_data = await database.get_user(self.bot.db, ctx.author)
        balance = user_data.get('balance', 0)
        if amount == "all":
            amount = int(balance)
        elif amount == "half":
            amount = int(balance // 2)
        elif amount.isdigit():
            amount = int(amount)
        if not user:
            embed.description = "Playing against the bot..."
            message = await ctx.send(embed=embed)
            
            balance = user_data.get('balance', 0)
            if balance < amount:
                embed.description = "Insufficient funds for this game."
                return await message.edit(embed=embed)
            view = TicTacToeBot(self.bot, ctx.author, amount, user_data, message)
            await message.edit(content=f"{view.turn.mention}'s turn", view=view)
        else:
            await ctx.send("This part of the command is still in development. You can't play against another user right now.")


async def setup(bot):
    await bot.add_cog(Balance(bot))
