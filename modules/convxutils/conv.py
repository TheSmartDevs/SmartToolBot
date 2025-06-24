# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import aiohttp
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin, progress_bar  # Import LOGGER, notify_admin, progress_bar from utils
from core import banned_users  # Check if user is banned

# Directory to save the downloaded files temporarily
DOWNLOAD_DIRECTORY = "./downloads/"

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

# ThreadPoolExecutor instance
executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of workers

async def aud_handler(client: Client, message: Message):
    # Check if user is banned
    user_id = message.from_user.id if message.from_user else None
    # Await for MotorDB (async)
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /aud or /convert")
        return

    # Check if the message is a reply to a video
    if not message.reply_to_message or not message.reply_to_message.video:
        await client.send_message(message.chat.id, "**❌ Reply To A Video With The Command**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        LOGGER.warning("No valid video provided for /aud or /convert command")
        return

    # Get the command and its arguments
    command_parts = message.text.split()

    # Check if the user provided an audio file name
    if len(command_parts) <= 1:
        await client.send_message(message.chat.id, "**❌Provide Name For The File**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        LOGGER.warning("No audio file name provided for /aud or /convert command")
        return

    # Get the audio file name from the command
    audio_file_name = command_parts[1]

    # Notify the user that the video is being downloaded
    status_message = await client.send_message(message.chat.id, "**Downloading Your File..✨**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    try:
        # Download the video
        video_file_path = await message.reply_to_message.download(DOWNLOAD_DIRECTORY)
        LOGGER.info(f"Downloaded video file to {video_file_path}")

        # Update the status message
        await status_message.edit("**Converting To Mp3✨..**")

        # Define the output audio file path
        audio_file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{audio_file_name}.mp3")

        # Convert the video to audio using ffmpeg in a separate thread
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, convert_video_to_audio, video_file_path, audio_file_path)
        LOGGER.info(f"Converted video to audio at {audio_file_path}")

        # No intermediate status update: use progress_bar directly for upload
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

        # Delete the status message after uploading is complete
        await status_message.delete()

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
        await status_message.edit(f"**Sorry Bro Converter API Dead✨**")
        # Notify admins about the error
        await notify_admin(client, "/aud or /convert", e, message)
    finally:
        # Delete the temporary video and audio files
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

# Function to set up handlers for the Pyrogram bot
def setup_aud_handler(app: Client):
    @app.on_message(filters.command(["aud", "convert"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def aud_command(client: Client, message: Message):
        # Run the aud_handler in the background to handle multiple requests simultaneously
        asyncio.create_task(aud_handler(client, message))
