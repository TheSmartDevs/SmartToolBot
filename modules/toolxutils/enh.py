import aiohttp
import random
from io import BytesIO
from PIL import Image
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import MessageIdInvalid
from config import COMMAND_PREFIX
from utils import notify_admin, LOGGER
import os

user_daily_limits = {}

async def upscale(buffer: bytes, width: int, height: int) -> tuple:
    try:
        random_number = random.randint(1_000_000, 999_999_999_999)
        form_data = aiohttp.FormData()
        form_data.add_field("image_file", buffer, filename="image.jpg", content_type="image/jpeg")
        form_data.add_field("name", str(random_number))
        form_data.add_field("desiredHeight", str(height * 4))
        form_data.add_field("desiredWidth", str(width * 4))
        form_data.add_field("outputFormat", "png")
        form_data.add_field("compressionLevel", "high")
        form_data.add_field("anime", "false")

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://upscalepics.com",
            "Referer": "https://upscalepics.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.upscalepics.com/upscale-to-size", data=form_data, headers=headers) as response:
                if response.status == 200:
                    json_response = await response.json()
                    return json_response.get("bgRemoved", "").strip(), None
                else:
                    return None, f"API request failed with status {response.status}"
    except Exception as e:
        return None, f"Upscale error: {str(e)}"

def setup_enh_handler(app: Client):
    task_queue = asyncio.Queue()

    async def process_tasks():
        while True:
            task = await task_queue.get()
            try:
                await task
            except Exception as e:
                LOGGER.error(f"Task processing error: {str(e)}")
            finally:
                task_queue.task_done()

    @app.on_message(filters.command(["enh"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def enh_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None

        if user_id not in user_daily_limits:
            user_daily_limits[user_id] = 10

        if user_daily_limits[user_id] <= 0:
            await client.send_message(message.chat.id, "**You have reached your daily limit of 10 enhancements.**")
            return

        if not message.reply_to_message or not message.reply_to_message.photo:
            await client.send_message(message.chat.id, "**Reply to a photo to enhance face**")
            return

        async def process_image():
            loading_message = None
            try:
                loading_message = await client.send_message(message.chat.id, "**Enhancing Your Face....**")
                file_id = message.reply_to_message.photo.file_id
                file_path = await client.download_media(file_id, in_memory=True)

                if not file_path:
                    raise Exception("Failed to download image")

                image_buffer = file_path.getvalue()

                with Image.open(BytesIO(image_buffer)) as img:
                    width, height = img.size

                image_url, error = await upscale(image_buffer, width, height)

                if image_url and image_url.startswith("http"):
                    user_daily_limits[user_id] -= 1
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as img_resp:
                            if img_resp.status == 200:
                                img_bytes = await img_resp.read()
                                if not img_bytes:
                                    raise ValueError("Empty image data received from API")
                               
                                img_io = BytesIO(img_bytes)
                                img_io.name = "enhanced.png" 
                                try:
                                    await client.delete_messages(message.chat.id, loading_message.id)
                                except MessageIdInvalid:
                                    LOGGER.warning("Loading message ID invalid, skipping deletion")
                                await client.send_document(
                                    message.chat.id,
                                    document=img_io,
                                    caption=f"✅ Face enhanced!\n{user_daily_limits[user_id]} enhancements remaining today."
                                )
                            else:
                                try:
                                    await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry Enhancer API Dead**")
                                except MessageIdInvalid:
                                    await client.send_message(message.chat.id, "**Sorry Enhancer API Dead**")
                else:
                    try:
                        await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry Enhancer API Dead**")
                    except MessageIdInvalid:
                        await client.send_message(message.chat.id, "**Sorry Enhancer API Dead**")
                    if error:
                        LOGGER.error(f"Enhancer error: {error}")
                        await notify_admin(client, "/enh", error, message)

            except Exception as e:
                LOGGER.error(f"Enhancer error: {str(e)}")
                if loading_message:
                    try:
                        await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry Enhancer API Dead**")
                    except MessageIdInvalid:
                        await client.send_message(message.chat.id, "**Sorry Enhancer API Dead**")
                await notify_admin(client, "/enh", e, message)

        await task_queue.put(process_image())

    app.loop.create_task(process_tasks())
