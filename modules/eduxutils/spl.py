# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

async def check_spelling(word):
    url = f"https://abirthetech.serv00.net/spl.php?prompt={word}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                result = await response.json()
                if 'response' not in result:
                    raise ValueError("Invalid API response: 'response' key missing")
                LOGGER.info(f"Successfully fetched spelling correction for '{word}'")
                return result['response'].strip()
    except Exception as e:
        LOGGER.error(f"Spelling check API error for word '{word}': {e}")
        raise

async def spell_check(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /spell")
        return

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text.strip()
        if len(user_input.split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Reply to a message with a single word to check spelling.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid reply format: {user_input}")
            return
    else:
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
        await notify_admin(client, "/spell", e, message)
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
