from utils import hash_pdf, normalize_url, is_duplicate, ask_for_description
import asyncio


async def process_new_resources(
    message, guild_settings, resources, pending_resources, bot
):
    new_resources = []
    duplicate_resources = []

    for attachment in message.attachments:
        if attachment.filename.endswith(".pdf"):
            pdf_hash = hash_pdf(attachment.url)
            if pdf_hash:
                pdf_info = {
                    "type": "pdf",
                    "url": attachment.url,
                    "name": attachment.filename,
                    "author": message.author.name,
                    "time": str(message.created_at),
                    "hash": pdf_hash,
                    "description": None,
                    "original_message_id": message.id,
                    "original_channel_id": message.channel.id,
                }
                if not is_duplicate(pdf_info, resources):
                    description = await ask_for_description(
                        message.channel,
                        message.author,
                        attachment.filename,
                        bot,
                    )
                    if description == "CANCEL_UPLOAD":
                        continue
                    pdf_info["description"] = description
                    pending_resources.append(pdf_info)  # Add to pending list
                    new_resources.append(pdf_info)
                    print(f"new PDF pending approval: {attachment.filename}")
                else:
                    duplicate_resources.append({"type": "pdf", "url": attachment.url})

    for word in message.content.split():
        if word.startswith("http://") or word.startswith("https://"):
            normalized_url = normalize_url(word)
            link_info = {
                "type": "link",
                "url": normalized_url,
                "author": message.author.name,
                "time": str(message.created_at),
                "description": None,
                "original_message_id": message.id,
                "original_channel_id": message.channel.id,
            }
            if not is_duplicate(link_info, resources):
                description = await ask_for_description(
                    message.channel, message.author, normalized_url, bot
                )
                if description == "CANCEL_UPLOAD":
                    continue
                link_info["description"] = description
                pending_resources.append(link_info)  # Add to pending list
                new_resources.append(link_info)
                print(f"new link pending approval: {normalized_url}")
            else:
                duplicate_resources.append({"type": "link", "url": normalized_url})

    if duplicate_resources:
        duplicate_names = "\n".join(
            [f"- `{res['url']}`" for res in duplicate_resources]
        )
        print(f"duplicate resources detected: {duplicate_names}")
        duplicate_message = await message.channel.send(
            f"**duplicate resources detected:**\n{duplicate_names}"
        )
        await asyncio.sleep(10)
        await duplicate_message.delete()

    approval_channel_id = (
        guild_settings["guilds"].get(str(message.guild.id), {}).get("approval_channel")
    )
    if new_resources and approval_channel_id:
        approval_channel = bot.get_channel(approval_channel_id)
        if approval_channel:
            for res in new_resources:
                resource_type = res["type"]
                resource_name = res["name"] if resource_type == "pdf" else res["url"]
                original_message_link = f"https://discord.com/channels/{message.guild.id}/{res['original_channel_id']}/{res['original_message_id']}"
                approval_message = await approval_channel.send(
                    f"\u200B\nnew {resource_type} added: `{resource_name}`\n"
                    f"author: `{res['author']}`\n"
                    f"desc: `{res['description']}`\n"
                    f"[message]({original_message_link})\n\n"
                    "✅ to approve, ❌ to reject"
                )
                res["approval_message_id"] = approval_message.id
                await approval_message.add_reaction("✅")
                await approval_message.add_reaction("❌")
