#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import requests
import time
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from urllib.parse import quote
from utils import notify_admin  # Import notify_admin
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Webss API endpoint
WEBSS_API_URL = "https://webss.yasirapi.eu.org/api"
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

async def try_different_url_formats(base_url: str, api_base_url: str):
    """Try different URL formats in sequence"""
    url_formats = []
    
    # If URL doesn't have http/https already
    if not base_url.startswith(('http://', 'https://')):
        # First try with https://
        if not base_url.startswith('www.'):
            url_formats.append(f"https://{base_url}")
            url_formats.append(f"https://www.{base_url}")
            url_formats.append(f"http://{base_url}")
            url_formats.append(f"http://www.{base_url}")
        else:
            url_formats.append(f"https://{base_url}")
            url_formats.append(f"http://{base_url}")
    else:
        # URL already has scheme, just try as is
        url_formats.append(base_url)
    
    for url in url_formats:
        encoded_url = quote(url, safe='')
        api_url = f"{api_base_url}?url={encoded_url}&width=1280&height=720&fullPage=false&delay=2000&quality=85"
        
        try:
            response = await fetch_screenshot(api_url, retries=1)  # Only try once per format
            return response, url
        except Exception as e:
            logger.error(f"Failed to fetch screenshot for {url}: {e}")
            continue
    
    # If all formats failed
    return None, None

async def fetch_screenshot(api_url: str, retries: int = 3, timeout: int = 15):
    """Fetch screenshot with improved retry mechanism"""
    for attempt in range(retries):
        try:
            response = requests.get(
                api_url,
                stream=True,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
                }
            )
            response.raise_for_status()
            
            # Check file size early
            content_length = int(response.headers.get('content-length', 0))
            if content_length > MAX_FILE_SIZE:
                raise ValueError(f"Screenshot too large ({content_length/1024/1024:.1f}MB)")
                
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = min(5, 2 * (attempt + 1))  # Exponential backoff with max 5s
                await asyncio.sleep(wait_time)
                continue
            logger.error(f"Failed to fetch screenshot after {retries} attempts: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in fetch_screenshot: {e}")
            raise

def setup_ss_handler(app):
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
            # Try different URL formats
            start_time = time.time()
            response, successful_url = await try_different_url_formats(url, WEBSS_API_URL)
            
            if not response:
                raise ValueError("Failed to access URL with any combination of prefixes")

            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                raise ValueError(f"Unexpected content type: {content_type}")

            # Generate a unique filename
            timestamp = int(time.time())
            temp_file = f"screenshot_{timestamp}.jpg"

            # Download without progress updates
            with open(temp_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

            # Verify file size before sending
            file_size = os.path.getsize(temp_file)
            if file_size > MAX_FILE_SIZE:
                raise ValueError(f"Resulting file too large ({file_size/1024/1024:.1f}MB)")

            # Send with caption that includes timing info
            elapsed = time.time() - start_time
            await client.send_photo(
                chat_id=message.chat.id,
                photo=temp_file,
                caption=f"**🌐 Screenshot of:** `{successful_url}`\n"
                        f"⏱ Captured in {elapsed:.1f}s | 📦 Size: {file_size/1024:.1f}KB",
                parse_mode=ParseMode.MARKDOWN
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
                logger.warning(f"Failed to edit processing message: {edit_error}")
            logger.error(f"Error in capture_screenshot: {e}")
            # Notify admins of error
            await notify_admin(client, "/ss", e, message)
        finally:
            # Clean up in all cases
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to remove temp file: {cleanup_error}")
