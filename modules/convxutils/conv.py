#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import time
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import aiohttp
from config import COMMAND_PREFIX

# Directory to save the downloaded files temporarily
DOWNLOAD_DIRECTORY = "./downloads/"

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ThreadPoolExecutor instance
executor = ThreadPoolExecutor(max_workers=5)  # You can adjust the number of workers

async def progress_bar(current, total, status_message, start_time, last_update_time):
    """Display a progress bar for uploads."""
    elapsed_time = time.time() - start_time
    percentage = (current / total) * 100
    progress = "▓" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
    speed = current / elapsed_time / 1024 / 1024  # Speed in MB/s
    uploaded = current / 1024 / 1024  # Uploaded size in MB
    total_size = total / 1024 / 1024  # Total size in MB

    # Throttle updates: Only update if at least 2 seconds have passed since the last update
    if time.time() - last_update_time[0] < 2:
        return
    last_update_time[0] = time.time()  # Update the last update time

    text = (
        f"📥 Upload Progress 📥\n\n"
        f"{progress}\n\n"
        f"🚧 Percentage: {percentage:.2f}%\n"
        f"⚡️ Speed: {speed:.2f} MB/s\n"
        f"📶 Uploaded: {uploaded:.2f} MB of {total_size:.2f} MB"
    )
    try:
        await status_message.edit(text)
    except Exception as e:
        logger.error(f"Error updating progress: {e}")

async def aud_handler(client: Client, message: Message):
    # Check if the message is a reply to a video
    if not message.reply_to_message or not message.reply_to_message.video:
        await client.send_message(message.chat.id, "**❌ Reply To A Video With The Command**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return

    # Get the command and its arguments
    command_parts = message.text.split()

    # Check if the user provided an audio file name
    if len(command_parts) <= 1:
        await client.send_message(message.chat.id, "**❌Provide Name For The File**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return

    # Get the audio file name from the command
    audio_file_name = command_parts[1]

    # Notify the user that the video is being downloaded
    status_message = await client.send_message(message.chat.id, "**Downloading Your File..✨**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    try:
        # Download the video
        video_file_path = await message.reply_to_message.download(DOWNLOAD_DIRECTORY)

        # Update the status message
        await status_message.edit("**Converting To Mp3✨..**")

        # Define the output audio file path
        audio_file_path = os.path.join(DOWNLOAD_DIRECTORY, f"{audio_file_name}.mp3")

        # Convert the video to audio using ffmpeg in a separate thread
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, convert_video_to_audio, video_file_path, audio_file_path)

        # Update the status message
        await status_message.edit("**Uploading To Telegram✨..**")

        # Start uploading the audio file to the user with a progress bar
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

        # Delete the status message after uploading is complete
        await status_message.delete()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await status_message.edit(f"**Sorry Bro Converter API Dead✨**")
    finally:
        # Delete the temporary video and audio files
        if os.path.exists(video_file_path):
            os.remove(video_file_path)
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

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
    @app.on_message(filters.command(["aud","convert"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def aud_command(client: Client, message: Message):
        # Run the aud_handler in the background to handle multiple requests simultaneously
        asyncio.create_task(aud_handler(client, message))