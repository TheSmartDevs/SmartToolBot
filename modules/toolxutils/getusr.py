from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatType
from config import COMMAND_PREFIX
from core import banned_users
from utils import LOGGER
import aiohttp
import aiofiles
import json
import os
from typing import Optional

def setup_getusr_handler(app: Client) -> None:
    @app.on_message(filters.command(["getusers"], prefixes=COMMAND_PREFIX))
    async def get_users(client: Client, message) -> None:
        """Handle /getusers command to fetch bot user data."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        LOGGER.info(f"User {user_id} initiated /getusers command in chat {chat_id}")

        # Check if user is banned
        if banned_users.find_one({"user_id": user_id}):
            LOGGER.warning(f"Banned user {user_id} attempted to use /getusers")
            await client.send_message(
                chat_id,
                "**✘ You're banned from using this bot.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Restrict to private chats only
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            LOGGER.info(f"User {user_id} attempted /getusers in group chat {chat_id}")
            await client.send_message(
                chat_id,
                "**❌ This command is only available in private chats.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Validate command arguments
        args = message.text.split(maxsplit=1)
        if len(args) < 2 or not args[1].strip():
            LOGGER.error(f"User {user_id} provided no bot token")
            await client.send_message(
                chat_id,
                "**❌ Please provide a valid bot token after the command.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        bot_token = args[1].strip()
        loading_message = await client.send_message(
            chat_id,
            "**Fetching user data...**",
            parse_mode=ParseMode.MARKDOWN
        )

        # Validate bot token using Telegram's getMe API
        LOGGER.info(f"Validating bot token ending in {bot_token[-4:]}")
        bot_info = await validate_bot_token(bot_token)
        if bot_info is None:
            LOGGER.error(f"Invalid bot token provided by user {user_id}")
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                "**❌ Invalid Bot Token Provided**",
                parse_mode=ParseMode.MARKDOWN
            )
            await loading_message.delete()
            return

        # Fetch data from API
        LOGGER.info(f"Fetching data for bot {bot_info.get('username', 'N/A')}")
        data = await fetch_bot_data(bot_token)
        if data is None:
            LOGGER.error(f"Failed to fetch user data for user {user_id}")
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                "**❌ Invalid Bot Token Provided**",
                parse_mode=ParseMode.MARKDOWN
            )
            await loading_message.delete()
            return

        # Save and send data
        file_path = f"/tmp/users_{user_id}.json"
        try:
            await save_and_send_data(client, chat_id, data, file_path)
            LOGGER.info(f"Successfully sent user data to user {user_id} in chat {chat_id}")
        except Exception as e:
            LOGGER.exception(f"Error processing data for user {user_id}: {str(e)}")
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                "**❌ Invalid Bot Token Provided**",
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            await loading_message.delete()
            if os.path.exists(file_path):
                os.remove(file_path)
                LOGGER.debug(f"Cleaned up temporary file {file_path}")

async def validate_bot_token(bot_token: str) -> Optional[dict]:
    """Validate bot token using Telegram's getMe API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.telegram.org/bot{bot_token}/getMe") as resp:
                if resp.status != 200:
                    LOGGER.warning(f"Telegram API returned status {resp.status} for bot token")
                    return None
                data = await resp.json()
                if not data.get("ok", False) or "result" not in data:
                    LOGGER.warning(f"Invalid Telegram API response: {data}")
                    return None
                return data["result"]
    except aiohttp.ClientError as e:
        LOGGER.error(f"Telegram API request failed: {str(e)}")
        return None

async def fetch_bot_data(bot_token: str) -> Optional[dict]:
    """Fetch bot user data from the API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.safone.co/tgusers?bot_token={bot_token}") as resp:
                if resp.status != 200:
                    LOGGER.warning(f"API returned status {resp.status} for bot token")
                    return None
                data = await resp.json()
                # Validate expected keys in API response
                if not isinstance(data, dict) or "bot_info" not in data or "stats" not in data:
                    LOGGER.error(f"Invalid API response structure for bot token")
                    return None
                return data
    except aiohttp.ClientError as e:
        LOGGER.error(f"API request failed: {str(e)}")
        return None

async def save_and_send_data(client: Client, chat_id: int, data: dict, file_path: str) -> None:
    """Save data to file and send as document."""
    # Save data to temporary file
    async with aiofiles.open(file_path, mode='w') as f:
        await f.write(json.dumps(data, indent=4))
    LOGGER.debug(f"Saved data to {file_path}")

    # Prepare caption with bot info
    bot_info = data.get("bot_info", {})
    stats = data.get("stats", {})
    
    caption = (
        "**📌 Requested Users**\n"
        "**━━━━━━━━**\n"
        f"**👤 Username:** `{bot_info.get('username', 'N/A')}`\n"
        f"**👥 Total Users:** `{stats.get('total_users', 0)}`\n"
        "**━━━━━━━━**\n"
        "**📂 File contains user & chat IDs.**"
    )

    # Send document
    await client.send_document(
        chat_id=chat_id,
        document=file_path,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN
    )
    LOGGER.info(f"Sent document to chat {chat_id}")
