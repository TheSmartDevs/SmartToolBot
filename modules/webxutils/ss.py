import os
import aiohttp
import time
import aiofiles
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from urllib.parse import quote
from utils import LOGGER, notify_admin
from core import banned_users

SCREENSHOT_API_URL = "https://api.screenshotone.com/take"
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_url(url: str) -> bool:
    return '.' in url and len(url) < 2048

def normalize_url(url: str) -> str:
    return url if url.startswith(('http://', 'https://')) else f"https://{url}"

async def fetch_screenshot(url: str) -> bytes:
    api_url = f"{SCREENSHOT_API_URL}?url={quote(url)}"
    timeout = aiohttp.ClientTimeout(total=10) 
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                response.raise_for_status()
                content_type = response.headers.get('Content-Type', '')
                if 'image' not in content_type:
                    raise ValueError(f"Unexpected content type: {content_type}")
                content_length = int(response.headers.get('Content-Length', 0))
                if content_length > MAX_FILE_SIZE:
                    raise ValueError(f"Screenshot too large ({content_length / 1024 / 1024:.1f}MB)")
                return await response.read()
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        LOGGER.error(f"Failed to fetch screenshot for {url}: {e}")
        return None

async def save_screenshot(url: str, timestamp: int) -> str:
    screenshot_bytes = await fetch_screenshot(url)
    if not screenshot_bytes:
        return None
    temp_file = f"screenshot_{timestamp}_{hash(url)}.jpg"
    async with aiofiles.open(temp_file, 'wb') as file:
        await file.write(screenshot_bytes)
    file_size = os.path.getsize(temp_file)
    if file_size > MAX_FILE_SIZE:
        os.remove(temp_file)
        return None
    return temp_file

async def capture_screenshots(client, message: Message, urls: list) -> None:
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(chat_id=message.chat.id, text=BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        return

    if not urls:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Please provide at least one URL after the command**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    for url in urls:
        if not validate_url(url):
            await client.send_message(
                chat_id=message.chat.id,
                text=f"**❌ Invalid URL format: {url}**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    processing_msg = await client.send_message(
        chat_id=message.chat.id,
        text="**Capturing ScreenShots Please Wait**",
        parse_mode=ParseMode.MARKDOWN
    )

    timestamp = int(time.time())
    tasks = [save_screenshot(normalize_url(url), timestamp) for url in urls]
    temp_files = await asyncio.gather(*tasks, return_exceptions=True)

    try:
        for i, temp_file in enumerate(temp_files):
            if isinstance(temp_file, Exception):
                LOGGER.error(f"Error processing {urls[i]}: {temp_file}")
                continue
            if temp_file:
                await client.send_photo(chat_id=message.chat.id, photo=temp_file)
                os.remove(temp_file)

        await client.delete_messages(chat_id=processing_msg.chat.id, message_ids=processing_msg.id)

    except Exception as e:
        error_msg = "**Sorry Bro SS Capture API Dead**"
        try:
            await client.edit_message_text(
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.id,
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as edit_error:
            LOGGER.warning(f"Failed to edit processing message: {edit_error}")
        LOGGER.error(f"Error in capture_screenshots: {e}")
        await notify_admin(client, "/ss", e, message)

def setup_ss_handler(app: Client):
    @app.on_message(filters.command(["ss", "sshot", "screenshot", "snap"], prefixes=COMMAND_PREFIX) & 
                   (filters.private | filters.group))
    async def handler(client, message: Message):
        urls = message.command[1:]  
        await capture_screenshots(client, message, urls)

