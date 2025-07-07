# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, DOMAIN_API_KEY, DOMAIN_API_URL, DOMAIN_CHK_LIMIT, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

async def format_date(date_str):
    return date_str

async def get_domain_info(domain: str) -> str:
    params = {
        "apiKey": DOMAIN_API_KEY,
        "domainName": domain,
        "outputFormat": "JSON"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(DOMAIN_API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                LOGGER.info(f"Response for domain {domain}: {data}")
                if data.get("WhoisRecord"):
                    whois_record = data["WhoisRecord"]
                    status = whois_record.get("status", "Unknown").lower()
                    data_error = whois_record.get("dataError", "")
                    registrar = whois_record.get("registrarName", "Unknown")
                    registration_date = await format_date(whois_record.get("createdDate", "Unknown"))
                    expiration_date = await format_date(whois_record.get("expiresDate", "Unknown"))

                    if status == "available" or data_error == "MISSING_WHOIS_DATA" or not whois_record.get("registryData"):
                        return f"**✅ {domain}**: Available for registration!"
                    else:
                        return (
                            f"**🔒 {domain}**: Already registered.\n"
                            f"**Registrar:** `{registrar}`\n"
                            f"**Registration Date:** `{registration_date}`\n"
                            f"**Expiration Date:** `{expiration_date}`"
                        )
                else:
                    return f"**✅ {domain}**: Available for registration!"
    except aiohttp.ClientError as e:
        LOGGER.error(f"Failed to fetch info for domain {domain}: {e}")
        await notify_admin(None, f"{COMMAND_PREFIX}dmn", e, None)
        return f"**❌ Sorry Bro Domain API Dead**"
    except Exception as e:
        LOGGER.error(f"Exception occurred while fetching info for domain {domain}: {e}")
        await notify_admin(None, f"{COMMAND_PREFIX}dmn", e, None)
        return f"**❌ Sorry Bro Domain Check API Dead**"

async def domain_info_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY)
        return

    if len(message.command) < 2:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Please provide at least one valid domain name.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    domains = message.command[1:]
    if len(domains) > DOMAIN_CHK_LIMIT:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"**❌ You can check up to {DOMAIN_CHK_LIMIT} domains at a time.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    progress_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Fetching domain information...✨**",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        results = await asyncio.gather(*[get_domain_info(domain) for domain in domains], return_exceptions=True)

        result_message = []
        for domain, result in zip(domains, results):
            if isinstance(result, Exception):
                LOGGER.error(f"Error processing domain {domain}: {result}")
                await notify_admin(client, f"{COMMAND_PREFIX}dmn", result, message)
                result_message.append(f"**❌ {domain}**: Failed to check domain")
            else:
                result_message.append(result)

        result_message = "\n\n".join(result_message)

        if all("✅" in result for result in result_message.split("\n\n")):
            await progress_message.edit_text(result_message, parse_mode=ParseMode.MARKDOWN)
            return

        if message.from_user:
            user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
            user_info = f"\n**Domain Info Grab By:** [{user_full_name}](tg://user?id={message.from_user.id})"
        else:
            group_name = message.chat.title or "this group"
            group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
            user_info = f"\n**Domain Info Grab By:** [{group_name}]({group_url})"

        result_message += user_info

        await progress_message.edit_text(f"**Domain Check Results:**\n\n{result_message}", parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        LOGGER.error(f"Error processing domain check: {e}")
        await notify_admin(client, f"{COMMAND_PREFIX}dmn", e, message)
        await progress_message.edit_text(
            "**❌ Sorry Bro Domain Check API Dead**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_dmn_handlers(app: Client):
    @app.on_message(filters.command(["dmn", ".dmn"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def domain_info(client: Client, message: Message):
        await domain_info_handler(client, message)
