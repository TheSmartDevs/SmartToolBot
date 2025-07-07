# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import aiohttp
import asyncio
import os
import base64
from io import BytesIO
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, OCR_WORKER_URL, IMGAI_SIZE_LIMIT, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

async def ocr_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY)
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>❌ Please reply to a photo to extract text.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    processing_msg = await client.send_message(
        chat_id=message.chat.id,
        text="<b>Processing Your Request...✨</b>",
        parse_mode=ParseMode.HTML
    )

    photo_path = None

    try:
        LOGGER.info("Downloading image...")
        photo_path = await client.download_media(
            message=message.reply_to_message,
            file_name=f"ocr_temp_{message.id}.jpg"
        )

        LOGGER.info("Converting image to base64...")
        img_base64 = image_to_base64(photo_path)

        LOGGER.info("Sending image to OCR API...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OCR_WORKER_URL,
                json={"imageBase64": img_base64, "mimeType": "image/jpeg"},
                timeout=15
            ) as response:
                if response.status != 200:
                    LOGGER.error(f"API returned non-200 status: {response.status}")
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=processing_msg.id,
                        text="<b>❌ Sorry Bro OCR API Dead</b>",
                        parse_mode=ParseMode.HTML
                    )
                    await notify_admin(client, "/ocr", Exception(f"API returned status {response.status}"), message)
                    return

                result = await response.json()

        LOGGER.info(f"OCR API Response: {result}")
        text = result.get('text', '')

        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.id,
            text=text if text else "<b>❌ No text found in image.</b>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except asyncio.TimeoutError as e:
        LOGGER.error("TimeoutError: OCR API request timed out")
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.id,
            text="<b>❌ Sorry Bro OCR API Dead</b>",
            parse_mode=ParseMode.HTML
        )
        await notify_admin(client, "/ocr", e, message)
    except Exception as e:
        LOGGER.error(f"OCR Error: {str(e)}")
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.id,
            text="<b>❌ Sorry Bro OCR API Dead</b>",
            parse_mode=ParseMode.HTML
        )
        await notify_admin(client, "/ocr", e, message)
    finally:
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            LOGGER.info(f"Deleted temporary image file: {photo_path}")

def setup_ocr_handler(app: Client):
    @app.on_message(filters.command(["ocr", ".ocr"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def ocr_extract(client: Client, message: Message):
        await ocr_handler(client, message)

def image_to_base64(image_path: str, max_size: int = IMGAI_SIZE_LIMIT) -> str:
    file_size = os.path.getsize(image_path)
    if file_size > max_size:
        raise ValueError(f"Image too large. Max {max_size/1000000}MB allowed")

    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
