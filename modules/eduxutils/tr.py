# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
import asyncio
import os
import base64
from io import BytesIO
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from googletrans import Translator, LANGUAGES
import logging
from config import COMMAND_PREFIX, OCR_WORKER_URL, IMGAI_SIZE_LIMIT
from utils import notify_admin  # Import notify_admin from utils

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Google Translator
translator = Translator()

# Image To Base64
def image_to_base64(image_path: str, max_size: int = IMGAI_SIZE_LIMIT) -> str:
    try:
        file_size = os.path.getsize(image_path)
        if file_size > max_size:
            raise ValueError(f"Image too large. Max {max_size/1000000}MB allowed")
        
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        # Cannot use await here; log the error and raise (notify_admin will be handled by caller)
        raise

# Google Translate Library
def translate_text(text: str, target_lang: str) -> str:
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        # Cannot use await here; log the error and raise (notify_admin will be handled by caller)
        raise

async def ocr_extract_text(client: Client, message: Message) -> str:
    photo_path = None
    try:
        logger.info("Downloading image...")
        photo_path = await client.download_media(
            message=message.reply_to_message,
            file_name=f"ocr_temp_{message.id}.jpg"
        )

        logger.info("Converting image to base64...")
        try:
            img_base64 = image_to_base64(photo_path)
        except Exception as e:
            await notify_admin(client, f"{COMMAND_PREFIX}tr", e, message)
            raise

        logger.info("Sending image to OCR API...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OCR_WORKER_URL,
                json={"imageBase64": img_base64, "mimeType": "image/jpeg"},
                timeout=15
            ) as response:
                if response.status != 200:
                    logger.error(f"API returned non-200 status: {response.status}")
                    raise Exception(f"OCR API failed with status: {response.status}")
                
                result = await response.json()
                text = result.get('text', '')
                if not text:
                    logger.warning("No text extracted from image")
                return text
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        await notify_admin(client, f"{COMMAND_PREFIX}tr", e, message)
        raise
    finally:
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            logger.info(f"Deleted temporary image file: {photo_path}")

async def translate_handler(client: Client, message: Message):
    # Check if command is combined format (e.g., /tren)
    combined_format = len(message.command[0]) > 2 and message.command[0][2:].lower() in LANGUAGES
    photo_mode = message.reply_to_message and message.reply_to_message.photo
    text_mode = (message.reply_to_message and message.reply_to_message.text) or (len(message.command) > (1 if combined_format else 2))

    # Determine target language
    if combined_format:
        target_lang = message.command[0][2:].lower()
        text_to_translate = " ".join(message.command[1:]) if not (photo_mode or (message.reply_to_message and message.reply_to_message.text)) else None
    else:
        if len(message.command) < 2:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Invalid language code!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        target_lang = message.command[1].lower()
        text_to_translate = " ".join(message.command[2:]) if not (photo_mode or (message.reply_to_message and message.reply_to_message.text)) else None

    if target_lang not in LANGUAGES:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Invalid language code!**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Handle text input (direct or replied text)
    if text_mode and not photo_mode:
        text_to_translate = message.reply_to_message.text if message.reply_to_message and message.reply_to_message.text else text_to_translate
        if not text_to_translate:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ No text provided to translate!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    elif photo_mode:
        if not message.reply_to_message.photo:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Reply to a valid photo for OCR!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Provide text or reply to a photo!**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Send processing message
    loading_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Translating Your Input...**",
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        # If photo, extract text using OCR
        if photo_mode:
            text_to_translate = await ocr_extract_text(client, message)
            if not text_to_translate:
                await loading_message.edit(
                    text="**No Valid Text Found In The Image**",
                    parse_mode=ParseMode.MARKDOWN
                )
                await notify_admin(client, f"{COMMAND_PREFIX}tr", Exception("No valid text extracted from image"), message)
                return

        # Translate the text
        try:
            translated_text = translate_text(text_to_translate, target_lang)
        except Exception as e:
            await notify_admin(client, f"{COMMAND_PREFIX}tr", e, message)
            raise

        await loading_message.edit(translated_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Translation handler error: {e}")
        await notify_admin(client, f"{COMMAND_PREFIX}tr", e, message)
        await loading_message.edit(
            text="**❌ Translation API Error**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_tr_handler(app: Client):
    @app.on_message(filters.command(["tr", "translate"] + [f"tr{code}" for code in LANGUAGES.keys()], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def tr_command(client: Client, message: Message):
        await translate_handler(client, message)
