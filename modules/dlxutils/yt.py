# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

import os
import re
import io
import math
import time
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from concurrent.futures import ThreadPoolExecutor
from moviepy import VideoFileClip
from PIL import Image
import yt_dlp
from config import COMMAND_PREFIX, YT_COOKIES_PATH, VIDEO_RESOLUTION, MAX_VIDEO_SIZE
from utils import LOGGER, progress_bar, notify_admin  # Use LOGGER from utils
from core import banned_users  # Check if user is banned

# Use the imported LOGGER
logger = LOGGER

# Headers Configuration
class Config:
    TEMP_DIR = Path("temp")
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

Config.TEMP_DIR.mkdir(exist_ok=True)
executor = ThreadPoolExecutor(max_workers=6)

def sanitize_filename(title: str) -> str:
    title = re.sub(r'[<>:"/\\|?*]', '', title[:50]).replace(' ', '_')
    return f"{title}_{int(time.time())}"

def format_size(size_bytes: int) -> str:
    if not size_bytes:
        return "0B"
    units = ("B", "KB", "MB", "GB")
    i = int(math.log(size_bytes, 1024))
    return f"{round(size_bytes / (1024 ** i), 2)} {units[i]}"

def format_duration(seconds: int) -> str:
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

async def get_video_duration(video_path: str) -> float:
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        logger.info(f"Video duration retrieved: {duration} seconds for {video_path}")
        return duration
    except Exception as e:
        logger.error(f"Failed to get duration for {video_path}: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}yt", e, None)
        return 0.0

