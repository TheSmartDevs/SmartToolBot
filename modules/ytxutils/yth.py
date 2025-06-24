# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
import re
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Use LOGGER and notify_admin
from core import banned_users           # Add banned user check

def youtube_parser(url):
    reg_exp = r"(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})"
    try:
        match = re.search(reg_exp, url)
        return match.group(1) if match else False
    except Exception as e:
        LOGGER.error(f"Error parsing YouTube URL {url}: {e}")
        return False

async def handle_yth_command(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    # Await the banned_users check (Motor async)
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(
            chat_id=message.chat.id,
            text="**✘Sorry You're Banned From Using Me↯**",
            parse_mode=ParseMode.HTML
        )
        return

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
        LOGGER.error(f"Error fetching YouTube thumbnail for URL {youtube_url}: {e}")
        error_msg = "<b>Sorry Bro YouTube Thumbnail API Dead</b>"
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.id,
            text=error_msg,
            parse_mode=ParseMode.HTML
        )
        await notify_admin(client, "/yth", e, message)

def setup_yth_handler(app: Client):
    @app.on_message(filters.command("yth", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def yth_command(client: Client, message: Message):
        await handle_yth_command(client, message)
