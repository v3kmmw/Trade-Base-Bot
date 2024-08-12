import config
import logging
import discord
import aiosqlite
from discord.ext import commands
from utilities import database
from cogwatch import watch
from discord.ext import tasks
from utilities.heartbeat import bot_status
import time
from help import HelpCommand
from utilities import control
import os
from utilities import api


print(os.cpu_count())
if os.cpu_count() == 24:
    token = config.TEST_TOKEN
else:
    token = config.BOT_TOKEN

class Bot(commands.AutoShardedBot):
    db: aiosqlite.Connection
    api_fetch : False
    user: discord.ClientUser
    owner_ids: list[int]
    
    def __init__(self) -> None:
        super().__init__(
            help_command=HelpCommand(),
            command_prefix=self.get_prefix,
            description="this is a cool bot made for jailbreak trade base, join here: https://discord.gg/tradebase",
            intents=discord.Intents.all(),
        )
        self.owner_ids = [1137565133913202800, 659865209741246514, 1259844955384315987]

    @tasks.loop(seconds=10)
    async def update_latency(self):
        await self.wait_until_ready()
        if not self.is_closed():
            bot_status["latency"] = self.latency * 1000
    
    @watch(path='commands', preload=True)
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        bot_status["status"] = "Running"
        bot_status["start_time"] = time.time()
        control.bot = self
        api.bot = self
        database.bot = self
        await self.update_latency.start()

    async def setup_hook(self) -> None:
        self.db: aiosqlite.Connection = await aiosqlite.connect("./data/database.db")
        if token == config.TEST_TOKEN:
            self.api_fetch = True

        if not self.db:
            raise RuntimeError("Failed connecting to the database.")

        with open("./data/schema.sql") as file:
            await self.db.executescript(file.read())

        try:
            await self.load_extension('jishaku')
        except Exception as e:
            print(f"Failed to load Jishaku: {e}")

    async def start(self) -> None:
        discord.utils.setup_logging(level=logging.INFO)
        await super().start(token, reconnect=True)

    async def get_prefix(self, message: discord.Message, /):
        if message.guild is None:
            return "="
        prefix = await database.get_prefix(self.db)
        if prefix is None:
            await database.set_prefix(self.db, "=")
        return commands.when_mentioned_or(prefix)(self, message)

if __name__ == "__main__":
    bot = Bot()
    bot.run()
