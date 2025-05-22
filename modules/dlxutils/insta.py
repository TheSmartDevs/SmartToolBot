# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import re
import logging
import time
from pathlib import Path
from typing import Optional, List
import aiohttp
import asyncio
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import progress_bar, notify_admin

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

class InstagramDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def download_content(self, url: str, downloading_message: Message, content_type: str) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://insta.bdbots.xyz/dl?url={url}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    logger.info(f"API request to {api_url} returned status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"API response: {data}")
                        if data.get("status") == "success":
                            api_content_type = data["data"]["type"]
                            await downloading_message.edit_text(
                                "**Found ☑️ Downloading...**" if content_type == "video" else "`📤 Uploading...`",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            media_files = []
                            for index, media in enumerate(data["data"]["media"]):
                                media_url = media["url"]
                                ext = "mp4" if media["type"] == "video" else "jpg"
                                filename = self.temp_dir / f"{data['data']['username']}_{data['data']['metadata']['shortcode']}_{index}.{ext}"
                                await self._download_file(session, media_url, filename)
                                media_files.append({
                                    "filename": str(filename),
                                    "type": media["type"]
                                })
                            return {
                                "title": data["data"].get("caption", "Instagram Reel"),
                                "media_files": media_files,
                                "webpage_url": url,
                                "username": data["data"]["username"],
                                "type": api_content_type
                            }
                    return None
        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}in", e, downloading_message)
            return None

    async def _download_file(self, session, url, dest):
        async with session.get(url) as response:
            if response.status == 200:
                logger.info(f"Downloading file from {url} to {dest}")
                async with aiofiles.open(dest, mode='wb') as f:
                    await f.write(await response.read())

def setup_insta_handlers(app: Client):
    ig_downloader = InstagramDownloader(Config.TEMP_DIR)

    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}in(\s+https?://\S+)?$") & (filters.private | filters.group))
    async def ig_handler(client: Client, message: Message):
        if message.reply_to_message and message.reply_to_message.text:
            url = message.reply_to_message.text.strip()
        else:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await client.send_message(
                    chat_id=message.chat.id,
                    text="**Provide an Instagram Reels/Post URL ❌**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            url = command_parts[1].strip()

        content_type = "video" if "/reel/" in url else "post"

        downloading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Video**" if content_type == "video" else "`🔍 Fetching media from Instagram...`",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            content_info = await ig_downloader.download_content(url, downloading_message, content_type)
            if content_info:
                title = content_info["title"]
                media_files = content_info["media_files"]
                webpage_url = content_info["webpage_url"]
                content_type = content_info["type"]
                username = content_info["username"]
                
                if message.from_user:
                    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                    user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
                else:
                    group_name = message.chat.title or "this squad"
                    group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this squad"
                    user_info = f"[{group_name}]({group_url})"

                if content_type == "video":
                    caption = (
                        f"🔥 Yo Bro! Insta DL Successfull ✅\n"
                        f"🎬 **Title**: {title}\n"
                        f"📸 **Uploader**: @{username}\n"
                        f"🌐 **Watch On Insta**: [Click Here]({webpage_url})\n"
                        f"👉 **Downloaded By**: {user_info}\n"
                        f"#InstaVibes #ReelIt #Slay"
                    )
                    inline_keyboard = InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔍 View On Insta", url=webpage_url)]]
                    )
                else:
                    caption = ""  # No caption for posts
                    inline_keyboard = None

                if len(media_files) > 1 and content_type == "carousel":
                    media_group = []
                    for index, media in enumerate(media_files):
                        media_type = InputMediaPhoto if media["type"] == "image" else InputMediaVideo
                        media_group.append(
                            media_type(
                                media=media["filename"],
                                caption=caption if index == 0 else "",
                                parse_mode=ParseMode.MARKDOWN
                            )
                        )
                    await client.send_media_group(
                        chat_id=message.chat.id,
                        media=media_group
                    )
                else:
                    media = media_files[0]
                    if media["type"] == "video":
                        async with aiofiles.open(media["filename"], 'rb'):
                            start_time = time.time()
                            last_update_time = [start_time]
                            await client.send_video(
                                chat_id=message.chat.id,
                                video=media["filename"],
                                supports_streaming=True,
                                caption=caption,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=inline_keyboard,
                                progress=progress_bar,
                                progress_args=(downloading_message, start_time, last_update_time)
                            )
                    else:
                        async with aiofiles.open(media["filename"], 'rb'):
                            await client.send_photo(
                                chat_id=message.chat.id,
                                photo=media["filename"],
                                caption=caption,
                                parse_mode=ParseMode.MARKDOWN
                            )

                await downloading_message.delete()
                for media in media_files:
                    os.remove(media["filename"])
            else:
                await downloading_message.edit_text(
                    "**Unable To Extract The URL 😕**", parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Error processing Instagram content: {e}")
            await notify_admin(client, f"{COMMAND_PREFIX}in", e, message)
            await downloading_message.edit_text(
                "**Instagram Downloader API Down 📉**", parse_mode=ParseMode.MARKDOWN
            )
