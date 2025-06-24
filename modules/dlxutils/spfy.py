# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import time
import requests
import aiohttp
import re
import asyncio
import aiofiles
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional
from config import COMMAND_PREFIX
from utils import LOGGER, progress_bar, notify_admin  # Import LOGGER, progress_bar, and notify_admin from utils
from core import banned_users  # Check if user is banned
import urllib.parse

# Use the imported LOGGER
logger = LOGGER

# Configuration
class Config:
    TEMP_DIR = Path("temp")

Config.TEMP_DIR.mkdir(exist_ok=True)

# ThreadPoolExecutor for blocking I/O operations
executor = ThreadPoolExecutor(max_workers=10)

async def sanitize_filename(title: str) -> str:
    """Sanitize file name by removing invalid characters."""
    title = re.sub(r'[<>:"/\\|?*]', '', title[:50]).strip()
    return f"{title.replace(' ', '_')}_{int(time.time())}"

async def download_image(url: str, output_path: str) -> Optional[str]:
    """Download image from a URL."""
    logger.info(f"Starting download of image from {url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(output_path, 'wb') as file:
                        await file.write(await response.read())
                    logger.info(f"Image downloaded successfully to {output_path}")
                    return output_path
                else:
                    logger.error(f"Failed to download image: HTTP status {response.status}")
                    # Notify admins
                    await notify_admin(None, f"{COMMAND_PREFIX}sp", Exception(f"Failed to download image: HTTP status {response.status}"), None)
    except Exception as e:
        logger.error(f"Failed to download image: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}sp", e, None)
    return None

async def handle_spotify_request(client: Client, message: Message, input_text: Optional[str]):
    # Check if the message is a reply to another message
    if not input_text and message.reply_to_message and message.reply_to_message.text:
        input_text = message.reply_to_message.text.strip()

    if not input_text:
        await client.send_message(
            chat_id=message.chat.id,
            text="**Please provide a track Spotify URL**",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.warning(f"No input provided, user: {message.from_user.id if message.from_user else 'unknown'}, chat: {message.chat.id}")
        return

    # Check if input_text is a URL (starts with http)
    is_url = input_text.lower().startswith('http')

    status_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Searching The Music**",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        async with aiohttp.ClientSession() as session:
            if is_url:
                # Handle Spotify URL
                logger.info(f"Processing Spotify URL: {input_text}")
                api_url = f"https://abirthetech.serv00.net/sp.php?url={urllib.parse.quote(input_text)}"
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Track API response: {data}")
                        if data["status"]:
                            await status_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
                        else:
                            await status_message.edit_text("**Please Provide A Valid Spotify URL ❌**", parse_mode=ParseMode.MARKDOWN)
                            logger.error(f"Invalid Spotify URL: {input_text}")
                            return
                    else:
                        await status_message.edit_text("**❌ Song Not Available On Spotify**", parse_mode=ParseMode.MARKDOWN)
                        logger.error(f"API request failed: HTTP status {response.status}")
                        # Notify admins
                        await notify_admin(client, f"{COMMAND_PREFIX}sp", Exception(f"API request failed: HTTP status {response.status}"), message)
                        return
            else:
                # Handle search query
                logger.info(f"Processing Spotify search query: {input_text}")
                encoded_query = urllib.parse.quote(input_text)
                api_url = f"https://abirthetech.serv00.net/sps.php?q={encoded_query}"
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Search API response: {data}")
                        if data["type"] == "search" and data["data"]:
                            await status_message.edit_text("**Found ☑️ Downloading...**", parse_mode=ParseMode.MARKDOWN)
                            # Use the first result
                            track = data["data"][0]
                            # Fetch track details using the Spotify URL
                            track_url = track["external_urls"]["spotify"]
                            logger.info(f"Selected track: {track['name']} (URL: {track_url})")
                            track_api_url = f"https://abirthetech.serv00.net/sp.php?url={urllib.parse.quote(track_url)}"
                            async with session.get(track_api_url) as track_response:
                                if track_response.status == 200:
                                    data = await track_response.json()
                                    logger.info(f"Track API response: {data}")
                                    if not data["status"]:
                                        await status_message.edit_text("**Song Metadata Unavailable**", parse_mode=ParseMode.MARKDOWN)
                                        logger.error("Song metadata unavailable")
                                        # Notify admins
                                        await notify_admin(client, f"{COMMAND_PREFIX}sp", Exception("Song metadata unavailable"), message)
                                        return
                                else:
                                    await status_message.edit_text("**❌ Song Unavailable Bro Try Later**", parse_mode=ParseMode.MARKDOWN)
                                    logger.error(f"Track API request failed: HTTP status {track_response.status}")
                                    # Notify admins
                                    await notify_admin(client, f"{COMMAND_PREFIX}sp", Exception(f"Track API request failed: HTTP status {track_response.status}"), message)
                                    return
                        else:
                            await status_message.edit_text("**Sorry No Songs Matched To Your Search!**", parse_mode=ParseMode.MARKDOWN)
                            logger.error(f"No songs matched search query: {input_text}")
                            return
                    else:
                        await status_message.edit_text("**❌ Sorry Bro Spotify Search API Dead**", parse_mode=ParseMode.MARKDOWN)
                        logger.error(f"Search API request failed: HTTP status {response.status}")
                        # Notify admins
                        await notify_admin(client, f"{COMMAND_PREFIX}sp", Exception(f"Search API request failed: HTTP status {response.status}"), message)
                        return

            # Extract track details from API response
            title = data["title"]
            artists = data["artist"]
            duration = data["duration"]
            album = data["album"]
            release_date = data["releaseDate"]
            spotify_url = data["spotify_url"]
            download_url = data["download_link"]
            cover_url = data.get("image") or data.get("cover")

            # Download cover image
            cover_path = None
            if cover_url:
                Config.TEMP_DIR.mkdir(exist_ok=True)
                cover_path = Config.TEMP_DIR / f"{await sanitize_filename(title)}.jpg"
                downloaded_path = await download_image(cover_url, str(cover_path))
                if downloaded_path:
                    logger.info(f"Cover image downloaded to {downloaded_path}")
                else:
                    logger.warning("Failed to download cover image")
                    cover_path = None

            # Download audio
            safe_title = await sanitize_filename(title)
            output_filename = Config.TEMP_DIR / f"{safe_title}.mp3"
            logger.info(f"Starting download of audio file from {download_url}")
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(output_filename, 'wb') as file:
                        await file.write(await response.read())
                    logger.info(f"Audio file downloaded successfully to {output_filename}")
                else:
                    await status_message.edit_text("**❌ Sorry Bro Spotify DL API Dead**", parse_mode=ParseMode.MARKDOWN)
                    logger.error(f"Audio download failed: HTTP status {response.status}")
                    # Notify admins
                    await notify_admin(client, f"{COMMAND_PREFIX}sp", Exception(f"Audio download failed: HTTP status {response.status}"), message)
                    return

            # Prepare user info for caption
            if message.from_user:
                user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
            else:
                group_name = message.chat.title or "this group"
                group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
                user_info = f"[{group_name}]({group_url})"

            # Format caption
            audio_caption = (
                f"🌟 **Title**: `{title}`\n"
                f"💥 **Artist**: `{artists}`\n"
                f"✨ **Duration**: `{duration}`\n"
                f"👀 **Album**: `{album}`\n"
                f"🎵 **Release Date**: `{release_date}`\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"**Downloaded By**: {user_info}"
            )

            # Create inline button for Spotify URL
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎸 Listen On Spotify", url=spotify_url)]
            ])

            last_update_time = [0]
            start_time = time.time()

            logger.info("Starting upload of audio file to Telegram")
            await client.send_audio(
                chat_id=message.chat.id,
                audio=str(output_filename),
                caption=audio_caption,
                title=title,
                performer=artists,
                parse_mode=ParseMode.MARKDOWN,
                thumb=str(cover_path) if cover_path else None,
                reply_markup=reply_markup,
                progress=progress_bar,
                progress_args=(status_message, start_time, last_update_time)
            )
            logger.info("Upload of audio successfully completed")

            if os.path.exists(output_filename):
                os.remove(output_filename)
                logger.info(f"Deleted audio file: {output_filename}")
            if cover_path and os.path.exists(cover_path):
                os.remove(cover_path)
                logger.info(f"Deleted cover image: {cover_path}")

            await status_message.delete()
            logger.info("Status message deleted")
    except Exception as e:
        await status_message.edit_text("**❌ Sorry Bro Spotify DL API Dead**", parse_mode=ParseMode.MARKDOWN)
        logger.error(f"Error processing Spotify request: {str(e)}")
        # Notify admins
        await notify_admin(client, status_message, f"{COMMAND_PREFIX}sp", Exception(str(e)))

def setup_spotify_handler(app: Client):
    """Set up the Spotify command handler."""
    # Create a regex pattern from the COMMAND_PREFIX list
    command_prefix_regex = rf"[{''.join(map(re.escape, COMMAND_PREFIX))}]"

    @app.on_message(filters.regex(rf"^{command_prefix_regex}sp(\s+.*)?$") & (filters.private | filters.group))
    async def spotify_command(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        # Check if the message contains a Spotify URL or query
        command_parts = message.text.split(maxsplit=1)
        input_text = command_parts[1].strip() if len(command_parts) > 1 else None
        logger.info(f"Spotify command received: input_text='{input_text or 'None'}', user: {user_id or 'unknown'}, chat: {message.chat.id}")
        await handle_spotify_request(client, message, input_text)
