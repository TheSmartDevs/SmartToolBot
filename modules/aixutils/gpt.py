# Copyright @ISmartDevs
# Channel t.me/TheSmartDev

import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from config import OPENAI_API_KEY, COMMAND_PREFIX, BAN_REPLY
from utils import notify_admin, LOGGER
from core import banned_users

async def fetch_gpt_response(prompt, model):
    if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "":
        return None
    async with aiohttp.ClientSession() as session:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "n": 1,
            "stop": None,
            "temperature": 0.5
        }
        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    json_response = await response.json()
                    response_text = json_response['choices'][0]['message']['content']
                    return response_text
                else:
                    return None
        except Exception as e:
            return None

def setup_gpt_handlers(app: Client):
    @app.on_message(filters.command(["gpt4"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gpt4_handler(client, message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        await client.send_message(message.chat.id, "**GPT-4 Gate Off 🔕**", parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command(["gpt", "gpt3", "gpt3.5"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gpt_handler(client, message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        try:
            prompt = None
            if message.reply_to_message and message.reply_to_message.text:
                prompt = message.reply_to_message.text
            elif len(message.command) > 1:
                prompt = " ".join(message.command[1:])
            if not prompt:
                await client.send_message(message.chat.id, "**Please Provide A Prompt For ChatGPTAI✨ Response**", parse_mode=ParseMode.MARKDOWN)
                return
            loading_message = await client.send_message(message.chat.id, "**ChatGPT 3.5 Is Thinking✨**", parse_mode=ParseMode.MARKDOWN)
            response_text = await fetch_gpt_response(prompt, "gpt-4o-mini")
            if response_text:
                await loading_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await loading_message.edit_text("**Sorry Chat Gpt 3.5 API Dead**", parse_mode=ParseMode.MARKDOWN)
                await notify_admin(client, "/gpt", Exception("Failed to fetch GPT response"), message)
        except Exception as e:
            await loading_message.edit_text("**Sorry Chat Gpt 3.5 API Dead**", parse_mode=ParseMode.MARKDOWN)
            await notify_admin(client, "/gpt", e, message)