def youtube_parser(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats and return a standardized URL.
    """
    reg_exp = r"(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})"
    match = re.search(reg_exp, url)
    if match:
        video_id = match.group(1)
        standardized_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Parsed YouTube URL: {standardized_url}")
        return standardized_url
    logger.warning(f"Invalid YouTube URL: {url}")
    return None

def get_ydl_opts(output_path: str, is_audio: bool = False) -> dict:
    width, height = VIDEO_RESOLUTION
    base = {
        'outtmpl': output_path + ('.%(ext)s' if is_audio else ''),
        'cookiefile': YT_COOKIES_PATH,
        'quiet': True,
        'noprogress': True,
        'nocheckcertificate': True,
    }
    if is_audio:
        base.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })
    else:
        base.update({
            'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
        })
    logger.info(f"YDL options configured for {'audio' if is_audio else 'video'} download")
    return base

async def download_media(url: str, is_audio: bool, status: Message) -> Tuple[Optional[dict], Optional[str]]:
    # Parse and validate URL
    parsed_url = youtube_parser(url)
    if not parsed_url:
        await status.edit_text("**Invalid YouTube ID Or URL**", parse_mode=ParseMode.MARKDOWN)
        logger.error(f"Invalid YouTube URL provided: {url}")
        # Notify admins
        await notify_admin(status._client, f"{COMMAND_PREFIX}yt", Exception("Invalid YouTube URL"), status)
        return None, "Invalid YouTube URL"
    
    try:
        # Wrap metadata fetching in a timeout
        with yt_dlp.YoutubeDL({'cookiefile': YT_COOKIES_PATH, 'quiet': True}) as ydl:
            info = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(executor, ydl.extract_info, parsed_url, False),
                timeout=30
            )
        
        if not info:
            await status.edit_text(f"**Sorry Bro {'Audio' if is_audio else 'Video'} Not Found**", parse_mode=ParseMode.MARKDOWN)
            logger.error(f"No media info found for URL: {parsed_url}")
            # Notify admins
            await notify_admin(status._client, f"{COMMAND_PREFIX}yt", Exception("No media info found"), status)
            return None, "No media info found"
        
        # Check duration (2 hours = 7200 seconds)
        duration = info.get('duration', 0)
        if duration > 7200:
            await status.edit_text(f"**Sorry Bro {'Audio' if is_audio else 'Video'} Is Over 2hrs**", parse_mode=ParseMode.MARKDOWN)
            logger.error(f"Media duration exceeds 2 hours: {duration} seconds")
            # Notify admins
            await notify_admin(status._client, f"{COMMAND_PREFIX}yt", Exception("Media duration exceeds 2 hours"), status)
            return None, "Media duration exceeds 2 hours"
        
        # Instantly edit status to "Found" after metadata is fetched
        await status.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Media found: {info.get('title', 'Unknown')} ({'audio' if is_audio else 'video'})")
        
        title = info.get('title', 'Unknown')
        safe_title = sanitize_filename(title)
        output_path = f"{Config.TEMP_DIR}/{safe_title}"
        
        opts = get_ydl_opts(output_path, is_audio)
        with yt_dlp.YoutubeDL(opts) as ydl:
            await asyncio.get_event_loop().run_in_executor(executor, ydl.download, [parsed_url])
        
        file_path = f"{output_path}.mp3" if is_audio else f"{output_path}.mp4"
        if not os.path.exists(file_path):
            await status.edit_text(f"**Sorry Bro {'Audio' if is_audio else 'Video'} Not Found**", parse_mode=ParseMode.MARKDOWN)
            logger.error(f"Download failed, file not found: {file_path}")
            # Notify admins
            await notify_admin(status._client, f"{COMMAND_PREFIX}yt", Exception("Download failed, file not found"), status)
            return None, "Download failed"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_VIDEO_SIZE:
            os.remove(file_path)
            await status.edit_text(f"**Sorry Bro {'Audio' if is_audio else 'Video'} Is Over 2GB**", parse_mode=ParseMode.MARKDOWN)
            logger.error(f"File size exceeds 2GB: {file_size} bytes")
            # Notify admins
            await notify_admin(status._client, f"{COMMAND_PREFIX}yt", Exception("File size exceeds 2GB"), status)
            return None, "File exceeds 2GB"
        
        thumbnail_path = await prepare_thumbnail(info.get('thumbnail'), output_path)
        duration = await get_video_duration(file_path) if not is_audio else info.get('duration', 0)
        
        metadata = {
            'file_path': file_path,
            'title': title,
            'views': info.get('view_count', 0),
            'duration': format_duration(int(duration)),
            'file_size': format_size(file_size),
            'thumbnail_path': thumbnail_path
        }
        logger.info(f"{'Audio' if is_audio else 'Video'} metadata prepared: {metadata}")
        
        return metadata, None
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching metadata for URL: {url}")
        await status.edit_text("**Sorry Bro YouTubeDL API Dead**", parse_mode=ParseMode.MARKDOWN)
        # Notify admins
        await notify_admin(status._client, f"{COMMAND_PREFIX}yt", asyncio.TimeoutError("Metadata fetch timed out"), status)
        return None, "Metadata fetch timed out"
    except Exception as e:
        logger.error(f"Download error for URL {url}: {e}")
        await status.edit_text("**Sorry Bro YouTubeDL API Dead**", parse_mode=ParseMode.MARKDOWN)
        # Notify admins
        await notify_admin(status._client, f"{COMMAND_PREFIX}yt", e, status)
        return None, f"Download failed: {str(e)}"

async def prepare_thumbnail(thumbnail_url: str, output_path: str) -> Optional[str]:
    if not thumbnail_url:
        logger.warning("No thumbnail URL provided")
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to fetch thumbnail, status: {resp.status}")
                    # Notify admins
                    await notify_admin(None, f"{COMMAND_PREFIX}yt", Exception(f"Failed to fetch thumbnail, status: {resp.status}"), None)
                    return None
                data = await resp.read()
        
        thumbnail_path = f"{output_path}_thumb.jpg"
        with Image.open(io.BytesIO(data)) as img:
            img.convert('RGB').save(thumbnail_path, "JPEG", quality=85)
        logger.info(f"Thumbnail saved: {thumbnail_path}")
        return thumbnail_path
    except Exception as e:
        logger.error(f"Thumbnail error: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}yt", e, None)
        return None

async def search_youtube(query: str, retries: int = 2) -> Optional[str]:
    opts = {
        'default_search': 'ytsearch1',
        'cookiefile': YT_COOKIES_PATH,
        'quiet': True,
        'simulate': True,
    }
    
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(executor, ydl.extract_info, query, False)
                if info.get('entries'):
                    url = info['entries'][0]['webpage_url']
                    logger.info(f"YouTube search successful, found URL: {url} for query: {query}")
                    return url
                
                # Fallback: Simplify query
                simplified_query = re.sub(r'[^\w\s]', '', query).strip()
                if simplified_query != query:
                    info = await asyncio.get_event_loop().run_in_executor(executor, ydl.extract_info, simplified_query, False)
                    if info.get('entries'):
                        url = info['entries'][0]['webpage_url']
                        logger.info(f"YouTube search successful with simplified query, found URL: {url} for query: {simplified_query}")
                        return url
        except Exception as e:
            logger.error(f"Search error (attempt {attempt + 1}) for query {query}: {e}")
            # Notify admins on last attempt
            if attempt == retries - 1:
                await notify_admin(None, f"{COMMAND_PREFIX}yt", e, None)
            if attempt < retries - 1:
                await asyncio.sleep(1)
    logger.error(f"YouTube search failed after {retries} attempts for query: {query}")
    return None

async def handle_media_request(client: Client, message: Message, query: str, is_audio: bool = False):
    logger.info(f"Handling media request: {'audio' if is_audio else 'video'}, query: {query}, user: {message.from_user.id if message.from_user else 'unknown'}, chat: {message.chat.id}")
    status = await client.send_message(
        message.chat.id,
        f"**Searching The {'Audio' if is_audio else 'Video'}**",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Check if query is a URL
    video_url = youtube_parser(query) if youtube_parser(query) else await search_youtube(query)
    if not video_url:
        await status.edit_text(f"**Sorry Bro {'Audio' if is_audio else 'Video'} Not Found**", parse_mode=ParseMode.MARKDOWN)
        logger.error(f"No video URL found for query: {query}")
        # Notify admins
        await notify_admin(client, f"{COMMAND_PREFIX}yt", Exception("No video URL found"), message)
        return
    
    result, error = await download_media(video_url, is_audio, status)
    if error:
        logger.error(f"Media download failed: {error}")
        return  # Error message already handled in download_media
    
    user_info = (
        f"[{message.from_user.first_name}{' ' + message.from_user.last_name if message.from_user.last_name else ''}](tg://user?id={message.from_user.id})" if message.from_user else
        f"[{message.chat.title}](https://t.me/{message.chat.username or 'this group'})"
    )
    caption = (
        f"🎵 **Title:** `{result['title']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👁️‍🗨️ **Views:** {result['views']}\n"
        f"**🔗 Url:** [Watch On YouTube]({video_url})\n"
        f"⏱️ **Duration:** {result['duration']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"**Downloaded By** {user_info}"
    )
    
    last_update_time = [0]
    start_time = time.time()
    send_func = client.send_audio if is_audio else client.send_video
    kwargs = {
        'chat_id': message.chat.id,
        'caption': caption,
        'parse_mode': ParseMode.MARKDOWN,
        'thumb': result['thumbnail_path'],
        'progress': progress_bar,
        'progress_args': (status, start_time, last_update_time)
    }
    if is_audio:
        kwargs.update({'audio': result['file_path'], 'title': result['title']})
    else:
        kwargs.update({
            'video': result['file_path'],
            'supports_streaming': True,
            'height': 720,
            'width': 1280,
            'duration': int(await get_video_duration(result['file_path']))
        })
    
    try:
        await send_func(**kwargs)
        logger.info(f"Media uploaded successfully: {'audio' if is_audio else 'video'}, file: {result['file_path']}")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await status.edit_text("**Sorry Bro YouTubeDL API Dead**", parse_mode=ParseMode.MARKDOWN)
        # Notify admins
        await notify_admin(client, f"{COMMAND_PREFIX}yt", e, message)
        return
    
    for path in (result['file_path'], result['thumbnail_path']):
        if path and os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up file: {path}")
    await status.delete()
    logger.info("Status message deleted")

def setup_yt_handler(app: Client):
    prefix = f"[{''.join(map(re.escape, COMMAND_PREFIX))}]"
    
    @app.on_message(filters.regex(rf"^{prefix}(yt|video)(\s+.+)?$") & (filters.private | filters.group))
    async def video_command(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        user_id = message.from_user.id if message.from_user else "unknown"
        chat_id = message.chat.id
        logger.info(f"Video command received from user: {user_id}, chat: {chat_id}, text: {message.text}")
        
        # Check if the message is a reply
        if message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text.strip()
            logger.info(f"Using replied message as query: {query}")
        else:
            # Check if query is provided directly
            query = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else None
            logger.info(f"Using direct query: {query if query else 'none'}")
        
        if not query:
            await client.send_message(
                message.chat.id,
                "**Please provide a video name or link ❌**",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.warning(f"No query provided for video command, user: {user_id}, chat: {chat_id}")
            return
        
        await handle_media_request(client, message, query)
    
    @app.on_message(filters.regex(rf"^{prefix}song(\s+.+)?$") & (filters.private | filters.group))
    async def song_command(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        user_id = message.from_user.id if message.from_user else "unknown"
        chat_id = message.chat.id
        logger.info(f"Song command received from user: {user_id}, chat: {chat_id}, text: {message.text}")
        
        # Check if the message is a reply
        if message.reply_to_message and message.reply_to_message.text:
            query = message.reply_to_message.text.strip()
            logger.info(f"Using replied message as query: {query}")
        else:
            # Check if query is provided directly
            query = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else None
            logger.info(f"Using direct query: {query if query else 'none'}")
        
        if not query:
            await client.send_message(
                message.chat.id,
                "**Please provide a music name or link ❌**",
                parse_mode=ParseMode.MARKDOWN
            )
            logger.warning(f"No query provided for song command, user: {user_id}, chat: {chat_id}")
            return
        
        await handle_media_request(client, message, query, is_audio=True)