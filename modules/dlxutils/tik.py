# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import time
import re
from pathlib import Path
from typing import Optional
import aiohttp
import aiofiles
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import LOGGER, progress_bar, notify_admin  # Import LOGGER, progress_bar, and notify_admin from utils
from core import banned_users  # Check if user is banned

# Use the imported LOGGER
logger = LOGGER

# Configuration
class Config:
    TEMP_DIR = Path("temp")

Config.TEMP_DIR.mkdir(exist_ok=True)

async def sanitize_filename(title: str) -> str:
    """Sanitize file name by removing invalid characters."""
    title = re.sub(r'[<>:"/\\|?*]', '', title[:50]).strip()
    return f"{title.replace(' ', '_')}_{int(time.time())}"

async def download_video(url: str, downloading_message: Message) -> Optional[dict]:
    """Download video from TikTok URL using API."""
    api_url = "https://downloader.bot/api/tiktok/info"
    payload = {"url": url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://downloader.bot"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            logger.error(f"API error: {data['error']}")
            # Notify admins
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}tt", Exception(f"API error: {data['error']}"), downloading_message)
            return None

        info = data["data"]
        video_url = info.get("mp4")
        if not video_url:
            logger.error("No video URL found in API response")
            # Notify admins
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}tt", Exception("No video URL found in API response"), downloading_message)
            return None

        await downloading_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
        
        title = info.get("title", "TikTok_Video")
        safe_title = await sanitize_filename(title)
        video_output = Config.TEMP_DIR / f"{safe_title}.mp4"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, headers=headers) as video_response:
                if video_response.status == 200:
                    async with aiofiles.open(video_output, 'wb') as f:
                        async for chunk in video_response.content.iter_chunked(8192):
                            await f.write(chunk)
                    logger.info(f"Video downloaded successfully to: {video_output}")
                    return {
                        'filename': str(video_output),
                        'title': title,
                        'webpage_url': url
                    }
                else:
                    logger.error(f"Failed to download video: HTTP {video_response.status}")
                    # Notify admins
                    await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}tt", Exception(f"Failed to download video: HTTP {video_response.status}"), downloading_message)
                    return None
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        # Notify admins
        await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}tt", e, downloading_message)
        return None

def setup_tt_handler(app: Client):
    # Create a regex pattern from the COMMAND_PREFIX list
    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}tt(\s+https?://\S+)?$") & (filters.private | filters.group))
    async def tiktok_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        url = None
        # Check if the message is a reply to another message containing a URL
        if message.reply_to_message and message.reply_to_message.text:
            replied_text = message.reply_to_message.text
            if re.match(r'https?://\S+', replied_text):
                url = replied_text

        # If no URL from reply, check the command arguments
        if not url:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="**Please provide a TikTok link ❌**",
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.warning(f"No TikTok URL provided, user: {user_id or 'unknown'}, chat: {message.chat.id}")
                return
            url = command_parts[1]

        status_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Video...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            video_info = await download_video(url, status_message)
            if not video_info:
                await status_message.edit_text("**❌ Invalid Video URL Inputted**", parse_mode=ParseMode.MARKDOWN)
                logger.error(f"Failed to download video for URL: {url}")
                return

            title = video_info['title']
            filename = video_info['filename']
            webpage_url = video_info['webpage_url']

            if message.from_user:
                user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
            else:
                group_name = message.chat.title or "this group"
                group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
                user_info = f"[{group_name}]({group_url})"

            caption = (
                f"🎵 **Title**: **{title}**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔗 **Url**: [Watch On TikTok]({webpage_url})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**Downloaded By**: {user_info}"
            )

            start_time = time.time()
            last_update_time = [start_time]

            await client.send_video(
                chat_id=message.chat.id,
                video=filename,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                progress=progress_bar,
                progress_args=(status_message, start_time, last_update_time)
            )

            await status_message.delete()
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f"Deleted the video file: {filename}")

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}tt", e, message)
            # Send user-facing error message
            await status_message.edit_text("**TikTok Downloader API Dead**", parse_mode=ParseMode.MARKDOWN)