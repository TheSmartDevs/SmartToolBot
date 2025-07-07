# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import aiohttp
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin, progress_bar
from core import banned_users

DOWNLOAD_DIRECTORY = "./downloads/"

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

executor = ThreadPoolExecutor(max_workers=5)

async def aud_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /aud or /convert")
        return

    if not message.reply_to_message or not message.reply_to_message.video:
        await client.send_message(message.chat.id, "**❌ Reply To A Video With The Command**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        LOGGER.warning("No valid video provided for /aud or /convert command")
        return

    command_parts = message.text.split()
    if len(command_parts) <= 1:
        await client.send_message(message.chat.id, "**❌Provide Name For The File**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        LOGGER.warning("No audio file name provided for /aud or /convert command")
        return

    audio_file_name = command_parts[1]
    status_message = await client.send_message(message.chat.id, "**Downloading Your File..✨**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    try:
        video_file_path = await message.reply_to_message.download(DOWNLOAD_DIRECTORY)
        LOGGER.info(f"Downloaded video file to {video_file_path}")

        await status_message.edit("**Converting To Mp3✨..**")

        audio_file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{audio_file_name}.mp3")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, convert_video_to_audio, video_file_path, audio_file_path)
        LOGGER.info(f"Converted video to audio at {audio_file_path}")

        start_time = time.time()
        last_update_time = [start_time]

        await client.send_audio(
            chat_id=message.chat.id,
            audio=audio_file_path,
            caption=f"`{audio_file_name}`",
            parse_mode=ParseMode.MARKDOWN,
            progress=progress_bar,
            progress_args=(status_message, start_time, last_update_time)
        )
        LOGGER.info("Audio file uploaded successfully")

        await status_message.delete()

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
        await status_message.edit(f"**Sorry Bro Converter API Dead✨**")
        await notify_admin(client, "/aud or /convert", e, message)
    finally:
        if 'video_file_path' in locals() and os.path.exists(video_file_path):
            os.remove(video_file_path)
            LOGGER.info(f"Removed temporary video file {video_file_path}")
        if 'audio_file_path' in locals() and os.path.exists(audio_file_path):
            os.remove(audio_file_path)
            LOGGER.info(f"Removed temporary audio file {audio_file_path}")

def convert_video_to_audio(video_file_path, audio_file_path):
    import subprocess
    process = subprocess.run(
        ["ffmpeg", "-i", video_file_path, audio_file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if process.returncode != 0:
        raise Exception(f"ffmpeg error: {process.stderr.decode()}")

async def download_file(url, session, destination):
    async with session.get(url) as response:
        with open(destination, 'wb') as f:
            while True:
                chunk = await response.content.read(1024)
                if not chunk:
                    break
                f.write(chunk)

def setup_aud_handler(app: Client):
    @app.on_message(filters.command(["aud"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def aud_command(client: Client, message: Message):
        asyncio.create_task(aud_handler(client, message))
