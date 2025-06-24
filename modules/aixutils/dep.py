# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import aiohttp
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import GROQ_API_KEY, GROQ_API_URL, TEXT_MODEL, COMMAND_PREFIX
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users

def setup_dep_handler(app: Client):
    @app.on_message(filters.command(["dep"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def dep_command(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIXED: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        # Extract user text from the command or reply
        user_text = None
        if message.reply_to_message and message.reply_to_message.text:
            # If the message is a reply, use the replied message's text as the prompt
            user_text = message.reply_to_message.text
        elif len(message.command) > 1:
            # If the message contains text after the command, use it as the prompt
            user_text = " ".join(message.command[1:])

        if not user_text:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Please Provide A Prompt For DeepSeekAi✨ Response**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send a temporary message
        temp_message = await client.send_message(
            chat_id=message.chat.id,
            text="**DeepSeek AI Is Thinking Wait..✨**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Call the Groq API using aiohttp
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

            # Edit the temporary message with the final response
            await temp_message.edit_text(bot_response, parse_mode=ParseMode.MARKDOWN)

        except aiohttp.ClientError as e:
            LOGGER.error(f"HTTP error while calling Groq API: {e}")
            await temp_message.edit_text("**Sorry Bro DeepseekAI✨ API Dead**", parse_mode=ParseMode.MARKDOWN)
            # Notify admins about the error
            await notify_admin(client, "/dep", e, message)
        except Exception as e:
            LOGGER.error(f"Error generating response: {e}")
            await temp_message.edit_text("**Sorry Bro DeepseekAI✨ API Dead**", parse_mode=ParseMode.MARKDOWN)
            # Notify admins about the error
            await notify_admin(client, "/dep", e, message)
