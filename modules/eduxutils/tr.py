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
from config import COMMAND_PREFIX, OCR_WORKER_URL, IMGAI_SIZE_LIMIT
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

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
            LOGGER.info(f"Converted image {image_path} to base64")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        LOGGER.error(f"Error converting image to base64: {e}")
        raise

# Google Translate Library
def translate_text(text: str, target_lang: str) -> str:
    try:
        translation = translator.translate(text, dest=target_lang)
        LOGGER.info(f"Translated text to {target_lang}")
        return translation.text
    except Exception as e:
        LOGGER.error(f"Translation error: {e}")
        raise

async def ocr_extract_text(client: Client, message: Message) -> str:
    photo_path = None
    try:
        LOGGER.info("Downloading image for OCR...")
        photo_path = await client.download_media(
            message=message.reply_to_message,
            file_name=f"ocr_temp_{message.id}.jpg"
        )

        LOGGER.info("Converting image to base64 for OCR...")
        try:
            img_base64 = image_to_base64(photo_path)
        except Exception as e:
            await notify_admin(client, "/tr ocr", e, message)
            raise

        LOGGER.info("Sending image to OCR API...")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OCR_WORKER_URL,
                json={"imageBase64": img_base64, "mimeType": "image/jpeg"},
                timeout=15
            ) as response:
                if response.status != 200:
                    LOGGER.error(f"OCR API returned non-200 status: {response.status}")
                    raise Exception(f"OCR API failed with status: {response.status}")
                
                result = await response.json()
                text = result.get('text', '')
                if not text:
                    LOGGER.warning("No text extracted from image")
                else:
                    LOGGER.info("Successfully extracted text from image")
                return text
    except Exception as e:
        LOGGER.error(f"OCR Error: {e}")
        await notify_admin(client, "/tr ocr", e, message)
        raise
    finally:
        if photo_path and os.path.exists(photo_path):
            os.remove(photo_path)
            LOGGER.info(f"Deleted temporary image file: {photo_path}")

async def translate_handler(client: Client, message: Message):
    # Check if user is banned
    user_id = message.from_user.id if message.from_user else None
    if user_id and banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /tr")
        return

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
            LOGGER.warning(f"Invalid command format: {message.text}")
            return
        target_lang = message.command[1].lower()
        text_to_translate = " ".join(message.command[2:]) if not (photo_mode or (message.reply_to_message and message.reply_to_message.text)) else None

    if target_lang not in LANGUAGES:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Invalid language code!**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.warning(f"Invalid language code: {target_lang}")
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
            LOGGER.warning("No text provided for translation")
            return
    elif photo_mode:
        if not message.reply_to_message.photo:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Reply to a valid photo for OCR!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning("No valid photo provided for OCR")
            return
    else:
        await client.send_message(
            chat_id=message.chat.id,
            text="**❌ Provide text or reply to a photo!**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.warning("No valid input provided for translation")
        return

    # Send processing message
    loading_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Translating Your Input...✨**",
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
                LOGGER.warning("No valid text extracted from image")
                await notify_admin(client, "/tr ocr", Exception("No valid text extracted from image"), message)
                return

        # Translate the text
        try:
            translated_text = translate_text(text_to_translate, target_lang)
        except Exception as e:
            await notify_admin(client, "/tr translate", e, message)
            raise

        await loading_message.edit(translated_text, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Sent translation to {target_lang} in chat {message.chat.id}")

    except Exception as e:
        LOGGER.error(f"Translation handler error: {e}")
        await notify_admin(client, "/tr", e, message)
        await loading_message.edit(
            text="**❌ Translation API Error**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_tr_handler(app: Client):
    @app.on_message(filters.command(["tr", "translate"] + [f"tr{code}" for code in LANGUAGES.keys()], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def tr_command(client: Client, message: Message):
        await translate_handler(client, message)