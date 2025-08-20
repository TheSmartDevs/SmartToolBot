import os
import aiohttp
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import MessageIdInvalid
from config import COMMAND_PREFIX
from utils import notify_admin, LOGGER
import threading

API_KEY = "23nfCEipDijgVv6SH14oktJe"
user_daily_limits = {}
daily_limits_lock = threading.Lock()

def generate_unique_filename(base_name: str) -> str:
    if os.path.exists(base_name):
        count = 1
        name, ext = os.path.splitext(base_name)
        while True:
            new_name = f"{name}_{count}{ext}"
            if not os.path.exists(new_name):
                return new_name
            count += 1
    return base_name

async def remove_bg(buffer: bytes) -> tuple:
    headers = {"X-API-Key": API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field("image_file", buffer, filename="image.png", content_type="image/png")
            async with session.post("https://api.remove.bg/v1.0/removebg", headers=headers, data=form_data) as resp:
                if "image" not in resp.headers.get("content-type", ""):
                    return False, await resp.json()
                output_filename = generate_unique_filename("no_bg.png")
                async with aiofiles.open(output_filename, "wb") as out_file:
                    await out_file.write(await resp.read())
                return True, output_filename
    except Exception as e:
        return False, {"title": "Unknown Error", "errors": [{"detail": str(e)}]}

def setup_bg_handler(app: Client):
    @app.on_message(filters.command(["rmbg"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def rmbg_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        with daily_limits_lock:
            if user_id not in user_daily_limits:
                user_daily_limits[user_id] = 10
            if user_daily_limits[user_id] <= 0:
                await client.send_message(message.chat.id, "**You have reached your daily limit of 10 background removals.**")
                return
        replied = message.reply_to_message
        valid_photo = replied and replied.photo
        valid_doc = replied and replied.document and replied.document.mime_type and replied.document.mime_type.startswith("image/")
        if not (valid_photo or valid_doc):
            await client.send_message(message.chat.id, "**Reply to a photo or image file to remove background**")
            return
        loading_message = await client.send_message(message.chat.id, "**Removing background...**")
        try:
            file_id = replied.photo.file_id if valid_photo else replied.document.file_id
            file_obj = await client.download_media(file_id, in_memory=True)
            buffer = file_obj.getvalue()
            success, result = await remove_bg(buffer)
            if not success:
                await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry Bro Removal Failed**")
                await notify_admin(client, "/rmbg", result, message)
                return
            with daily_limits_lock:
                user_daily_limits[user_id] -= 1
            await client.send_document(message.chat.id, document=result, caption=f"✅ Background removed!\n{user_daily_limits[user_id]} removals remaining today.")
            try:
                await client.delete_messages(message.chat.id, loading_message.id)
            except MessageIdInvalid:
                pass
        except Exception as e:
            LOGGER.error(f"rmbg error: {str(e)}")
            try:
                await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry Bro Removal Failed**")
            except MessageIdInvalid:
                await client.send_message(message.chat.id, "**Sorry Bro Removal Failed**")
            await notify_admin(client, "/rmbg", e, message)
        finally:
            if os.path.exists(result):
                try:
                    os.remove(result)
                except Exception:
                    LOGGER.warning(f"Cleanup error for {result}")
