# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

import os
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import GROQ_API_KEY, GROQ_API_URL, TEXT_MODEL, COMMAND_PREFIX, BAN_REPLY
from utils import notify_admin, LOGGER
from core import banned_users

def setup_dep_handler(app: Client):
    @app.on_message(filters.command(["dep"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def dep_command(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        user_text = None
        if message.reply_to_message and message.reply_to_message.text:
            user_text = message.reply_to_message.text
        elif len(message.command) > 1:
            user_text = " ".join(message.command[1:])

        if not user_text:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please Provide A Prompt For DeepSeekAi✨ Response**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        temp_message = await client.send_message(
            chat_id=message.chat.id,
            text="**DeepSeek AI Is Thinking Wait..✨**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": TEXT_MODEL,
                        "messages": [
                            {"role": "system", "content": "Reply in the same language as the user's message But Always Try To Answer Shortly"},
                            {"role": "user", "content": user_text},
                        ],
                    },
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    bot_response = data.get("choices", [{}])[0].get("message", {}).get("content", "Sorry DeepSeek API Dead")

            await temp_message.edit_text(bot_response, parse_mode=ParseMode.MARKDOWN)

        except aiohttp.ClientError as e:
            LOGGER.error(f"HTTP error while calling Groq API: {e}")
            await temp_message.edit_text("**Sorry Bro DeepseekAI✨ API Dead**", parse_mode=ParseMode.MARKDOWN)
            await notify_admin(client, "/dep", e, message)
        except Exception as e:
            LOGGER.error(f"Error generating response: {e}")
            await temp_message.edit_text("**Sorry Bro DeepseekAI✨ API Dead**", parse_mode=ParseMode.MARKDOWN)
            await notify_admin(client, "/dep", e, message)
