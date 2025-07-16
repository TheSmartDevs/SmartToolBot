#Updates Channel: https://t.me/TheSmartDev
import os
import io
from PIL import Image
import google.generativeai as genai
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX, IMGAI_SIZE_LIMIT, BAN_REPLY, GOOGLE_API_KEY, MODEL_NAME
from utils import notify_admin, LOGGER
from core import banned_users

def setup_gem_handler(app: Client):
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    @app.on_message(filters.command(["gem", "gemi", "gemini"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gemi_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        try:
            loading_message = await client.send_message(message.chat.id, "**🔍GeminiAI is thinking, Please Wait✨**")

            prompt = None
            if message.reply_to_message and message.reply_to_message.text:
                prompt = message.reply_to_message.text
            elif len(message.text.strip()) > 5:
                prompt = message.text.split(maxsplit=1)[1]

            if not prompt:
                await client.edit_message_text(message.chat.id, loading_message.id, "**Please Provide A Prompt For GeminiAI✨ Response**")
                return

            response = model.generate_content(prompt)
            response_text = response.text

            if len(response_text) > 4000:
                await client.delete_message(message.chat.id, loading_message.id)
                parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                for part in parts:
                    await client.send_message(message.chat.id, part)
            else:
                await client.edit_message_text(message.chat.id, loading_message.id, response_text)

        except Exception as e:
            LOGGER.error(f"Gemini error: {str(e)}")
            await client.send_message(message.chat.id, "**❌Sorry Bro Gemini API Error**")
            await notify_admin(client, "/gem", e, message)
        finally:
            if os.path.exists("temp_file"):
                os.remove("temp_file")

    @app.on_message(filters.command(["imgai"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def imgai_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        try:
            if not message.reply_to_message or not message.reply_to_message.photo:
                await client.send_message(message.chat.id, "**❌ Please Reply To An Image For Analysis**")
                return

            processing_msg = await client.send_message(message.chat.id, "**🔍Gemini Is Analyzing The Image Please Wait✨**")
            photo_path = await message.reply_to_message.download()

            try:
                if os.path.getsize(photo_path) > IMGAI_SIZE_LIMIT:
                    await processing_msg.edit(f"**❌Sorry Bro Image Too Large**")
                    return

                with Image.open(photo_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                user_prompt = " ".join(message.command[1:]) if len(message.command) > 1 else "Describe this image in detail"

                response = model.generate_content([user_prompt, img])
                analysis = response.text

                if len(analysis) > 4000:
                    await processing_msg.delete()
                    parts = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
                    for part in parts:
                        await client.send_message(message.chat.id, part)
                else:
                    await processing_msg.edit(f"{analysis}")

            except Exception as e:
                LOGGER.error(f"Image analysis error: {str(e)}")
                await processing_msg.edit("**❌ Sorry Bro ImageAI Error**")
                await notify_admin(client, "/imgai", e, message)
            finally:
                if os.path.exists(photo_path):
                    os.remove(photo_path)

        except Exception as e:
            LOGGER.error(f"Image analysis error: {str(e)}")
            await client.send_message(message.chat.id, "**❌ Sorry Bro ImageAI Error**")
            await notify_admin(client, "/imgai", e, message)
