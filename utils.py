import hashlib
import requests
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import discord
import asyncio


def normalize_url(url):
    parsed_url = urlparse(url)
    query_params = dict(parse_qsl(parsed_url.query))

    query_params.pop("utm_source", None)
    query_params.pop("utm_medium", None)

    normalized_query = urlencode(query_params)
    normalized_url = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            normalized_query,
            parsed_url.fragment,
        )
    )

    return normalized_url


def hash_pdf(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            pdf_content = response.content
            pdf_hash = hashlib.sha256(pdf_content).hexdigest()
            print(f"hashed PDF: {pdf_hash}")
            return pdf_hash
        else:
            print(f"failed to fetch PDF: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Fetch error: {e}")
        return None


def is_duplicate(resource, resources):
    for existing_resource in resources:
        if resource["type"] == existing_resource["type"]:
            if resource["type"] == "pdf" and resource.get(
                "hash"
            ) == existing_resource.get("hash"):
                print(f"duplicate PDF: {resource['name']}")
                return True
            if resource["type"] == "link" and resource.get(
                "url"
            ) == existing_resource.get("url"):
                print(f"duplicate link: {resource['url']}")
                return True
    return False


async def ask_for_description(channel, author, resource_detail, bot):
    prompt_message = await channel.send(
        f"{author.mention}, provide a description for `{resource_detail}`. "
        f"type `cancel-upload` to cancel upload of this resource. 5 minutes to respond."
    )

    def check(m):
        return m.author == author and m.channel == channel

    try:
        description_message = await bot.wait_for("message", timeout=300.0, check=check)
        await prompt_message.delete()

        if description_message.content.lower() == "cancel-upload":
            cancel_message = await channel.send(f"{author.mention}, upload canceled.")
            await asyncio.sleep(10)
            await cancel_message.delete()
            return "CANCEL_UPLOAD"

        return description_message.content
    except asyncio.TimeoutError:
        await prompt_message.delete()
        timeout_message = await channel.send(
            f"{author.mention}, timeout. No description added."
        )
        await asyncio.sleep(10)
        await timeout_message.delete()
        return "no description provided."
