import tomllib

with open("./data/config.toml", "rb") as file:
    config = tomllib.load(file)

BOT_TOKEN = config["bot"]["config"]["token"]
TEST_TOKEN = config["bot"]["config"]["test_token"]
LOG_CHANNEL = config["bot"]["config"]["log_channel"]