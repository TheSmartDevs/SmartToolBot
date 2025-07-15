# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
from io import BytesIO
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import google.generativeai as genai
from config import COMMAND_PREFIX, IMGAI_SIZE_LIMIT, BAN_REPLY, OCR_API_KEY, MODEL_NAME
from utils import LOGGER, notify_admin
from core import banned_users

def setup_ocr_handler(app: Client):
    genai.configure(api_key=OCR_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

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

            if os.path.getsize(photo_path) > IMGAI_SIZE_LIMIT:
                raise ValueError(f"Image too large. Max {IMGAI_SIZE_LIMIT/1000000}MB allowed")

            LOGGER.info("Processing image for OCR with GeminiAI...")
            with Image.open(photo_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                response = model.generate_content(["Extract text from this image of all lang", img])
                text = response.text

                LOGGER.info(f"OCR Response: {text}")
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=processing_msg.id,
                    text=text if text else "<b>❌ No readable text found in image.</b>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )

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

    @app.on_message(filters.command(["ocr"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def ocr_extract(client: Client, message: Message):
        await ocr_handler(client, message)
