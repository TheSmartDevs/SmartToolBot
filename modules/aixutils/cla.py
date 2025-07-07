# Copyright @ISmartCoder
# Channel t.me/TheSmartDev

import os
import logging
import json
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from config import COMMAND_PREFIX, BAN_REPLY, REPLICATE_API_TOKEN
from core import banned_users
from utils import LOGGER, notify_admin

CLAUDE_API_URL = "https://api.replicate.com/v1/models/anthropic/claude-3.7-sonnet/predictions"

async def query_claude(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }

    payload = {
        "input": {
            "prompt": prompt,
            "max_tokens": 8192,
            "system_prompt": "",
            "extended_thinking": False,
            "max_image_resolution": 0.5,
            "thinking_budget_tokens": 1024
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(CLAUDE_API_URL, headers=headers, data=json.dumps(payload)) as response:
            if response.status == 201:
                result = await response.json()
                output = result.get("output", [])
                if isinstance(output, list):
                    return ''.join(output).strip()
                return str(output)
            else:
                raise Exception(f"Claude API error {response.status}: {await response.text()}")

def setup_cla_handler(app: Client):
    @app.on_message(filters.command(["cla"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def claude_handler(client: Client, message: Message):
        user_id = message.from_user.id
        if await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return

        loading_message = None
        try:
            loading_message = await client.send_message(message.chat.id, "**🔍 Claude AI ✨ is thinking... Please wait!**")

            # Extract prompt
            prompt = None
            if message.reply_to_message and message.reply_to_message.text:
                prompt = message.reply_to_message.text
            elif len(message.text.strip().split()) > 1:
                prompt = message.text.split(maxsplit=1)[1]

            if not prompt:
                await client.edit_message_text(message.chat.id, loading_message.id, "**⚠️ Please provide a prompt for Claude AI ✨**")
                return

            response_text = await query_claude(prompt)

            # Telegram message limit: 4096 chars
            if len(response_text) > 4000:
                parts = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
                await client.edit_message_text(message.chat.id, loading_message.id, parts[0])
                for part in parts[1:]:
                    await client.send_message(message.chat.id, part)
            else:
                await client.edit_message_text(message.chat.id, loading_message.id, response_text)

        except Exception as e:
            LOGGER.error(f"Error during Claude generation: {e}")
            if loading_message:
                await client.edit_message_text(message.chat.id, loading_message.id, "**🔍 Sorry, Claude AI ✨ failed to respond.**")
            await notify_admin(client, "/cla", e, message)
