# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import re
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
from utils import LOGGER, progress_bar, notify_admin

# Configuration
class Config:
    TEMP_DIR = Path("temp")
    MAX_MEDIA_PER_GROUP = 10  # Telegram's media group limit

Config.TEMP_DIR.mkdir(exist_ok=True)

class InstagramDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def download_content(self, url: str, downloading_message: Message, content_type: str) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://its-smart-dev.vercel.app/download?url={url}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as response:
                    LOGGER.info(f"API request to {api_url} returned status {response.status}")
                    if response.status != 200:
                        return None
                    data = await response.json()
                    LOGGER.info(f"API response: {data}")
                    if data.get("status") != "success":
                        return None
                    
                    # Infer content type (video or carousel) from URL and media count
                    api_content_type = "video" if "/reel/" in url or len(data["media_urls"]) == 1 and data["media_urls"][0].endswith('.mp4') else "carousel"
                    await downloading_message.edit_text(
                        "**Found ☑️ Downloading...**" if api_content_type == "video" else "`📤 Uploading...`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    media_files = []
                    # Download all media files concurrently
                    tasks = [
                        self._download_file(
                            session, 
                            media_url, 
                            self.temp_dir / f"{data['author']}_{time.time()}_{index}.{ 'mp4' if media_url.endswith('.mp4') else 'jpg' }"
                        )
                        for index, media_url in enumerate(data["media_urls"])
                    ]
                    downloaded_files = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for index, result in enumerate(downloaded_files):
                        if isinstance(result, Exception):
                            LOGGER.error(f"Failed to download media {index}: {result}")
                            continue
                        media_files.append({
                            "filename": str(result),
                            "type": "video" if data["media_urls"][index].endswith('.mp4') else "image"
                        })
                    
                    if not media_files:
                        return None
                        
                    return {
                        "title": data.get("title", "Instagram Reel"),
                        "media_files": media_files,
                        "webpage_url": url,
                        "username": data["author"],
                        "type": api_content_type
                    }
        except Exception as e:
            LOGGER.error(f"Instagram download error: {e}")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}in|ig|insta", e, downloading_message)
            return None

    async def _download_file(self, session: aiohttp.ClientSession, url: str, dest: Path) -> Path:
        async with session.get(url) as response:
            if response.status == 200:
                LOGGER.info(f"Downloading file from {url} to {dest}")
                async with aiofiles.open(dest, mode='wb') as f:
                    await f.write(await response.read())
                return dest
            raise Exception(f"Failed to download {url}: Status {response.status}")

def setup_insta_handlers(app: Client):
    ig_downloader = InstagramDownloader(Config.TEMP_DIR)

    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"
    command_suffix_regex = r"(in|ig|insta)"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}{command_suffix_regex}(\s+https?://\S+)?$") & (filters.private | filters.group))
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
            if not content_info:
                await downloading_message.edit_text(
                    "**Unable To Extract The URL 😕**", parse_mode=ParseMode.MARKDOWN
                )
                return

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

            caption = (
                f"🔥 Yo Bro! Insta DL Successfull ✅\n"
                f"🎬 **Title**: {title}\n"
                f"📸 **Uploader**: @{username}\n"
                f"🌐 **Watch On Insta**: [Click Here]({webpage_url})\n"
                f"👉 **Downloaded By**: {user_info}\n"
                f"#InstaVibes #ReelIt #Slay"
            ) if content_type == "video" else ""
            
            inline_keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔍 View On Insta", url=webpage_url)]]
            ) if content_type == "video" else None

            if content_type == "carousel" and len(media_files) > 1:
                # Split media files into chunks of MAX_MEDIA_PER_GROUP
                for i in range(0, len(media_files), Config.MAX_MEDIA_PER_GROUP):
                    media_group = []
                    for index, media in enumerate(media_files[i:i + Config.MAX_MEDIA_PER_GROUP]):
                        media_type = InputMediaPhoto if media["type"] == "image" else InputMediaVideo
                        media_group.append(
                            media_type(
                                media=media["filename"],
                                caption=caption if index == 0 and i == 0 else "",
                                parse_mode=ParseMode.MARKDOWN
                            )
                        )
                    await client.send_media_group(
                        chat_id=message.chat.id,
                        media=media_group
                    )
            else:
                media = media_files[0]
                async with aiofiles.open(media["filename"], 'rb'):
                    if media["type"] == "video":
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
                        await client.send_photo(
                            chat_id=message.chat.id,
                            photo=media["filename"],
                            caption=caption,
                            parse_mode=ParseMode.MARKDOWN
                        )

            await downloading_message.delete()
            # Clean up files asynchronously
            await asyncio.gather(*(asyncio.to_thread(os.remove, media["filename"]) for media in media_files))
                
        except Exception as e:
            LOGGER.error(f"Error processing Instagram content: {e}")
            await notify_admin(client, f"{COMMAND_PREFIX}in|ig|insta", e, message)
            await downloading_message.edit_text(
                "**Instagram Downloader API Down **", parse_mode=ParseMode.MARKDOWN
            )
