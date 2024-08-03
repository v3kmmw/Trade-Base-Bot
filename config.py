import tomllib

with open("./data/config.toml", "rb") as file:
    config = tomllib.load(file)

BOT_TOKEN = config["bot"]["config"]["token"]
OPENAIKEY = config["bot"]['config']["openaikey"]
TEST_TOKEN = config["bot"]["config"]["test_token"]
LOG_CHANNEL = config["bot"]["config"]["log_channel"]
AUTOMOD_EXCEPTION_CHANNELS = config["bot"]["config"]["automodexemptchannels"]
AUTOMOD_EXCEPTION_USERS = config["bot"]["config"]["automodexemptusers"]