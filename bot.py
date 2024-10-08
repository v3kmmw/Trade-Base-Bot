import config
import logging
import discord
import aiosqlite
from discord.ext import commands
from utilities import database
from cogwatch import watch
from discord.ext import tasks
from utilities import heartbeat
import time
from help import HelpCommand
from utilities import control
import os
from utilities import api
import psutil
import datetime
import threading
if os.cpu_count() > 8:
    token = config.TEST_TOKEN
else:
    token = config.BOT_TOKEN

def start_api():
    from utilities import api
    api.start()

def start_control_panel():
    from utilities import control
    control.start()

def start_heartbeat():
    from utilities import heartbeat
    heartbeat.start()

class Bot(commands.AutoShardedBot):
    db: aiosqlite.Connection
    api_fetch : False
    user: discord.ClientUser
    testing: False
    owner_ids: list[int]
    
    def __init__(self) -> None:
        super().__init__(
            help_command=HelpCommand(),
            command_prefix=self.get_prefix,
            description="this is a cool bot made for jailbreak trade base, join here: https://discord.gg/tradebase",
            intents=discord.Intents.all(),
        )
        self.owner_ids = [1137565133913202800, 659865209741246514, 1259844955384315987]
    
    @watch(path='commands', preload=True)
    async def on_ready(self):
        print(f"Logged in as {self.user}")
        log_channel = config.LOG_CHANNEL
        channel = await self.fetch_channel(log_channel)
        boot_time_timestamp = psutil.boot_time()
        boot_time = datetime.datetime.fromtimestamp(boot_time_timestamp)
        current_time = datetime.datetime.now()
        uptime = current_time - boot_time
        days, seconds = divmod(uptime.total_seconds(), 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        formatted_uptime = f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"
        prefix = await database.get_prefix(self.db)
        activity = discord.Activity(type=discord.ActivityType.watching, name=f"{prefix}commands")
        await self.change_presence(activity=activity)
        from main import script_started_at_str
        await channel.send(f"Bot started\nServer uptime: {formatted_uptime}\nScript started at: {script_started_at_str}")
        api_thread = threading.Thread(target=start_api)
        api_thread.start()

    # Start the heartbeat server in another separate thread
        heartbeat_thread = threading.Thread(target=start_heartbeat)
        heartbeat_thread.start()

    # Start the control panel in a separate thread
        control_panel_thread = threading.Thread(target=start_control_panel)
        control_panel_thread.start()
        control.bot = self
        api.bot = self
        database.bot = self
        heartbeat.bot = self

    async def setup_hook(self) -> None:
        self.db: aiosqlite.Connection = await aiosqlite.connect("./data/database.db")
        if token == config.TEST_TOKEN:
            self.testing = True

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
