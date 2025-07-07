# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from pydub import AudioSegment
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

async def handle_voice_command(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /voice")
        return

    if not message.reply_to_message:
        await client.send_message(
            chat_id=message.chat.id,
            text="**Please reply to an audio message.**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.warning("No reply to an audio message provided for /voice command")
        return

    reply = message.reply_to_message

    if not (reply.audio or reply.voice or reply.document):
        await client.send_message(
            chat_id=message.chat.id,
            text="**⚠️ Please reply to a valid audio file.**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.warning("No valid audio file provided for /voice command")
        return

    file_extension = ""
    if reply.audio and reply.audio.file_name:
        file_extension = reply.audio.file_name.split('.')[-1].lower()
    elif reply.document and reply.document.file_name:
        file_extension = reply.document.file_name.split('.')[-1].lower()

    valid_audio_extensions = ['mp3', 'wav', 'ogg', 'm4a']
    if file_extension and file_extension not in valid_audio_extensions:
        await client.send_message(
            chat_id=message.chat.id,
            text="**⚠️ Please reply to a valid audio file**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.warning(f"Invalid audio file extension: {file_extension}")
        return

    processing_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Converting Mp3 To Voice Message✨..**",
        parse_mode=ParseMode.MARKDOWN
    )

    input_path = f"downloads/input.{file_extension if file_extension else 'ogg'}"
    output_path = "downloads/output.ogg"
    os.makedirs("downloads", exist_ok=True)

    try:
        await reply.download(input_path)
        LOGGER.info(f"Downloaded audio file to {input_path}")

        await convert_audio(input_path, output_path)
        LOGGER.info(f"Converted audio to {output_path}")

        await processing_message.delete()

        await client.send_voice(
            chat_id=message.chat.id,
            voice=output_path,
            caption=""
        )
        LOGGER.info("Voice message sent successfully")

    except Exception as e:
        await processing_message.edit_text(
            f"**Sorry Failed To Convert✨**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.error(f"Failed to convert audio: {e}")
        await notify_admin(client, "/voice", e, message)

    finally:
        await cleanup_files(input_path, output_path)

async def convert_audio(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="ogg", codec="libopus")

async def cleanup_files(*files):
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                LOGGER.info(f"Removed temporary file {file}")
        except Exception as e:
            LOGGER.error(f"Failed to remove {file}: {e}")

def setup_voice_handler(app: Client):
    app.add_handler(MessageHandler(
        handle_voice_command,
        filters.command(["voice"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
    ))
