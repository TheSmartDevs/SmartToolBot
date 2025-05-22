# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin from utils

# Configure logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def fetch_pronunciation_info(word):
    url = f"https://abirthetech.serv00.net/pr.php?prompt={word}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise an exception for non-200 status codes
                result = await response.json()
                pronunciation_info = result['response']
                return {
                    "word": pronunciation_info['Word'],
                    "breakdown": pronunciation_info['- Breakdown'],
                    "pronunciation": pronunciation_info['- Pronunciation'],
                    "stems": pronunciation_info['Word Stems'].split(", "),
                    "definition": pronunciation_info['Definition'],
                    "audio_link": pronunciation_info['Audio']
                }
    except (aiohttp.ClientError, ValueError, KeyError) as e:
        logger.error(f"Pronunciation API error for word '{word}': {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}prn", e, None)
        return None

async def pronunciation_check(client: Client, message: Message):
    # Check if the message is a reply
    if message.reply_to_message and message.reply_to_message.text:
        word = message.reply_to_message.text.strip()
        # Ensure reply contains a single word
        if len(word.split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Reply to a message with a single word to check pronunciation.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    else:
        # Check if command has a single word
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2 or len(user_input[1].split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Provide a single word to check pronunciation.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        word = user_input[1].strip()

    checking_message = await client.send_message(
        message.chat.id,
        "**Checking Pronunciation...✨**",
        parse_mode=ParseMode.MARKDOWN
    )
    try:
        pronunciation_info = await fetch_pronunciation_info(word)
        if pronunciation_info is None:
            await checking_message.edit(
                text="**❌ Sorry Bro Pronunciation API Dead**",
                parse_mode=ParseMode.MARKDOWN
            )
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}prn", Exception("Pronunciation API returned no data"), message)
            return

        audio_filename = None
        if pronunciation_info['audio_link']:
            audio_filename = f"Smart Tool ⚙️ {word}.mp3"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(pronunciation_info['audio_link']) as response:
                        response.raise_for_status()
                        with open(audio_filename, 'wb') as f:
                            f.write(await response.read())
            except aiohttp.ClientError as e:
                logger.error(f"Failed to download audio for word '{word}': {e}")
                # Notify admins
                await notify_admin(client, f"{COMMAND_PREFIX}prn", e, message)
                audio_filename = None

        caption = (
            f"**Word:** {pronunciation_info['word']}\n"
            f"- **Breakdown:** {pronunciation_info['breakdown']}\n"
            f"- **Pronunciation:** {pronunciation_info['pronunciation']}\n\n"
            f"**Word Stems:**\n{', '.join(pronunciation_info['stems'])}\n\n"
            f"**Definition:**\n{pronunciation_info['definition']}"
        )

        if audio_filename:
            await client.send_audio(
                chat_id=message.chat.id,
                audio=audio_filename,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
            os.remove(audio_filename)
        else:
            await client.send_message(
                message.chat.id,
                caption,
                parse_mode=ParseMode.MARKDOWN
            )
        await checking_message.delete()
    except Exception as e:
        logger.error(f"Error processing pronunciation check for word '{word}': {e}")
        # Notify admins
        await notify_admin(client, f"{COMMAND_PREFIX}prn", e, message)
        # Send user-facing error message
        await checking_message.edit(
            text="**❌ Sorry Bro Pronunciation API Dead**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_pron_handler(app: Client):
    app.add_handler(
        MessageHandler(
            pronunciation_check,
            filters.command(["prn"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
