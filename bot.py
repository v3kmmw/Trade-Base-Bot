import config
import logging
import discord
import aiosqlite
from discord.ext import commands
from utilities import database
from cogwatch import watch

class Bot(commands.AutoShardedBot):
    db: aiosqlite.Connection
    user: discord.ClientUser
    owner_ids: list[int]
    
    def __init__(self) -> None:
        super().__init__(
            help_command=None,
            command_prefix=self.get_prefix,
            description="this is a cool bot made for jailbreak trade base, join here: https://discord.gg/gwBbM6BrnP",
            intents=discord.Intents.all(),
        )
        self.owner_ids = [1137565133913202800]
    
    @watch(path='commands', preload=True)
    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def setup_hook(self) -> None:
        self.db: aiosqlite.Connection = await aiosqlite.connect("./data/database.db")

        if not self.db:
            raise RuntimeError("Failed connecting to the database.")

        with open("./data/schema.sql") as file:
            await self.db.executescript(file.read())

        # Load Jishaku extension
        try:
            await self.load_extension('jishaku')
        except Exception as e:
            print(f"Failed to load Jishaku: {e}")

    async def start(self) -> None:
        discord.utils.setup_logging(level=logging.INFO)
        await super().start(config.BOT_TOKEN, reconnect=True)

    async def get_prefix(self, message: discord.Message, /):
        if message.guild is None:
            return "="
        prefix = await database.get_prefix(self.db, message.guild.id)
        if prefix is None:
            await database.set_prefix(self.db, message.guild, "=")
        return prefix if prefix else "="

if __name__ == "__main__":
    bot = Bot()
    bot.run()
