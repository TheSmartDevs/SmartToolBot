# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin from utils

# Configure logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def get_ip_info(ip: str) -> str:
    url = f"https://ipinfo.io/{ip}/json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise an exception for non-200 status codes
                data = await response.json()
    
        ip = data.get("ip", "Unknown")
        asn = data.get("org", "Unknown")
        isp = data.get("org", "Unknown")
        country = data.get("country", "Unknown")
        city = data.get("city", "Unknown")
        timezone = data.get("timezone", "Unknown")

        # Simulated IP fraud score and risk level for demonstration
        fraud_score = 0
        risk_level = "low" if fraud_score < 50 else "high"

        details = (
            f"**YOUR IP INFORMATION 🌐**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"**IP:** `{ip}`\n"
            f"**ASN:** `{asn}`\n"
            f"**ISP:** `{isp}`\n"
            f"**Country City:** `{country} {city}`\n"
            f"**Timezone:** `{timezone}`\n"
            f"**IP Fraud Score:** `{fraud_score}`\n"
            f"**Risk LEVEL:** `{risk_level} Risk`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

        return details
    except aiohttp.ClientError as e:
        logger.error(f"Failed to fetch IP info for {ip}: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}ip", e, None)
        return "Invalid IP address or API error"
    except Exception as e:
        logger.error(f"Unexpected error fetching IP info for {ip}: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}ip", e, None)
        return "Invalid IP address or API error"

async def ip_info_handler(client: Client, message: Message):
    if len(message.command) <= 1:
        await client.send_message(
            message.chat.id,
            "**❌ Please provide a single IP address.**",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return

    ip = message.command[1]
    fetching_msg = await client.send_message(
        message.chat.id,
        "**Fetching IP Info Please Wait.....✨**",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

    try:
        details = await get_ip_info(ip)
        if details.startswith("Invalid"):
            raise Exception("Failed to retrieve IP information")

        if message.from_user:
            user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
            user_info = f"\n**Ip-Info Grab By:** [{user_full_name}](tg://user?id={message.from_user.id})"
        else:
            group_name = message.chat.title or "this group"
            group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
            user_info = f"\n**Ip-Info Grab By:** [{group_name}]({group_url})"

        details += user_info

        await fetching_msg.edit_text(
            details,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error processing IP info for {ip}: {e}")
        # Notify admins
        await notify_admin(client, f"{COMMAND_PREFIX}ip", e, message)
        # Send user-facing error message
        await fetching_msg.edit_text(
            "**❌ Sorry Bro IP Info API Dead**",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

def setup_ip_handlers(app: Client):
    @app.on_message(filters.command(["ip", ".ip"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def ip_info(client: Client, message: Message):
        await ip_info_handler(client, message)
