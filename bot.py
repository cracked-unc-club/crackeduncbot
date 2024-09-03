import discord
from discord.ext import commands
import os
from datetime import datetime
from env_loader import load_environment_variables
from guild_settings import load_guild_settings, get_prefix
from commands import setup_commands
from events import setup_events
import json
import requests

load_environment_variables()

bot_start_time = datetime.utcnow()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SAVE_PATH = os.getenv("SAVE_PATH", "./resources.json")

CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_NAMESPACE_ID = os.getenv("CLOUDFLARE_NAMESPACE_ID")

if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r") as file:
        resources = json.load(file)
else:
    resources = []


guild_settings = load_guild_settings()

pending_resources = []

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(
    command_prefix=lambda bot, message: get_prefix(bot, message, guild_settings),
    intents=intents,
    help_command=None,
)


def upload_to_cloudflare_kv(save_path):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/storage/kv/namespaces/{CLOUDFLARE_NAMESPACE_ID}/values/resources.json"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        with open(save_path, "rb") as f:
            response = requests.put(url, headers=headers, data=f.read())

        if response.status_code == 200:
            print("Successfully uploaded resources.json to Cloudflare Workers KV.")
            return True
        else:
            print(
                f"Failed to upload to Cloudflare KV: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        print(f"An error occurred during upload: {e}")
        return False


setup_commands(bot, bot_start_time, guild_settings)
setup_events(
    bot,
    guild_settings,
    resources,
    pending_resources,
    SAVE_PATH,
    upload_to_cloudflare_kv,
)

bot.run(DISCORD_BOT_TOKEN)
