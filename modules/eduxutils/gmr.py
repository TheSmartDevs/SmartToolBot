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

async def check_grammar(text):
    url = f"http://abirthetech.serv00.net/gmr.php?prompt={text}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                result = await response.json()
                if 'response' not in result:
                    raise ValueError("Invalid API response: 'response' key missing")
                LOGGER.info("Successfully fetched grammar correction")
                return result['response'].strip()
    except Exception as e:
        LOGGER.error(f"Grammar check API error: {e}")
        raise

async def grammar_check(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /gra")
        return

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text.strip()
    else:
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2:
            await client.send_message(
                message.chat.id,
                "**❌ Provide some text or reply to a message to fix grammar.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid command format: {message.text}")
            return
        user_input = user_input[1].strip()

    checking_message = await client.send_message(
        message.chat.id,
        "**Checking And Fixing Grammar Please Wait...✨**",
        parse_mode=ParseMode.MARKDOWN
    )
    try:
        corrected_text = await check_grammar(user_input)
        await checking_message.edit(
            text=f"{corrected_text}",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Grammar correction sent for text in chat {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Error processing grammar check: {e}")
        await notify_admin(client, "/gra", e, message)
        await checking_message.edit(
            text="**❌ Sorry, Grammar Check API Failed**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_gmr_handler(app: Client):
    app.add_handler(
        MessageHandler(
            grammar_check,
            filters.command(["gra"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
