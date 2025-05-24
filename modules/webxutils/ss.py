# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import requests
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from urllib.parse import quote
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
import logging

# ScreenshotOne API endpoint
SCREENSHOT_API_URL = "https://api.screenshotone.com/take"
ACCESS_KEY = "Z8LQ6Z0DsTQV_A"  # Your API access key
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit for Telegram photos

def validate_url(url: str) -> bool:
    """Basic URL validation for user input"""
    return '.' in url and len(url) < 2048

def normalize_url(url: str) -> str:
    """Add scheme if missing"""
    if url.startswith(('http://', 'https://')):
        return url
    else:
        return f"https://{url}"

async def fetch_screenshot(url: str):
    """Fetch screenshot from ScreenshotOne API"""
    api_url = f"{SCREENSHOT_API_URL}?access_key={ACCESS_KEY}&url={quote(url)}&format=jpg&block_ads=true&block_cookie_banners=true&block_banners_by_heuristics=false&block_trackers=true&delay=0&timeout=60&response_type=by_format&image_quality=80"

    try:
        response = requests.get(api_url, stream=True)
        response.raise_for_status()

        # Check content type and size
        content_type = response.headers.get('Content-Type', '')
        if 'image' not in content_type:
            raise ValueError(f"Unexpected content type: {content_type}")

        # Check file size
        content_length = int(response.headers.get('Content-Length', 0))
        if content_length > MAX_FILE_SIZE:
            raise ValueError(f"Screenshot too large ({content_length / 1024 / 1024:.1f}MB)")

        return response

    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Failed to fetch screenshot: {e}")
        return None

def setup_ss_handler(app: Client):
    @app.on_message(filters.command(["ss", "sshot", "screenshot", "snap"], prefixes=COMMAND_PREFIX) & 
                   (filters.private | filters.group))
    async def capture_screenshot(client, message: Message):
        """Handle screenshot capture command"""
        # Extract URL from the command
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
            # Normalize URL
            url = normalize_url(url)

            # Fetch screenshot from ScreenshotOne API
            start_time = time.time()
            response = await fetch_screenshot(url)

            if not response:
                raise ValueError("Failed to capture screenshot.")

            # Generate a unique filename
            timestamp = int(time.time())
            temp_file = f"screenshot_{timestamp}.jpg"

            # Save the image
            with open(temp_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            # Verify file size before sending
            file_size = os.path.getsize(temp_file)
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"Resulting file too large ({file_size/1024/1024:.1f}MB)")

            # Send the photo without caption
            await client.send_photo(
                chat_id=message.chat.id,
                photo=temp_file
            )

            # Delete loading message after successful screenshot send
            await client.delete_messages(
                chat_id=processing_msg.chat.id,
                message_ids=processing_msg.id
            )

        except Exception as e:
            # For ANY error, edit the message to "Sorry Bro API Dead"
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
            # Notify admins of error
            await notify_admin(client, "/ss", e, message)
        finally:
            # Clean up in all cases
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    LOGGER.warning(f"Failed to remove temp file: {cleanup_error}")
