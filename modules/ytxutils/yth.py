#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
import re
import logging
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def youtube_parser(url):
    # Regular expression to extract YouTube video ID from various URL formats
    reg_exp = r"(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})"
    try:
        match = re.search(reg_exp, url)
        return match.group(1) if match else False
    except Exception as e:
        logger.error(f"Error parsing YouTube URL {url}: {e}")
        return False

async def handle_yth_command(client: Client, message: Message):
    if len(message.command) == 1:
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>❌ Provide a Valid YouTube link</b>",
            parse_mode=ParseMode.HTML
        )
        return

    youtube_url = message.command[1].strip()
    processing_msg = await client.send_message(
        chat_id=message.chat.id,
        text="<b>Fetching YouTube thumbnail...✨</b>",
        parse_mode=ParseMode.HTML
    )

    try:
        video_id = youtube_parser(youtube_url)
        if not video_id:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="<b>Invalid YouTube link Bro ❌</b>",
                parse_mode=ParseMode.HTML
            )
            return
        
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        caption = "<code>Photo Sent</code>"
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=thumbnail_url,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
        await processing_msg.delete()

    except Exception as e:
        logger.error(f"Error fetching YouTube thumbnail for URL {youtube_url}: {e}")
        error_msg = "<b>Sorry Bro YouTube Thumbnail API Dead</b>"
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.id,
            text=error_msg,
            parse_mode=ParseMode.HTML
        )
        # Notify admins of error
        await notify_admin(client, "/yth", e, message)

def setup_yth_handler(app: Client):
    @app.on_message(filters.command("yth", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def yth_command(client: Client, message: Message):
        await handle_yth_command(client, message)
