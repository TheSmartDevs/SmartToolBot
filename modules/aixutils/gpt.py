# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from config import OPENAI_API_KEY, COMMAND_PREFIX
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users

async def fetch_gpt_response(prompt, model):
    LOGGER.info(f"Fetching GPT response for prompt: {prompt} with model: {model}")
    if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "":
        LOGGER.error("OPENAI_API_KEY is missing or empty")
        return None
    async with aiohttp.ClientSession() as session:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        LOGGER.debug(f"Request headers: {{'Authorization': 'Bearer {'*' * 10}{OPENAI_API_KEY[-10:]}', 'Content-Type': 'application/json'}}")
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
                    LOGGER.info("Successfully fetched GPT response")
                    return response_text
                else:
                    error_message = await response.text()
                    LOGGER.error(f"API error {response.status}: {error_message}")
                    return None
        except Exception as e:
            LOGGER.error(f"Exception in fetch_gpt_response: {str(e)}")
            return None

def setup_gpt_handlers(app: Client):
    @app.on_message(filters.command(["gpt4"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gpt4_handler(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        LOGGER.info(f"Received /gpt4 command from user {message.from_user.id} in chat {message.chat.id}")
        await client.send_message(message.chat.id, "**GPT-4 Gate Off 🔕**", parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command(["gpt", "gpt3", "gpt3.5"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gpt_handler(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        LOGGER.info(f"Received GPT command from user {message.from_user.id} in chat {message.chat.id}")
        try:
            # Extract prompt from the command or reply
            prompt = None
            if message.reply_to_message and message.reply_to_message.text:
                # If the message is a reply, use the replied message's text as the prompt
                prompt = message.reply_to_message.text
            elif len(message.command) > 1:
                # If the message contains text after the command, use it as the prompt
                prompt = " ".join(message.command[1:])

            if not prompt:
                LOGGER.warning("No prompt provided in GPT command")
                await client.send_message(message.chat.id, "**Please Provide A Prompt For ChatGPTAI✨ Response**", parse_mode=ParseMode.MARKDOWN)
                return

            LOGGER.info(f"Processing prompt: {prompt}")
            loading_message = await client.send_message(message.chat.id, "**ChatGPT 3.5 Is Thinking✨**", parse_mode=ParseMode.MARKDOWN)
            response_text = await fetch_gpt_response(prompt, "gpt-4o-mini")
            if response_text:
                LOGGER.info("Editing loading message with GPT response")
                await loading_message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
            else:
                LOGGER.error("Failed to fetch GPT response")
                await loading_message.edit_text("**Sorry Chat Gpt 3.5 API Dead**", parse_mode=ParseMode.MARKDOWN)
                # Notify admins about the error
                await notify_admin(client, "/gpt", Exception("Failed to fetch GPT response"), message)
        except Exception as e:
            LOGGER.error(f"Exception in gpt_handler: {str(e)}")
            await loading_message.edit_text("**Sorry Chat Gpt 3.5 API Dead**", parse_mode=ParseMode.MARKDOWN)
            # Notify admins about the error
            await notify_admin(client, "/gpt", e, message)
