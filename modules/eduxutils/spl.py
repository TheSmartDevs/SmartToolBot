# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

async def check_spelling(word):
    url = f"https://abirthetech.serv00.net/spl.php?prompt={word}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise an exception for non-200 status codes
                result = await response.json()
                if 'response' not in result:
                    raise ValueError("Invalid API response: 'response' key missing")
                LOGGER.info(f"Successfully fetched spelling correction for '{word}'")
                return result['response'].strip()
    except Exception as e:
        LOGGER.error(f"Spelling check API error for word '{word}': {e}")
        raise

async def spell_check(client: Client, message: Message):
    # Check if user is banned
    user_id = message.from_user.id if message.from_user else None
    # Await for MotorDB (async)
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /spell")
        return

    # Check if the message is a reply
    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text.strip()
        # Ensure reply contains a single word
        if len(user_input.split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Reply to a message with a single word to check spelling.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid reply format: {user_input}")
            return
    else:
        # Check if command has a single word
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2 or len(user_input[1].split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Provide a single word to check spelling.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid command format: {message.text}")
            return
        user_input = user_input[1].strip()

    # Proceed with spell check
    checking_message = await client.send_message(
        message.chat.id,
        "**Checking Spelling...✨**",
        parse_mode=ParseMode.MARKDOWN
    )
    try:
        corrected_word = await check_spelling(user_input)
        await checking_message.edit(
            text=f"`{corrected_word}`",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Spelling correction sent for '{user_input}' in chat {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Error processing spelling check for word '{user_input}': {e}")
        # Notify admins
        await notify_admin(client, "/spell", e, message)
        # Send user-facing error message
        await checking_message.edit(
            text="**❌ Sorry, Spelling Check API Failed**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_spl_handler(app: Client):
    app.add_handler(
        MessageHandler(
            spell_check,
            filters.command(["spell"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
