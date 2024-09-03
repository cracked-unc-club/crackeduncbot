import discord
from discord.ext import commands
from approval_handler import handle_reaction
from resource_manager import process_new_resources
from guild_settings import save_guild_settings, get_prefix


def setup_events(
    bot,
    guild_settings,
    resources,
    pending_resources,
    save_path,
    upload_to_cloudflare_kv,
):

    @bot.event
    async def on_ready():
        print(f"logged in as {bot.user}")

    @bot.event
    async def on_guild_join(guild):
        guild_id = str(guild.id)
        guild_settings["guilds"][guild_id] = {
            "prefix": guild_settings["default_prefix"],
            "resources_channel": None,
            "approval_channel": None,
        }
        save_guild_settings(guild_settings)

        welcome_message = (
            f"I'm {bot.user.name}.\n"
            f"default prefix is `{guild_settings['default_prefix']}`.\n"
            f"use `{guild_settings['default_prefix']}setprefix` to change it.\n\n"
            f"`{guild_settings['default_prefix']}setresourcechannel` to set the channel where I'll monitor for PDFs and links.\n\n"
            f"`{guild_settings['default_prefix']}setapprovalchannel` to set the channel where you'll approve the PDFs and links."
        )
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send(welcome_message)
                break

    @bot.event
    async def on_message(message):
        await bot.process_commands(message)

        if message.author == bot.user:
            return

        if bot.user.mentioned_in(message) and not message.mention_everyone:
            guild_id = str(message.guild.id)
            prefix = guild_settings["guilds"].get(guild_id, {}).get("prefix", "!")
            await message.channel.send(
                f"current prefix: `{prefix}`\n" f"bug report: `!bugreport`"
            )

        if message.content.lower().startswith("!bugreport"):
            description = message.content[len("!bugreport") :].strip()

            if description:
                bug_report_channel_id = 1279668175188787230

                bug_report_channel = bot.get_channel(bug_report_channel_id)
                if bug_report_channel:
                    report_message = (
                        f"\u200B\n**bug report** from `{message.guild.name}`\n"
                        f"**user**: `{message.author}` (ID: `{message.author.id})`\n"
                        f"**channel**: `{message.channel.name}` (ID: `{message.channel.id})`\n"
                        f"**description**:\n`{description}`"
                    )
                    await bug_report_channel.send(report_message)
                    await message.channel.send(
                        "thanks for the bug report. for further assistance contact the dev at `contact@crackedunc.club`"
                    )
                else:
                    await message.channel.send(
                        "bug reporting is restricted to specific servers, this shouldn't trigger, please contact me at `contact@crackedunc.club`"
                    )
            else:
                await message.channel.send(
                    "please provide a description with your bug report, e.g., `!bugreport <description>`."
                )

            return

        guild_id = str(message.guild.id)
        resources_channel_id = (
            guild_settings["guilds"].get(guild_id, {}).get("resources_channel")
        )

        if resources_channel_id and message.channel.id == resources_channel_id:
            await process_new_resources(
                message, guild_settings, resources, pending_resources, bot
            )

    @bot.event
    async def on_raw_reaction_add(payload):
        await handle_reaction(
            payload,
            bot,
            guild_settings,
            resources,
            pending_resources,
            save_path,
            upload_to_cloudflare_kv,
        )

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            prefix = get_prefix(bot, ctx.message, guild_settings)
            await ctx.send(
                f"Command not found. Type `{prefix}help` for a list of commands."
            )
        elif isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"Error: missing required argument `{error.param.name}`. Provide all necessary information."
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                "Error: invalid argument provided. Check your input and try again."
            )
        else:
            raise error
