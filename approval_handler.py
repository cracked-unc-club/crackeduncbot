import discord
import asyncio
import json


async def handle_reaction(
    payload,
    bot,
    guild_settings,
    resources,
    pending_resources,
    save_path,
    upload_to_cloudflare_kv,
):
    if payload.user_id == bot.user.id:
        return

    guild_id = str(payload.guild_id)
    approval_channel_id = (
        guild_settings["guilds"].get(guild_id, {}).get("approval_channel")
    )
    if payload.channel_id != approval_channel_id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)
    if not member.guild_permissions.manage_messages:
        return

    approval_channel = bot.get_channel(payload.channel_id)
    if not approval_channel:
        return

    try:
        message = await approval_channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return

    reaction = payload.emoji.name
    if reaction not in ["✅", "❌"]:
        return

    resource = next(
        (
            res
            for res in pending_resources
            if res.get("approval_message_id") == message.id
        ),
        None,
    )
    if not resource:
        return

    original_channel = bot.get_channel(resource["original_channel_id"])
    user_message = None

    if reaction == "✅":
        print("✅ reaction detected, attempting to upload to Cloudflare...")
        resources.append(resource)

        with open(save_path, "w") as file:
            json.dump(resources, file, indent=4)

        upload_success = upload_to_cloudflare_kv(save_path)

        if upload_success:
            print("Upload to Cloudflare succeeded, sending approval message...")
            await approval_channel.send(
                f"resource `{resource['name'] if resource['type'] == 'pdf' else resource['url']}` approved and uploaded."
            )
            user_message = await original_channel.send(
                f"resource `{resource['name'] if resource['type'] == 'pdf' else resource['url']}` has been approved and uploaded."
            )
        else:
            print("Upload to Cloudflare failed, no message sent.")
            resources.remove(resource)  # Rollback on failure

    elif reaction == "❌":
        print("❌ reaction detected, sending rejection message...")
        await approval_channel.send(
            f"resource `{resource['name'] if resource['type'] == 'pdf' else resource['url']}` rejected."
        )
        user_message = await original_channel.send(
            f"resource `{resource['name'] if resource['type'] == 'pdf' else resource['url']}` has been rejected."
        )

    if user_message:
        await asyncio.sleep(10)
        await user_message.delete()

    pending_resources.remove(resource)
