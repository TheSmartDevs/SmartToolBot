# Copyright @ISmartCoder
# Channel t.me/TheSmartDev

import os
import io
import base64
import aiohttp
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX, IMGAI_SIZE_LIMIT, TEXT_API_URL, IMAGE_API_URL, BAN_REPLY
from utils import notify_admin, LOGGER
from core import banned_users

def setup_gem_handler(app: Client):
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

            async with aiohttp.ClientSession() as session:
                async with session.get(TEXT_API_URL, params={"prompt": prompt}) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    response_text = response_data.get("response", "No response received")

            if len(response_text) > 4000:
                await loading_message.delete()
                parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                for part in parts:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=part
                    )
            else:
                await loading_message.edit_text(response_text)

        except Exception as e:
            LOGGER.error(f"Gemini error: {str(e)}")
            await client.send_message(message.chat.id, "**❌Sorry Bro Gemini API Dead**")
            await notify_admin(client, "/gem", e, message)

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
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG", quality=85)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

                user_prompt = " ".join(message.command[1:]) if len(message.command) > 1 else "Describe this image in detail"

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        IMAGE_API_URL,
                        json={
                            "imageBase64": img_base64,
                            "prompt": user_prompt
                        },
                        timeout=20
                    ) as response:
                        response.raise_for_status()
                        result = await response.json()
                        analysis = result.get('analysis', 'No analysis available')

                await processing_msg.delete()
                
                if len(analysis) > 4000:
                    with io.BytesIO(analysis.encode()) as file:
                        file.name = "image_analysis.txt"
                        await client.send_document(
                            chat_id=message.chat.id,
                            document=file,
                            caption="**Image Analysis Result**"
                        )
                else:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=f"{analysis}"
                    )

            except aiohttp.ClientTimeout:
                await processing_msg.edit("**❌ Sorry Bro ImageAI API Dead**")
                await notify_admin(client, "/imgai", Exception("Timeout error"), message)
            except Exception as e:
                await processing_msg.edit(f"**❌ Sorry Bro ImageAI API Dead**")
                await notify_admin(client, "/imgai", e, message)
            finally:
                if os.path.exists(photo_path):
                    os.remove(photo_path)

        except Exception as e:
            LOGGER.error(f"Image analysis error: {str(e)}")
            await client.send_message(message.chat.id, "**❌ Sorry Bro ImageAI API Dead**")
            await notify_admin(client, "/imgai", e, message)
