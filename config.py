import tomllib

with open("./data/config.toml", "rb") as file:
    config = tomllib.load(file)

BOT_TOKEN = config["bot"]["config"]["token"]