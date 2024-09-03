import json
import os

SETTINGS_PATH = os.getenv("SETTINGS_PATH", "./guild_settings.json")


def load_guild_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as file:
            return json.load(file)
    else:
        return {"default_prefix": "!", "guilds": {}}


def save_guild_settings(guild_settings):
    with open(SETTINGS_PATH, "w") as file:
        json.dump(guild_settings, file, indent=4)


def get_prefix(bot, message, guild_settings):
    guild_id = str(message.guild.id)
    return (
        guild_settings["guilds"]
        .get(guild_id, {})
        .get("prefix", guild_settings["default_prefix"])
    )


def set_guild_prefix(guild_id, prefix, guild_settings):
    guild_settings["guilds"][guild_id] = guild_settings["guilds"].get(guild_id, {})
    guild_settings["guilds"][guild_id]["prefix"] = prefix
    save_guild_settings(guild_settings)


def set_guild_resources_channel(guild_id, channel_id, guild_settings):
    guild_settings["guilds"][guild_id] = guild_settings["guilds"].get(guild_id, {})
    guild_settings["guilds"][guild_id]["resources_channel"] = channel_id
    save_guild_settings(guild_settings)
