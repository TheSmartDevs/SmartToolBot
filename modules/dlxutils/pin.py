import os
import re
import asyncio
import time
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, progress_bar, notify_admin
from core import banned_users
logger = LOGGER
class Config:
    TEMP_DIR = Path("./downloads")
Config.TEMP_DIR.mkdir(exist_ok=True)
class PinterestDownloader:
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
    async def sanitize_filename(self, title: str) -> str:
        title = re.sub(r'[<>:"/\\|?*]', '', title[:50]).strip()
        return f"{title.replace(' ', '_')}_{int(time.time())}"
    async def download_media(self, url: str, downloading_message: Message) -> Optional[dict]:
        self.temp_dir.mkdir(exist_ok=True)
        api_url = f"https://pin-teal.vercel.app/dl?url={url}"
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=100),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(api_url) as response:
                    logger.info(f"API request to {api_url} returned status {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"API response: {data}")
                        if data.get("status") != "success":
                            logger.error("API response status is not success")
                            await downloading_message.edit_text("**Unable To Extract Media**", parse_mode=ParseMode.MARKDOWN)
                            return None
                        media = data.get("media", [])
                        title = data.get("title", "Pinterest Media")
                        high_quality_video = None
                        thumbnail = None
                        for item in media:
                            if item.get("type") == "video/mp4" and (not high_quality_video or "720p" in item.get("quality")):
                                high_quality_video = item.get("url")
                            if item.get("type") == "image/jpeg" and item.get("quality") == "Thumbnail":
                                thumbnail = item.get("url")
                        if not high_quality_video and not thumbnail:
                            logger.error("No suitable media found in API response")
                            await downloading_message.edit_text("**Unable To Extract Media**", parse_mode=ParseMode.MARKDOWN)
                            return None
                        await downloading_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
                        safe_title = await self.sanitize_filename(title)
                        result = {'title': title, 'webpage_url': url}
                        if high_quality_video:
                            video_filename = self.temp_dir / f"{safe_title}.mp4"
                            await self._download_file(session, high_quality_video, video_filename)
                            result['video_filename'] = str(video_filename)
                            if thumbnail:
                                thumbnail_filename = self.temp_dir / f"{safe_title}_thumb.jpg"
                                await self._download_file(session, thumbnail, thumbnail_filename)
                                result['thumbnail_filename'] = str(thumbnail_filename)
                        else:
                            image_filename = self.temp_dir / f"{safe_title}.jpg"
                            await self._download_file(session, thumbnail, image_filename)
                            result['image_filename'] = str(image_filename)
                        return result
                    logger.error(f"API request failed: HTTP status {response.status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Pinterest download error: {e}")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}pnt", e, downloading_message)
            return None
        except asyncio.TimeoutError:
            logger.error("Request to Pinterest API timed out")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}pnt", asyncio.TimeoutError("Request to Pinterest API timed out"), downloading_message)
            return None
        except Exception as e:
            logger.error(f"Pinterest download error: {e}")
            await notify_admin(downloading_message._client, f"{COMMAND_PREFIX}pnt", e, downloading_message)
            return None
    async def _download_file(self, session: aiohttp.ClientSession, url: str, dest: Path):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    logger.info(f"Downloading media from {url} to {dest}")
                    async with aiofiles.open(dest, mode='wb') as f:
                        async for chunk in response.content.iter_chunked(1024 * 1024):
                            await f.write(chunk)
                    logger.info(f"Media downloaded successfully to {dest}")
                else:
                    logger.error(f"Failed to download file: HTTP status {response.status}")
                    raise Exception(f"Failed to download file: {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Error downloading file from {url}: {e}")
            await notify_admin(None, f"{COMMAND_PREFIX}pnt", e, None)
            raise
def setup_pinterest_handler(app: Client):
    pin_downloader = PinterestDownloader(Config.TEMP_DIR)
    command_prefix_regex = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"
    @app.on_message(
        filters.regex(rf"^{command_prefix_regex}(pnt|pint)(\s+https?://(pin\.it|in\.pinterest\.com|www\.pinterest\.com)/\S+)?$") &
        (filters.private | filters.group)
    )
    async def pin_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            return
        url = None
        if message.reply_to_message and message.reply_to_message.text:
            match = re.search(r"https?://(pin\.it|in\.pinterest\.com|www\.pinterest\.com)/\S+", message.reply_to_message.text)
            if match:
                url = match.group(0)
        if not url:
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) > 1:
                match = re.search(r"https?://(pin\.it|in\.pinterest\.com|www\.pinterest\.com)/\S+", command_parts[1])
                if match:
                    url = match.group(0)
        if not url:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please provide a Pinterest link**",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.warning(f"No Pinterest URL provided, user: {user_id or 'unknown'}, chat: {message.chat.id}")
            return
        logger.info(f"Pinterest URL received: {url}, user: {user_id or 'unknown'}, chat: {message.chat.id}")
        downloading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Searching The Media**",
            parse_mode=ParseMode.MARKDOWN
        )
        try:
            media_info = await pin_downloader.download_media(url, downloading_message)
            if not media_info:
                await downloading_message.edit_text("**Unable To Extract Media**", parse_mode=ParseMode.MARKDOWN)
                logger.error(f"Failed to download media for URL: {url}")
                return
            start_time = time.time()
            last_update_time = [start_time]
            if 'video_filename' in media_info:
                thumbnail = media_info.get('thumbnail_filename')
                async with aiofiles.open(media_info['video_filename'], 'rb'):
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=media_info['video_filename'],
                        thumb=thumbnail,
                        supports_streaming=True,
                        progress=progress_bar,
                        progress_args=(downloading_message, start_time, last_update_time)
                    )
            elif 'image_filename' in media_info:
                async with aiofiles.open(media_info['image_filename'], 'rb'):
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=media_info['image_filename'],
                        progress=progress_bar,
                        progress_args=(downloading_message, start_time, last_update_time)
                    )
            await downloading_message.delete()
            for key in ['video_filename', 'thumbnail_filename', 'image_filename']:
                if key in media_info and os.path.exists(media_info[key]):
                    os.remove(media_info[key])
                    logger.info(f"Deleted file: {media_info[key]}")
        except Exception as e:
            logger.error(f"Error processing Pinterest media: {e}")
            await notify_admin(client, f"{COMMAND_PREFIX}pnt", e, downloading_message)
            await downloading_message.edit_text("**Pinterest Downloader API Dead**", parse_mode=ParseMode.MARKDOWN)
