# Copyright @ISmartCoder
# Updates Channel t.me/TheSmartDev

import os
import re
import time
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, List
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from pyrogram.enums import ParseMode
from moviepy import VideoFileClip
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, progress_bar
from core import banned_users

logger = LOGGER

class Config:
    TEMP_DIR = Path("temp")
    MAX_MEDIA_PER_GROUP = 10
    DOWNLOAD_RETRIES = 3
    RETRY_DELAY = 2

Config.TEMP_DIR.mkdir(exist_ok=True)

class InstagramDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    async def sanitize_filename(self, shortcode: str, index: int, media_type: str) -> str:
        safe_shortcode = re.sub(r'[<>:"/\\|?*]', '', shortcode[:30]).strip()
        return f"{safe_shortcode}_{index}_{int(time.time())}.{ 'mp4' if media_type == 'video' else 'jpg' }"

    async def sanitize_caption(self, caption: str) -> str:
        if not caption or caption.lower() == "unknown":
            return "Instagram Content"
        sanitized = re.sub(r'@\w+', '', caption).strip()
        return sanitized if sanitized else "Instagram Content"

    async def download_file(self, session: aiohttp.ClientSession, url: str, dest: Path, retries: int = Config.DOWNLOAD_RETRIES) -> Path:
        for attempt in range(1, retries + 1):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        logger.info(f"Downloading file from {url} to {dest} (attempt {attempt}/{retries})")
                        async with aiofiles.open(dest, mode='wb') as f:
                            async for chunk in response.content.iter_chunked(1024 * 1024):
                                await f.write(chunk)
                        logger.info(f"File downloaded successfully to {dest}")
                        return dest
                    else:
                        error_msg = f"Failed to download {url}: Status {response.status}"
                        logger.error(error_msg)
                        if attempt == retries:
                            raise Exception(error_msg)
            except aiohttp.ClientError as e:
                error_msg = f"Error downloading file from {url}: {e}"
                logger.error(error_msg)
                if attempt == retries:
                    raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error downloading file from {url}: {e}"
                logger.error(error_msg)
                if attempt == retries:
                    raise Exception(error_msg)
            logger.info(f"Retrying download for {url} in {Config.RETRY_DELAY} seconds...")
            await asyncio.sleep(Config.RETRY_DELAY)
        raise Exception(f"Failed to download {url} after {retries} attempts")

    async def download_content(self, url: str, downloading_message: Message, content_type: str) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://insta.bdbots.xyz/dl?url={url}"
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=100),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(api_url) as response:
                    logger.info(f"API request to {api_url} returned status {response.status}")
                    if response.status != 200:
                        logger.error(f"API request failed: HTTP status {response.status}")
                        return None
                    data = await response.json()
                    logger.info(f"API response: {data}")
                    if data.get("status") != "success":
                        logger.error("API response indicates failure")
                        return None
                    
                    if content_type in ["reel", "igtv"]:
                        await downloading_message.edit_text(
                            "**Found ☑️ Downloading...**",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    
                    media_files = []
                    tasks = []
                    thumbnail_tasks = []
                    thumbnail_paths = []
                    for index, media in enumerate(data["data"]["media"]):
                        media_type = media["type"]
                        filename = self.temp_dir / await self.sanitize_filename(data["data"]["metadata"]["shortcode"], index, media_type)
                        tasks.append(self.download_file(session, media["url"], filename))
                        
                        thumbnail_url = media.get("thumbnail")
                        thumbnail_filename = None
                        if thumbnail_url:
                            thumbnail_filename = self.temp_dir / f"{filename.stem}_thumb.jpg"
                            thumbnail_tasks.append(self.download_file(session, thumbnail_url, thumbnail_filename))
                            thumbnail_paths.append(thumbnail_filename)
                        else:
                            thumbnail_tasks.append(None)
                            thumbnail_paths.append(None)
                    
                    downloaded_files = await asyncio.gather(*tasks, return_exceptions=True)
                    downloaded_thumbnails = await asyncio.gather(*[t for t in thumbnail_tasks if t], return_exceptions=True) if any(t for t in thumbnail_tasks) else [None] * len(tasks)
                    
                    thumbnail_index = 0
                    for index, (result, thumbnail_result, thumbnail_path) in enumerate(zip(downloaded_files, thumbnail_tasks, thumbnail_paths)):
                        if isinstance(result, Exception):
                            logger.error(f"Failed to download media {index} for URL {data['data']['media'][index]['url']}: {result}")
                            if thumbnail_path and os.path.exists(thumbnail_path):
                                os.remove(thumbnail_path)
                                logger.info(f"Deleted orphaned thumbnail: {thumbnail_path}")
                            continue
                        thumbnail_filename = None
                        if thumbnail_result and not isinstance(thumbnail_result, Exception):
                            thumbnail_filename = str(thumbnail_path)
                            thumbnail_index += 1
                        media_files.append({
                            "filename": str(result),
                            "type": data["data"]["media"][index]["type"],
                            "thumbnail": thumbnail_filename
                        })
                    
                    if not media_files:
                        logger.error("No media files downloaded successfully")
                        return None
                        
                    return {
                        "title": await self.sanitize_caption(data["data"]["caption"]),
                        "media_files": media_files,
                        "webpage_url": data["data"]["metadata"]["url"],
                        "type": data["data"]["type"]
                    }
        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            return None

def setup_insta_handlers(app: Client):
    ig_downloader = InstagramDownloader(Config.TEMP_DIR)

    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}(in|insta|ig)(\s+https?://\S+)?$") & (filters.private | filters.group))
    async def ig_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            return

        url = None
        if message.reply_to_message and message.reply_to_message.text:
            match = re.search(r"https?://(www\.)?instagram\.com/\S+", message.reply_to_message.text)
            if match:
                url = match.group(0)
        if not url:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) > 1:
                match = re.search(r"https?://(www\.)?instagram\.com/\S+", command_parts[1])
                if match:
                    url = match.group(0)

        if not url:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please provide a valid Instagram URL or reply to a message with one ❌**",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.warning(f"No Instagram URL provided, user: {user_id or 'unknown'}, chat: {message.chat.id}")
            return

        logger.info(f"Instagram URL received: {url}, user: {user_id or 'unknown'}, chat: {message.chat.id}")
        content_type = "reel" if "/reel/" in url else "igtv" if "/tv/" in url else "story" if "/stories/" in url else "post"
        downloading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Video**" if content_type in ["reel", "igtv"] else "`🔍 Fetching media from Instagram...`",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            content_info = await ig_downloader.download_content(url, downloading_message, content_type)
            if not content_info:
                await downloading_message.edit_text(
                    "**Unable To Extract The URL 😕**", parse_mode=ParseMode.MARKDOWN
                )
                logger.error(f"Failed to download content for URL: {url}")
                return

            media_files = content_info["media_files"]
            content_type = content_info["type"]
            
            if content_type == "carousel" or media_files[0]["type"] == "image":
                await downloading_message.edit_text(
                    "`📤 Uploading...`",
                    parse_mode=ParseMode.MARKDOWN
                )

            if content_type == "carousel" and len(media_files) > 1:
                for i in range(0, len(media_files), Config.MAX_MEDIA_PER_GROUP):
                    media_group = []
                    for index, media in enumerate(media_files[i:i + Config.MAX_MEDIA_PER_GROUP]):
                        if media["type"] == "image":
                            media_group.append(
                                InputMediaPhoto(
                                    media=media["filename"]
                                )
                            )
                        else:
                            video_clip = VideoFileClip(media["filename"])
                            duration = video_clip.duration
                            video_clip.close()
                            
                            media_group.append(
                                InputMediaVideo(
                                    media=media["filename"],
                                    thumb=media["thumbnail"] if media["thumbnail"] else None,
                                    width=1280,
                                    height=720,
                                    duration=int(duration),
                                    supports_streaming=True
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
                        video_clip = VideoFileClip(media["filename"])
                        duration = video_clip.duration
                        video_clip.close()
                        
                        start_time = time.time()
                        last_update_time = [start_time]
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=media["filename"],
                            thumb=media["thumbnail"] if media["thumbnail"] else None,
                            width=1280,
                            height=720,
                            duration=int(duration),
                            supports_streaming=True,
                            progress=progress_bar,
                            progress_args=(downloading_message, start_time, last_update_time)
                        )
                    else:
                        await client.send_photo(
                            chat_id=message.chat.id,
                            photo=media["filename"]
                        )

            await downloading_message.delete()
            for media in media_files:
                if os.path.exists(media["filename"]):
                    os.remove(media["filename"])
                    logger.info(f"Deleted media file: {media['filename']}")
                if media["thumbnail"] and os.path.exists(media["thumbnail"]):
                    os.remove(media["thumbnail"])
                    logger.info(f"Deleted thumbnail file: {media['thumbnail']}")

        except Exception as e:
            logger.error(f"Error processing Instagram content: {e}")
            await downloading_message.edit_text(
                "**Sorry The Media Not Found**", parse_mode=ParseMode.MARKDOWN
            )
            if 'media_files' in locals():
                for media in media_files:
                    if os.path.exists(media["filename"]):
                        os.remove(media["filename"])
                        logger.info(f"Deleted media file on error: {media['filename']}")
                    if media["thumbnail"] and os.path.exists(media["thumbnail"]):
                        os.remove(media["thumbnail"])
                        logger.info(f"Deleted thumbnail file on error: {media['thumbnail']}")
