# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned
from typing import Tuple, List

async def fetch_synonyms_antonyms(word: str) -> Tuple[List[str], List[str]]:
    synonyms_url = f"https://api.datamuse.com/words?rel_syn={word}"
    antonyms_url = f"https://api.datamuse.com/words?rel_ant={word}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(synonyms_url) as syn_response, session.get(antonyms_url) as ant_response:
                syn_response.raise_for_status()  # Raise an exception for non-200 status codes
                ant_response.raise_for_status()
                synonyms = [syn['word'] for syn in await syn_response.json()]
                antonyms = [ant['word'] for ant in await ant_response.json()]
        LOGGER.info(f"Successfully fetched synonyms and antonyms for '{word}'")
        return synonyms, antonyms
    except (aiohttp.ClientError, ValueError) as e:
        LOGGER.error(f"Datamuse API error for word '{word}': {e}")
        raise

def setup_syn_handler(app: Client):
    @app.on_message(filters.command(["syn", "synonym"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def synonyms_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /syn")
            return

        # Check if the message is a reply
        if message.reply_to_message and message.reply_to_message.text:
            word = message.reply_to_message.text.strip()
            # Ensure reply contains a single word
            if len(word.split()) != 1:
                await client.send_message(
                    message.chat.id,
                    "**❌ Reply to a message with a single word to get synonyms and antonyms.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.warning(f"Invalid reply format: {word}")
                return
        else:
            # Check if command has a single word
            if len(message.command) <= 1 or len(message.command[1].split()) != 1:
                await client.send_message(
                    message.chat.id,
                    "**❌ Provide a single word to get synonyms and antonyms.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.warning(f"Invalid command format: {message.text}")
                return
            word = message.command[1].strip()

        loading_message = await client.send_message(
            message.chat.id,
            "**Fetching Synonyms and Antonyms...✨**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            synonyms, antonyms = await fetch_synonyms_antonyms(word)
            synonyms_text = ", ".join(synonyms) if synonyms else "No synonyms found"
            antonyms_text = ", ".join(antonyms) if antonyms else "No antonyms found"

            response_text = (
                f"**Synonyms:**\n{synonyms_text}\n\n"
                f"**Antonyms:**\n{antonyms_text}"
            )

            await loading_message.edit(response_text, parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Sent synonyms and antonyms for '{word}' in chat {message.chat.id}")
        except Exception as e:
            LOGGER.error(f"Error processing synonyms/antonyms for word '{word}': {e}")
            # Notify admins
            await notify_admin(client, "/syn", e, message)
            # Send user-facing error message
            await loading_message.edit(
                "**❌ Sorry, Synonym/Antonym API Failed**",
                parse_mode=ParseMode.MARKDOWN
            )
