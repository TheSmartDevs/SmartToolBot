import os
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from tempfile import mkstemp
from config import COMMAND_PREFIX
from utils import LOGGER


def setup_rs_handler(app: Client):

    @app.on_message(filters.command(["rs"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def resize_handler(client: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not message.reply_to_message or not message.reply_to_message.photo:
            await client.send_message(chat_id, "**Please Reply To An Image With The Command**")
            return

        if len(message.command) != 2 or 'x' not in message.command[1].lower():
            await client.send_message(chat_id, "**Please use the format**: `/rs 1280x720`")
            return

        try:
            width, height = map(int, message.command[1].lower().split("x"))
        except ValueError:
            await client.send_message(chat_id, "**Invalid size format. Use `WIDTHxHEIGHT` like `1280x720`**")
            return

        temp_msg = await client.send_message(chat_id, "**🛠 Resizing Your Image... Wait...**")

        try:
            original_file = await client.download_media(message.reply_to_message, file_name="original.jpg")
            LOGGER.info(f"[{user_id}] Downloaded image: {original_file}")

            resized_file = resize_image(original_file, width, height)
            LOGGER.info(f"[{user_id}] Image resized to {width}x{height}: {resized_file}")

            await client.send_photo(chat_id, photo=resized_file)

            await temp_msg.delete()

        except Exception as e:
            LOGGER.error(f"[{user_id}] Error during image resizing", exc_info=True)
            await temp_msg.edit("**❌ Sorry The Provided Image Or Size Invalid**")

        finally:
            try:
                if os.path.exists(original_file):
                    os.remove(original_file)
                if 'resized_file' in locals() and os.path.exists(resized_file):
                    os.remove(resized_file)
                LOGGER.info(f"[{user_id}] Temporary files cleaned up.")
            except Exception as cleanup_err:
                LOGGER.warning(f"[{user_id}] Cleanup error: {cleanup_err}")


def resize_image(input_path, width, height):
    fd, output_path = mkstemp(suffix=".jpg")
    os.close(fd)

    with Image.open(input_path) as img:
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        resized.save(output_path, format="JPEG")

    return output_path
