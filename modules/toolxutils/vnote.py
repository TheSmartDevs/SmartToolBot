import os
import subprocess
import traceback
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX
from utils import LOGGER
from core import banned_users  # Add banned user check

# Thread pool for non-blocking FFmpeg execution
executor = ThreadPoolExecutor(max_workers=7)

def run_ffmpeg(ffmpeg_cmd):
    """Run FFmpeg command in a separate thread."""
    return subprocess.run(ffmpeg_cmd, check=True)

def setup_vnote_handler(app: Client):
    @app.on_message(filters.command("vnote", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def vnote_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        if not message.reply_to_message or not message.reply_to_message.video:
            await client.send_message(message.chat.id, "**❗ Reply to a video with this command**")
            return

        video = message.reply_to_message.video
        if video.duration > 60:
            await client.send_message(message.chat.id, "**❗ I can’t process videos longer than 1 minute.**")
            return

        status_msg = await client.send_message(message.chat.id, "**Converting Video To Video Notes**")

        try:
            input_path = await client.download_media(video, file_name="input_video.mp4")
            LOGGER.info(f"Downloaded video to {input_path}")

            output_path = "video_note_ready.mp4"

            # Crop to center square and encode for Telegram
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", "crop='min(in_w,in_h)':'min(in_w,in_h)',scale=640:640",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                output_path
            ]

            # Run FFmpeg in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(executor, run_ffmpeg, ffmpeg_cmd)

            await status_msg.edit("`📤 Uploading...`")
            await client.send_video_note(message.chat.id, video_note=output_path, length=640)
            await status_msg.delete()

        except Exception as e:
            LOGGER.error("Error while processing video:\n" + traceback.format_exc())
            await status_msg.edit("**Sorry I Can't Process This Media**")
        finally:
            # Clean up files
            for f in ["input_video.mp4", "video_note_ready.mp4"]:
                if os.path.exists(f):
                    os.remove(f)