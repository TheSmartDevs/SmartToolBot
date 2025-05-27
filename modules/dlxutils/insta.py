# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import re
import time
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, List
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import LOGGER, progress_bar, notify_admin  # Import LOGGER, progress_bar, and notify_admin from utils
from core import banned_users  # Check if user is banned

# Configuration
class Config:
    TEMP_DIR = Path("temp")
    MAX_MEDIA_PER_GROUP = 10  # Telegram's media group limit

Config.TEMP_DIR.mkdir(exist_ok=True)

class InstagramDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def sanitize_filename(self, username: str, shortcode: str, index: int, media_type: str) -> str:
        """Sanitize file name using username, shortcode, and index."""
        safe_username = re.sub(r'[<>:"/\\|?*]', '', username[:30]).strip()
        safe_shortcode = re.sub(r'[<>:"/\\|?*]', '', shortcode).strip()
        return f"{safe_username}_{safe_shortcode}_{index}_{int(time.time())}.{ 'mp4' if media_type == 'video' else 'jpg' }"

    async def download_content(self, url: str, downloading_message: Message, content_type: str) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://insta.bdbots.xyz/dl?url={url}"
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=100),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(api_url) as response:
                    LOGGER.info(f"API request to {api_url} returned status {response.status}")
                    if response.status != 200:
                        LOGGER.error(f"API request failed: HTTP status {response.status}")
                        return None
                    data = await response.json()
                    LOGGER.info(f"API response: {data}")
                    if data.get("status") != "success":
                        LOGGER.error("API response indicates failure")
                        return None
                    
                    api_content_type = data["data"]["type"]
                    await downloading_message.edit_text(
                        "**Found ☑️ Downloading...**" if content_type == "video" else "**📤 Uploading...**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    media_files = []
                    # Download all media files concurrently
                    tasks = [
                        self._download_file(
                            session,
                            media["url"],
                            self.temp_dir / await self.sanitize_filename(
                                data['data']['username'],
                                data['data']['metadata']['shortcode'],
                                index,
                                media['type']
                            )
                        )
                        for index, media in enumerate(data["data"]["media"])
                    ]
                    downloaded_files = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for index, result in enumerate(downloaded_files):
                        if isinstance(result, Exception):
                            LOGGER.error(f"Failed to download media {index}: {result}")
                            continue
                        media_files.append({
                            "filename": str(result),
                            "type": data["data"]["media"][index]["type"]
                        })
                    
                    if not media_files:
                        LOGGER.error("No media files downloaded successfully")
                        return None
                        
                    return {
                        "title": data["data"].get("caption", "Instagram Content"),
                        "media_files": media_files,
                        "webpage_url": url,
                        "username": data["data"]["username"],
                        "type": api_content_type
                    }
        except aiohttp.ClientError as e:
            LOGGER.error(f"Instagram download error: {e}")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}in", e, downloading_message)
            return None
        except asyncio.TimeoutError:
            LOGGER.error("Request to Instagram API timed out")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}in", asyncio.TimeoutError("Request to Instagram API timed out"), downloading_message)
            return None
        except Exception as e:
            LOGGER.error(f"Instagram download error: {e}")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}in", e, downloading_message)
            return None

    async def _download_file(self, session: aiohttp.ClientSession, url: str, dest: Path) -> Path:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    LOGGER.info(f"Downloading file from {url} to {dest}")
                    async with aiofiles.open(dest, mode='wb') as f:
                        async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                            await f.write(chunk)
                    LOGGER.info(f"File downloaded successfully to {dest}")
                    return dest
                raise Exception(f"Failed to download {url}: Status {response.status}")
        except aiohttp.ClientError as e:
            LOGGER.error(f"Error downloading file from {url}: {e}")
            raise

def setup_insta_handlers(app: Client):
    ig_downloader = InstagramDownloader(Config.TEMP_DIR)

    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}in(\s+https?://\S+)?$") & (filters.private | filters.group))
    async def ig_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            return

        url = None
        # Check if URL from reply
        if message.reply_to_message and message.reply_to_message.text:
            match = re.search(r"https?://(www\.)?instagram\.com/(reel|p)/\S+", message.reply_to_message.text)
            if match:
                url = match.group(0)
        # Check if URL from command
        if not url:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) > 1:
                match = re.search(r"https?://(www\.)?instagram\.com/(reel|p)/\S+", command_parts[1])
                if match:
                    url = match.group(0)

        if not url:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please provide a valid Instagram Reels/Post URL or reply to a message with one ❌**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"No Instagram URL provided, user: {user_id or 'unknown'}, chat: {message.chat.id}")
            return

        LOGGER.info(f"Instagram URL received: {url}, user: {user_id or 'unknown'}, chat: {message.chat.id}")
        content_type = "video" if "/reel/" in url else "post"
        downloading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Video**" if content_type == "video" else "**🔍 Fetching media from Instagram...**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            content_info = await ig_downloader.download_content(url, downloading_message, content_type)
            if not content_info:
                await downloading_message.edit_text(
                    "**Unable To Extract The URL 😕**", parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.error(f"Failed to download content for URL: {url}")
                return

            title = content_info["title"]
            media_files = content_info["media_files"]
            webpage_url = content_info["webpage_url"]
            content_type = content_info["type"]
            username = content_info["username"]
            
            if message.from_user:
                user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                user_info = f"[{user_full_name}](tg://user?id={user_id})"
            else:
                group_name = message.chat.title or "this squad"
                group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this squad"
                user_info = f"[{group_name}]({group_url})"

            caption = (
                f"🔥 **Insta DL Success!** ✅\n"
                f"🎬 **Title**: `{title}`\n"
                f"📸 **Uploader**: `@{username}`\n"
                f"🌐 **Link**: [View on Instagram]({webpage_url})\n"
                f"👉 **Downloaded By**: {user_info}\n"
                f"#InstaVibes #ReelIt"
            ) if content_type == "video" else (
                f"📸 **Insta Post Downloaded!** ✅\n"
                f"🎨 **Caption**: `{title}`\n"
                f"👤 **Uploader**: `@{username}`\n"
                f"🌐 **Link**: [View on Instagram]({webpage_url})\n"
                f"👉 **Downloaded By**: {user_info}\n"
                f"#InstaMoments #PostVibes"
            )
            
            inline_keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔍 View on Insta", url=webpage_url)]]
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
            for media in media_files:
                if os.path.exists(media["filename"]):
                    os.remove(media["filename"])
                    LOGGER.info(f"Deleted media file: {media['filename']}")

        except Exception as e:
            LOGGER.error(f"Error processing Instagram content: {e}")
            await notify_admin(client, f"{COMMAND_PREFIX}in", e, downloading_message)
            await downloading_message.edit_text(
                "**Instagram Downloader API Down**", parse_mode=ParseMode.MARKDOWN
            )