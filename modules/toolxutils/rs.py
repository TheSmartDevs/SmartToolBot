import os
import aiofiles
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from tempfile import mkstemp
from config import COMMAND_PREFIX
from utils import LOGGER
import asyncio

# Async-safe temp image storage per user
image_store = {}
image_store_lock = asyncio.Lock()

# Format resolutions
RESOLUTIONS = {
    "dp_square": (1080, 1080),
    "widescreen": (1920, 1080),
    "story": (1080, 1920),
    "portrait": (1080, 1620),
    "vertical": (1080, 2160),
    "horizontal": (2160, 1080),
    "standard": (1620, 1080),
    "ig_post": (1080, 1080),
    "tiktok_dp": (200, 200),
    "fb_cover": (820, 312),
    "yt_banner": (2560, 1440),
    "yt_thumb": (1280, 720),
    "x_header": (1500, 500),
    "x_post": (1600, 900),
    "linkedin_banner": (1584, 396),
    "whatsapp_dp": (500, 500),
    "small_thumb": (320, 180),
    "medium_thumb": (480, 270),
    "wide_banner": (1920, 480),
    "bot_father": (640, 360)
}

# Async resize function
async def resize_image(input_path, width, height):
    fd, output_path = mkstemp(suffix=".jpg")
    os.close(fd)

    try:
        async with aiofiles.open(input_path, mode='rb') as f:
            img = Image.open(f.name)
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path, format="JPEG", quality=95, optimize=True)
            img.close()
    except Exception as e:
        LOGGER.error(f"Error in resize_image: {e}", exc_info=True)
        raise
    return output_path

def setup_rs_handler(app: Client):

    @app.on_message(filters.command("rs", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def resize_menu_handler(client: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not message.reply_to_message or not message.reply_to_message.photo:
            await client.send_message(chat_id, "**❌ Reply to a photo or image with this command**")
            return

        status_msg = await client.send_message(chat_id, "**Resizing Your Image...**")
        try:
            # Download image asynchronously
            original_file = await client.download_media(message.reply_to_message, file_name=f"res_{user_id}.jpg")
            async with image_store_lock:
                image_store[user_id] = original_file
            LOGGER.info(f"[{user_id}] Image saved to {original_file}")

            buttons = [
                [InlineKeyboardButton(" 1:1 DP Square", callback_data="resize_dp_square"),
                 InlineKeyboardButton(" 16:9 Widescreen", callback_data="resize_widescreen")],
                [InlineKeyboardButton(" 9:16 Story", callback_data="resize_story"),
                 InlineKeyboardButton(" 2:3 Portrait", callback_data="resize_portrait")],
                [InlineKeyboardButton(" 1:2 Vertical", callback_data="resize_vertical"),
                 InlineKeyboardButton(" 2:1 Horizontal", callback_data="resize_horizontal")],
                [InlineKeyboardButton(" 3:2 Standard", callback_data="resize_standard"),
                 InlineKeyboardButton(" IG Post", callback_data="resize_ig_post")],
                [InlineKeyboardButton(" TikTok DP", callback_data="resize_tiktok_dp"),
                 InlineKeyboardButton(" FB Cover", callback_data="resize_fb_cover")],
                [InlineKeyboardButton(" YT Banner", callback_data="resize_yt_banner"),
                 InlineKeyboardButton(" YT Thumb", callback_data="resize_yt_thumb")],
                [InlineKeyboardButton(" X Header", callback_data="resize_x_header"),
                 InlineKeyboardButton(" X Post", callback_data="resize_x_post")],
                [InlineKeyboardButton(" LinkedIn Banner", callback_data="resize_linkedin_banner"),
                 InlineKeyboardButton(" WhatsApp DP", callback_data="resize_whatsapp_dp")],
                [InlineKeyboardButton(" Small Thumb", callback_data="resize_small_thumb"),
                 InlineKeyboardButton(" Medium Thumb", callback_data="resize_medium_thumb")],
                [InlineKeyboardButton("Wide Banner", callback_data="resize_wide_banner"),
                 InlineKeyboardButton(" Bot Father", callback_data="resize_bot_father")],
                [InlineKeyboardButton("❌ Close", callback_data="resize_close")]
            ]

            await client.send_message(
                chat_id,
                "**🔧 Choose a format to resize the image:**",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            LOGGER.error(f"[{user_id}] Error downloading image: {e}", exc_info=True)
            await client.send_message(chat_id, "**This Image Can Not Be Resized**")
        finally:
            await status_msg.delete()

    @app.on_callback_query(filters.regex("^resize_"))
    async def resize_button_handler(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        chat_id = callback_query.message.chat.id
        data = callback_query.data.replace("resize_", "")

        if data == "close":
            await callback_query.message.delete()
            await callback_query.answer("Menu closed.")
            return

        async with image_store_lock:
            if user_id not in image_store:
                await callback_query.answer("⚠️ Image not found. Please use /rs again.", show_alert=True)
                return
            input_path = image_store[user_id]

        width, height = RESOLUTIONS.get(data, (1080, 1080))

        try:
            output_file = await resize_image(input_path, width, height)
            async with aiofiles.open(output_file, mode='rb') as f:
                await client.send_document(
                    chat_id,
                    document=f.name,
                    caption=f"✔️ Resized to {width}x{height}"
                )
            await callback_query.answer(f"Image successfully resized to {width}x{height}!")
        except Exception as e:
            LOGGER.error(f"[{user_id}] Resizing error: {e}", exc_info=True)
            await callback_query.answer("Failed to resize image.", show_alert=True)
        finally:
            async with image_store_lock:
                image_store.pop(user_id, None)
            try:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_file):
                    os.remove(output_file)
            except Exception as e:
                LOGGER.warning(f"[{user_id}] Cleanup error: {e}")
