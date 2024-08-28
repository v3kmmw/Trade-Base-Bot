import tomllib

with open("./data/config.toml", "rb") as file:
    config = tomllib.load(file)

BOT_TOKEN = config["bot"]["config"]["token"]
OPENAIKEY = config["bot"]['config']["openaikey"]
TEST_TOKEN = config["bot"]["config"]["test_token"]
LOG_CHANNEL = config["bot"]["config"]["log_channel"]
AUTOMOD_EXCEPTION_CHANNELS = config["bot"]["config"]["automodexemptchannels"]
AUTOMOD_EXCEPTION_USERS = config["bot"]["config"]["automodexemptusers"]
R2_ENDPOINT_URL = config['bot']['config']['r2_endpoint_url']
R2_BUCKET_NAME = config["bot"]["config"]["r2_bucket_name"]
R2_ACCESS_KEY = config["bot"]["config"]["r2_access_key"]
R2_SECRET_KEY = config["bot"]["config"]["r2_secret_key"]