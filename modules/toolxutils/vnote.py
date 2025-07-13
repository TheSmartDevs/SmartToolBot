# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
import time
import subprocess
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FileIdInvalid
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

executor = ThreadPoolExecutor(max_workers=16)  # Increased for better CPU utilization

def run_ffmpeg(ffmpeg_cmd):
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        LOGGER.error(f"FFmpeg failed: {e.stderr.decode()}")
        raise

def setup_vnote_handler(app: Client):
    @app.on_message(filters.command("vnote", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def vnote_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        
        if not message.reply_to_message or not message.reply_to_message.video:
            await client.send_message(message.chat.id, "**❗ Reply to a video with this command**")
            return
        
        video = message.reply_to_message.video
        if video.duration > 60:
            await client.send_message(message.chat.id, "**❗ I can't process videos longer than 1 minute.**")
            return
        
        status_msg = await client.send_message(message.chat.id, "**Converting Video To Video Notes**")
        
        input_path = f"downloads/input_{user_id}_{int(time.time())}.mp4"
        output_path = f"downloads/output_{user_id}_{int(time.time())}.mp4"
        
        try:
            # Ensure downloads directory
            os.makedirs("downloads", exist_ok=True)
            
            # Download
            input_path = await client.download_media(video, file_name=input_path)
            if not input_path:
                raise FileNotFoundError("Download failed")
            
            # FFmpeg: ultra-fast settings
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-vf", "crop='min(iw,ih):min(iw,ih)',scale=640:640",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
                "-c:a", "aac", "-b:a", "96k", "-ar", "32000",
                "-t", "60", "-movflags", "+faststart", output_path
            ]
            
            await asyncio.get_event_loop().run_in_executor(executor, run_ffmpeg, ffmpeg_cmd)
            
            # Upload
            await client.send_video_note(
                chat_id=message.chat.id,
                video_note=output_path,
                length=640,
                duration=min(video.duration, 60)
            )
            
            await status_msg.delete()
            
        except FileIdInvalid:
            LOGGER.error("Invalid video file_id")
            await notify_admin(client, "/vnote", "Invalid file_id", message)
            await status_msg.edit("**Invalid video file**")
        except Exception as e:
            LOGGER.error(f"Error: {str(e)}")
            await notify_admin(client, "/vnote", e, message)
            await status_msg.edit("**Sorry I Can't Process This Media**")
        finally:
            for f in [input_path, output_path]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
            LOGGER.info(f"Cleaned up: {[input_path, output_path]}")
