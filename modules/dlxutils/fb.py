# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import logging
import time
import re
from pathlib import Path
from typing import Optional
import aiohttp
import asyncio
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX  # Import COMMAND_PREFIX from config
from utils import progress_bar, notify_admin  # Import progress_bar and notify_admin from utils

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    TEMP_DIR = Path("temp")

Config.TEMP_DIR.mkdir(exist_ok=True)

class FacebookDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def download_video(self, url: str, downloading_message: Message) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://tooly.chative.io/facebook/video?url={url}"
        
        try:
            connector = aiohttp.TCPConnector(limit_per_host=10)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(api_url) as response:
                    logger.info(f"API request to {api_url} returned status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"API response: {data}")
                        if data["success"]:
                            await downloading_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
                            video_url = data["videos"]["hd"]["url"]
                            title = data.get("title", "Untitled")
                            filename = self.temp_dir / f"{title}.mp4"
                            await self._download_file(session, video_url, filename)
                            return {
                                'title': title,
                                'filename': str(filename),
                                'webpage_url': url
                            }
                    return None
        except Exception as e:
            logger.error(f"Facebook download error: {e}")
            # Notify admins
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}fb", e, downloading_message)
            return None

    async def _download_file(self, session, url, dest):
        async with session.get(url) as response:
            if response.status == 200:
                logger.info(f"Downloading video from {url} to {dest}")
                f = await aiofiles.open(dest, mode='wb')
                await f.write(await response.read())
                await f.close()

def setup_fb_handlers(app: Client):
    fb_downloader = FacebookDownloader(Config.TEMP_DIR)

    # Create a regex pattern from the COMMAND_PREFIX list
    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}fb(\s+https?://\S+)?$") & (filters.private | filters.group))
    async def fb_handler(client: Client, message: Message):
        # Check if message is a reply to another message
        if message.reply_to_message and message.reply_to_message.text:
            url = message.reply_to_message.text
        else:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="**Please provide a Facebook link ❌**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            url = command_parts[1]

        downloading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Video**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            video_info = await fb_downloader.download_video(url, downloading_message)
            if video_info:
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
                    f"🔗 **Url**: [Watch On Facebook]({webpage_url})\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"**Downloaded By**: {user_info}"
                )

                async with aiofiles.open(filename, 'rb') as video_file:
                    start_time = time.time()
                    last_update_time = [start_time]
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=filename,
                        supports_streaming=True,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        progress=progress_bar,
                        progress_args=(downloading_message, start_time, last_update_time)
                    )
                
                await downloading_message.delete()
                os.remove(filename)
            else:
                logger.info("Invalid Video URL or Video is Private")
                await downloading_message.edit_text("**Invalid Video URL Or Video Private**")
        except Exception as e:
            logger.error(f"Error downloading Facebook video: {e}")
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}fb", e, message)
            # Send user-facing error message
            await downloading_message.edit_text("**Facebook Downloader API Dead**")
