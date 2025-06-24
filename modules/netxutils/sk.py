# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Use LOGGER and notify_admin
from core import banned_users          # Use banned_users

# Function to verify a Stripe key
async def verify_stripe_key(stripe_key: str) -> str:
    url = "https://api.stripe.com/v1/account"
    headers = {
        "Authorization": f"Bearer {stripe_key}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return "**The Stripe key is live.**"
                else:
                    return "**The Stripe key is dead.**"
    except Exception as e:
        LOGGER.error(f"Error verifying Stripe key: {e}")
        return "**Error verifying Stripe key.**"

# Function to get information about a Stripe key
async def get_stripe_key_info(stripe_key: str) -> str:
    url = "https://api.stripe.com/v1/account"
    headers = {
        "Authorization": f"Bearer {stripe_key}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return "**Unable to retrieve information for the provided Stripe key.**"
                data = await response.json()

        details = (
            f"**Stripe Key Information:**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"**ID:** `{data.get('id', 'N/A')}`\n"
            f"**Email:** `{data.get('email', 'N/A')}`\n"
            f"**Country:** `{data.get('country', 'N/A')}`\n"
            f"**Business Name:** `{data.get('business_name', 'N/A')}`\n"
            f"**Type:** `{data.get('type', 'N/A')}`\n"
            f"**Payouts Enabled:** `{data.get('payouts_enabled', 'N/A')}`\n"
            f"**Details Submitted:** `{data.get('details_submitted', 'N/A')}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )
        return details
    except Exception as e:
        LOGGER.error(f"Error fetching Stripe key info: {e}")
        return "**Error retrieving Stripe key information.**"

async def stripe_key_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    # Await the banned_users check (Motor async)
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
        return

    if len(message.command) <= 1:
        await client.send_message(
            message.chat.id,
            "**❌Please provide a Stripe key. Usage: /sk [Stripe Key]**",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return

    stripe_key = message.command[1]
    fetching_msg = await client.send_message(
        message.chat.id,
        "**Processing Your Request...✨**",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

    try:
        result = await verify_stripe_key(stripe_key)
        await fetching_msg.edit_text(
            result,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except Exception as e:
        LOGGER.error(f"Error in stripe_key_handler: {e}")
        await fetching_msg.edit_text(
            "**Error processing Stripe key verification.**",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        await notify_admin(client, "/sk", e, message)

async def stripe_key_info_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    # Await the banned_users check (Motor async)
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
        return

    if len(message.command) <= 1:
        await client.send_message(
            message.chat.id,
            "**❌Please provide a Stripe key. Usage: /skinfo [Stripe Key]**",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        return

    stripe_key = message.command[1]
    fetching_msg = await client.send_message(
        message.chat.id,
        "**Processing Your Request...✨**",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

    try:
        result = await get_stripe_key_info(stripe_key)
        await fetching_msg.edit_text(
            result,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    except Exception as e:
        LOGGER.error(f"Error in stripe_key_info_handler: {e}")
        await fetching_msg.edit_text(
            "**Error processing Stripe key information.**",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        await notify_admin(client, "/skinfo", e, message)

def setup_sk_handlers(app: Client):
    @app.on_message(filters.command(["sk", ".sk"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stripe_key(client: Client, message: Message):
        await stripe_key_handler(client, message)

    @app.on_message(filters.command(["skinfo", ".skinfo"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stripe_key_info(client: Client, message: Message):
        await stripe_key_info_handler(client, message)
