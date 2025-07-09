# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

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
ACCESS_KEY = "Z8LQ6Z0DsTQV_A"
MAX_FILE_SIZE = 5 * 1024 * 1024

def validate_url(url: str) -> bool:
    return '.' in url and len(url) < 2048

def normalize_url(url: str) -> str:
    if url.startswith(('http://', 'https://')):
        return url
    else:
        return f"https://{url}"

async def fetch_screenshot(url: str, retries=3, backoff_factor=1.0):
    api_url = f"{SCREENSHOT_API_URL}?access_key={ACCESS_KEY}&url={quote(url)}&format=jpg&block_ads=true&block_cookie_banners=true&block_banners_by_heuristics=false&block_trackers=true&delay=0&timeout=60&response_type=by_format&image_quality=80"

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    response.raise_for_status()

                    content_type = response.headers.get('Content-Type', '')
                    if 'image' not in content_type:
                        raise ValueError(f"Unexpected content type: {content_type}")

                    content_length = int(response.headers.get('Content-Length', 0))
                    if content_length > MAX_FILE_SIZE:
                        raise ValueError(f"Screenshot too large ({content_length / 1024 / 1024:.1f}MB)")

                    return response

        except aiohttp.ClientConnectionError as e:
            if attempt < retries - 1:
                sleep_time = backoff_factor * (2 ** attempt)
                LOGGER.warning(f"Connection error on attempt {attempt + 1}: {e}. Retrying in {sleep_time}s...")
                await asyncio.sleep(sleep_time)
                continue
            LOGGER.error(f"Failed to fetch screenshot after {retries} attempts: {e}")
            return None
        except aiohttp.ClientError as e:
            LOGGER.error(f"Failed to fetch screenshot: {e}")
            return None

def setup_ss_handler(app: Client):
    @app.on_message(filters.command(["ss", "sshot", "screenshot", "snap"], prefixes=COMMAND_PREFIX) & 
                   (filters.private | filters.group))
    async def capture_screenshot(client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(
                chat_id=message.chat.id,
                text=BAN_REPLY,
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if len(message.command) < 2:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Please provide a URL after the command**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        url = message.command[1].strip()

        if not validate_url(url):
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Invalid URL format**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        processing_msg = await client.send_message(
            chat_id=message.chat.id,
            text="**Capturing ScreenShot Please Wait**",
            parse_mode=ParseMode.MARKDOWN
        )

        temp_file = None
        try:
            url = normalize_url(url)

            start_time = time.time()
            response = await fetch_screenshot(url)

            if not response:
                raise ValueError("Failed to capture screenshot.")

            timestamp = int(time.time())
            temp_file = f"screenshot_{timestamp}.jpg"

            async with aiofiles.open(temp_file, 'wb') as file:
                async for chunk in response.content.iter_chunked(8192):
                    await file.write(chunk)

            file_size = os.path.getsize(temp_file)
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"Resulting file too large ({file_size/1024/1024:.1f}MB)")

            await client.send_photo(
                chat_id=message.chat.id,
                photo=temp_file
            )

            await client.delete_messages(
                chat_id=processing_msg.chat.id,
                message_ids=processing_msg.id
            )

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
            LOGGER.error(f"Error in capture_screenshot: {e}")
            await notify_admin(client, "/ss", e, message)
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    LOGGER.warning(f"Failed to remove temp file: {cleanup_error}")
