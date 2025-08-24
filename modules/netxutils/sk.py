#Copyright @ISmartCoder
#Updates Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

async def verify_stripe_key(stripe_key: str) -> str:
    url = "https://api.stripe.com/v1/account"
    headers = {
        "Authorization": f"Bearer {stripe_key}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return "Live ✅"
                else:
                    return "SK KEY REVOKED ❌"
    except Exception as e:
        LOGGER.error(f"Error verifying Stripe key: {e}")
        return "SK KEY REVOKED ❌"

async def get_stripe_key_info(stripe_key: str) -> str:
    url = "https://api.stripe.com/v1/account"
    balance_url = "https://api.stripe.com/v1/balance"
    headers = {
        "Authorization": f"Bearer {stripe_key}"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return "SK KEY REVOKED ❌"
                data = await response.json()
            async with session.get(balance_url, headers=headers) as balance_response:
                balance_data = await balance_response.json() if balance_response.status == 200 else {}
        available_balance = balance_data.get("available", [{}])[0].get("amount", 0) / 100 if balance_data else 0
        currency = balance_data.get("available", [{}])[0].get("currency", "N/A").upper() if balance_data else "N/A"
        details = (
            f"**み SK Key Authentication ↝ Successful ✅**\n"
            f"**━━━━━━━━━━━━━━━━━━━━━━**\n"
            f"**⊗ SK Key Status** ↝ {'Live ✅' if data.get('charges_enabled') else 'Restricted ❌'}\n"
            f"**⊗ Account ID** ↝ {data.get('id', 'N/A')}\n"
            f"**⊗ Email** ↝ {data.get('email', 'N/A')}\n"
            f"**⊗ Business Name** ↝ {data.get('business_profile', {}).get('name', 'N/A')}\n"
            f"**⊗ Charges Enabled** ↝ {'Yes ✅' if data.get('charges_enabled') else 'No ❌'}\n"
            f"**⊗ Payouts Enabled** ↝ {'Yes ✅' if data.get('payouts_enabled') else 'No ❌'}\n"
            f"**⊗ Account Type** ↝ {data.get('type', 'N/A').capitalize()}\n"
            f"**⊗ Balance** ↝ {available_balance} {currency}\n"
            f"**━━━━━━━━━━━━━━━━━━━━━━**\n"
            f"**⌁ Thank You For Using Smart Tool ↯**"
        )
        return details
    except Exception as e:
        LOGGER.error(f"Error fetching Stripe key info: {e}")
        return "SK KEY REVOKED ❌"

async def stripe_key_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY)
        return

    if len(message.command) <= 1:
        await client.send_message(
            message.chat.id,
            "**❌ Please provide a Stripe key. Usage: /sk [Stripe Key]**",
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
        if result == "SK KEY REVOKED ❌":
            user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={user_id})"
            await fetching_msg.edit_text(
                f"⊗ **SK ➺** `{stripe_key}`\n"
                f"⊗ **Response: SK KEY REVOKED ❌**\n"
                f"⊗ **Checked By ➺** {user_link}",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        else:
            await fetching_msg.edit_text(
                result,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    except Exception as e:
        LOGGER.error(f"Error in stripe_key_handler: {e}")
        user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={user_id})"
        await fetching_msg.edit_text(
            f"⊗ **SK ➺** `{stripe_key}`\n"
            f"⊗ **Response: SK KEY REVOKED ❌**\n"
            f"⊗ **Checked By ➺** {user_link}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        await notify_admin(client, "/sk", e, message)

async def stripe_key_info_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY)
        return

    if len(message.command) <= 1:
        await client.send_message(
            message.chat.id,
            "**❌ Please provide a Stripe key. Usage: /skinfo [Stripe Key]**",
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
        if result == "SK KEY REVOKED ❌":
            user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={user_id})"
            await fetching_msg.edit_text(
                f"⊗ **SK ➺** `{stripe_key}`\n"
                f"⊗ **Response: SK KEY REVOKED ❌**\n"
                f"⊗ **Checked By ➺** {user_link}",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        else:
            await fetching_msg.edit_text(
                result,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    except Exception as e:
        LOGGER.error(f"Error in stripe_key_info_handler: {e}")
        user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={user_id})"
        await fetching_msg.edit_text(
            f"⊗ **SK ➺** `{stripe_key}`\n"
            f"⊗ **Response: SK KEY REVOKED ❌**\n"
            f"⊗ **Checked By ➺** {user_link}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
        await notify_admin(client, "/skinfo", e, message)

def setup_sk_handlers(app: Client):
    @app.on_message(filters.command(["sk"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stripe_key(client: Client, message: Message):
        await stripe_key_handler(client, message)

    @app.on_message(filters.command(["skinfo"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stripe_key_info(client: Client, message: Message):
        await stripe_key_info_handler(client, message)
