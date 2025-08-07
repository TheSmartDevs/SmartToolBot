from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode, ChatMemberStatus
from datetime import datetime
from mimetypes import guess_type
import secrets
import urllib.parse
import asyncio
from config import COMMAND_PREFIX, BAN_REPLY, LOG_CHANNEL_ID
from utils import notify_admin, LOGGER
from core import banned_users

class Server:
    BASE_URL = "https://fdlapi-ed9a85898ea5.herokuapp.com"

async def get_file_properties(message):
    file_name = None
    file_size = 0
    mime_type = None
    if message.document:
        file_name = message.document.file_name
        file_size = message.document.file_size
        mime_type = message.document.mime_type
    elif message.video:
        file_name = getattr(message.video, 'file_name', None)
        file_size = message.video.file_size
        mime_type = message.video.mime_type
    elif message.audio:
        file_name = getattr(message.audio, 'file_name', None)
        file_size = message.audio.file_size
        mime_type = message.audio.mime_type
    elif message.photo:
        file_name = None
        file_size = message.photo[-1].file_size
        mime_type = "image/jpeg"
    elif message.video_note:
        file_name = None
        file_size = message.video_note.file_size
        mime_type = "video/mp4"
    if not file_name:
        attributes = {
            "video": "mp4",
            "audio": "mp3",
            "video_note": "mp4",
            "photo": "jpg",
        }
        for attribute in attributes:
            if getattr(message, attribute, None):
                file_type, file_format = attribute, attributes[attribute]
                break
        else:
            raise ValueError("Invalid media type.")
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"{file_type}-{date}.{file_format}"
    if not mime_type:
        mime_type = guess_type(file_name)[0] or "application/octet-stream"
    return file_name, file_size, mime_type

async def format_file_size(file_size):
    if file_size < 1024 * 1024:
        size = file_size / 1024
        unit = "KB"
    elif file_size < 1024 * 1024 * 1024:
        size = file_size / (1024 * 1024)
        unit = "MB"
    else:
        size = file_size / (1024 * 1024 * 1024)
        unit = "GB"
    return f"{size:.2f} {unit}"

def setup_fdl_handler(app: Client):
    @app.on_message(filters.command(["fdl"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_file_download(client: Client, message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        if not message.reply_to_message:
            await client.send_message(message.chat.id, "**Please Reply To File For Link**", parse_mode=ParseMode.MARKDOWN)
            return
        reply_message = message.reply_to_message
        if not (reply_message.document or reply_message.video or reply_message.photo or reply_message.audio or reply_message.video_note):
            await client.send_message(message.chat.id, "**Please Reply To A Valid File**", parse_mode=ParseMode.MARKDOWN)
            return
        processing_msg = await client.send_message(message.chat.id, "**Processing Your File.....**", parse_mode=ParseMode.MARKDOWN)
        try:
            # Check if bot is admin in the log channel
            bot_member = await client.get_chat_member(LOG_CHANNEL_ID, "me")
            if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=processing_msg.id,
                    text="**Error: Bot must be an admin in the log channel**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            code = secrets.token_urlsafe(6)[:6]
            file_name, file_size, mime_type = await get_file_properties(reply_message)
            file_id = None  # Initialize file_id
            if message.chat.id == LOG_CHANNEL_ID:
                file_id = reply_message.id
                sent = await client.copy_message(
                    chat_id=LOG_CHANNEL_ID,
                    from_chat_id=LOG_CHANNEL_ID,
                    message_id=reply_message.id,
                    caption=code
                )
                file_id = sent.id
            else:
                sent = await reply_message.forward(LOG_CHANNEL_ID)
                file_id = sent.id
                sent = await client.copy_message(
                    chat_id=LOG_CHANNEL_ID,
                    from_chat_id=LOG_CHANNEL_ID,
                    message_id=file_id,
                    caption=code
                )
                file_id = sent.id
            quoted_code = urllib.parse.quote(code)
            base_url = Server.BASE_URL.rstrip('/')
            download_link = f"{base_url}/dl/{file_id}?code={quoted_code}"
            is_video = mime_type.startswith('video') or reply_message.video or reply_message.video_note
            stream_link = f"{base_url}/stream/{file_id}?code={quoted_code}" if is_video else None
            buttons = [
                InlineKeyboardButton("🚀 Download Link", url=download_link)
            ]
            if stream_link:
                buttons.append(InlineKeyboardButton("🖥️ Stream Link", url=stream_link))
            response = (
                f"**✨ Your Links are Ready! ✨**\n\n"
                f"> {file_name}\n\n"
                f"**📂 File Size: {await format_file_size(file_size)}**\n\n"
                f"**🚀 Download Link:** {download_link}\n\n"
            )
            if stream_link:
                response += f"**🖥️ Stream Link:** {stream_link}\n\n"
            response += "**⌛️ Note: Links remain active while the bot is running and the file is accessible.**"
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text=response,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([buttons]),
                disable_web_page_preview=True
            )
            LOGGER.info(f"Generated links for file_id: {file_id}, download: {download_link}, stream: {stream_link}")
        except Exception as e:
            LOGGER.error(f"Error generating links for file_id: {file_id if 'file_id' in locals() else 'unknown'}, error: {str(e)}")
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=processing_msg.id,
                text="**Sorry Failed To Generate Link**",
                parse_mode=ParseMode.MARKDOWN
            )
