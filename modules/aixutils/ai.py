# Copyright @ISmartCoder
# Channel t.me/TheSmartDev
import os
import io
import logging
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX, BAN_REPLY
from core import banned_users
from utils import notify_admin, LOGGER

API_URL = "https://abirthetech.serv00.net/ai.php"

def setup_ai_handler(app: Client):
    @app.on_message(filters.command(["ai"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gemi_handler(client: Client, message: Message):
        user_id = message.from_user.id
        if await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        loading_message = None
        try:
            loading_message = await client.send_message(message.chat.id, "**🔍 Smart AI ✨ is thinking... Please wait! ✨**")

            prompt = None
            if message.reply_to_message and message.reply_to_message.text:
                prompt = message.reply_to_message.text
            elif len(message.text.strip()) > 5:
                prompt = message.text.split(maxsplit=1)[1]

            if not prompt:
                await client.edit_message_text(message.chat.id, loading_message.id, "**Please Provide A Prompt For SmartAi✨ Response**")
                return

            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, params={"prompt": prompt}) as response:
                    response_data = await response.json()
                    response_text = response_data["response"]

            if len(response_text) > 4000:
                parts = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
                for part in parts:
                    await client.send_message(message.chat.id, part)
            else:
                await client.edit_message_text(message.chat.id, loading_message.id, response_text)

        except Exception as e:
            LOGGER.error(f"Error during text generation: {e}")
            if loading_message:
                await client.edit_message_text(message.chat.id, loading_message.id, "**🔍Sorry Bro Smart AI ✨ API Dead**")
                await notify_admin(client, "/ai", e, message)
