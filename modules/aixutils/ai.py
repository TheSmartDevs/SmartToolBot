import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX, BAN_REPLY
from utils import notify_admin, LOGGER
from core import banned_users

def setup_ai_handler(app: Client):
    @app.on_message(filters.command(["ai"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def ai_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        try:
            loading_message = await client.send_message(message.chat.id, "**🔍SmartAI is thinking, Please Wait✨**")

            prompt = None
            if message.reply_to_message and message.reply_to_message.text:
                prompt = message.reply_to_message.text
            elif len(message.text.strip()) > 4:
                prompt = message.text.split(maxsplit=1)[1]

            if not prompt:
                await client.edit_message_text(message.chat.id, loading_message.id, "**Please Provide A Prompt For SmartAI✨ Response**")
                return

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://abirthetech.serv00.net/ai.php?prompt={prompt}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("response", "No response received")
                    else:
                        response_text = "**❌Sorry Bro SmartAI API Error**"
                        LOGGER.error(f"API request failed with status {resp.status}")

            if len(response_text) > 4000:
                await client.delete_message(message.chat.id, loading_message.id)
                parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                for part in parts:
                    await client.send_message(message.chat.id, part)
            else:
                await client.edit_message_text(message.chat.id, loading_message.id, response_text)

        except Exception as e:
            LOGGER.error(f"SmartAI error: {str(e)}")
            await client.send_message(message.chat.id, "**❌Sorry Bro SmartAI API Error**")
            await notify_admin(client, "/ai", e, message)
