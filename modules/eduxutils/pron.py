# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

async def fetch_pronunciation_info(word):
    url = f"https://abirthetech.serv00.net/pr.php?prompt={word}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                result = await response.json()
                pronunciation_info = result['response']
                LOGGER.info(f"Successfully fetched pronunciation info for '{word}'")
                return {
                    "word": pronunciation_info['Word'],
                    "breakdown": pronunciation_info['- Breakdown'],
                    "pronunciation": pronunciation_info['- Pronunciation'],
                    "stems": pronunciation_info['Word Stems'].split(", "),
                    "definition": pronunciation_info['Definition'],
                    "audio_link": pronunciation_info['Audio']
                }
    except (aiohttp.ClientError, ValueError, KeyError) as e:
        LOGGER.error(f"Pronunciation API error for word '{word}': {e}")
        return None

async def pronunciation_check(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /prn")
        return

    if message.reply_to_message and message.reply_to_message.text:
        word = message.reply_to_message.text.strip()
        if len(word.split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Reply to a message with a single word to check pronunciation.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid reply format: {word}")
            return
    else:
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2 or len(user_input[1].split()) != 1:
            await client.send_message(
                message.chat.id,
                "**❌ Provide a single word to check pronunciation.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid command format: {message.text}")
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
            LOGGER.error(f"Pronunciation API returned no data for word '{word}'")
            await notify_admin(client, "/prn", Exception("Pronunciation API returned no data"), message)
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
                LOGGER.info(f"Downloaded audio for word '{word}'")
            except aiohttp.ClientError as e:
                LOGGER.error(f"Failed to download audio for word '{word}': {e}")
                await notify_admin(client, "/prn audio", e, message)
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
            LOGGER.info(f"Sent audio pronunciation for '{word}' and removed file {audio_filename}")
        else:
            await client.send_message(
                message.chat.id,
                caption,
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.info(f"Sent text pronunciation for '{word}'")
        await checking_message.delete()
    except Exception as e:
        LOGGER.error(f"Error processing pronunciation check for word '{word}': {e}")
        await notify_admin(client, "/prn", e, message)
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
