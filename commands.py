import discord
from discord.ext import commands
from guild_settings import (
    save_guild_settings,
    set_guild_prefix,
    set_guild_resources_channel,
)
from datetime import datetime


def setup_commands(bot, bot_start_time, guild_settings):
    @bot.command(name="status")
    @commands.has_permissions(manage_messages=True)
    async def status(ctx):
        print("status command called")
        latency = round(bot.latency * 1000, 2)
        server_count = len(bot.guilds)
        user_count = sum(g.member_count for g in bot.guilds)
        uptime = datetime.utcnow() - bot_start_time
        status_message = (
            f"**Bot Status**\n\n"
            f"> Latency: {latency}ms\n"
            f"> Servers: {server_count}\n"
            f"> Users: {user_count}\n"
            f"> Uptime: {str(uptime).split('.')[0]}\n\n"
        )
        website_url = "https://crackedunc.club/"
        status_message += f"Visit the [site]({website_url})"
        await ctx.send(status_message)

    @bot.command(name="setresourcechannel")
    @commands.has_permissions(manage_messages=True)
    async def set_resource_channel(ctx, channel: discord.TextChannel):
        print("setresourcechannel command called")
        guild_id = str(ctx.guild.id)
        set_guild_resources_channel(guild_id, channel.id, guild_settings)
        await ctx.send(f"Resource channel set to {channel.mention}")

    @bot.command(name="setapprovalchannel")
    @commands.has_permissions(manage_messages=True)
    async def set_approval_channel(ctx, channel: discord.TextChannel):
        print("setapprovalchannel command called")
        guild_id = str(ctx.guild.id)
        guild_settings["guilds"][guild_id] = guild_settings["guilds"].get(guild_id, {})
        guild_settings["guilds"][guild_id]["approval_channel"] = channel.id
        save_guild_settings(guild_settings)
        await ctx.send(f"Approval channel set to {channel.mention}")

    @bot.command(name="setprefix")
    @commands.has_permissions(manage_messages=True)
    async def set_prefix(ctx, new_prefix: str):
        print("setprefix command called")
        guild_id = str(ctx.guild.id)
        set_guild_prefix(guild_id, new_prefix, guild_settings)
        await ctx.send(f"Prefix set to `{new_prefix}`")

    @bot.command(name="help")
    async def help_command(ctx):
        print("help command called")
        guild_id = str(ctx.guild.id)
        prefix = guild_settings["guilds"].get(guild_id, {}).get("prefix", "!")
        help_message = (
            f"**Bot Help**\n\n"
            f"`{prefix}status` - Show bot status and link.\n"
            f"`{prefix}setresourcechannel <channel>` - Set resource channel.\n"
            f"`{prefix}setapprovalchannel <channel>` - Set approval channel.\n"
            f"`{prefix}setprefix <new_prefix>` - Change command prefix.\n"
            f"`{prefix}bugreport <description>` - Submit a bug report.\n"
            f"`{prefix}help` - Show this message."
        )
        await ctx.send(help_message)

    @bot.command(name="bugreport")
    async def bugreport(ctx, *, description: str):
        print("bugreport command called")
        dev_guild_id = 1151350764854317076
        bug_report_channel_id = 1279668175188787230

        bug_report_channel = bot.get_channel(bug_report_channel_id)
        if bug_report_channel:
            report_message = (
                f"\u200B\n**report** from `{ctx.guild.name}`\n"
                f"**user**: `{ctx.author}` (ID: `{ctx.author.id}`)\n"
                f"**channel**: `{ctx.channel.name}` (ID: `{ctx.channel.id}`)\n"
                f"**desc**:\n`{description}`"
            )
            await bug_report_channel.send(report_message)
            await ctx.send(
                "thanks for the bug report. for further assistance contact us dev at `contact@crackedunc.club`."
            )
        else:
            await ctx.send(
                "bug reporting is restricted to specific servers. this shouldnt trigger, please contact me at `contact@crackedunc.club`."
            )
