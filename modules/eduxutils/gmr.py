# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin from utils

# Configure logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def check_grammar(text):
    url = f"http://abirthetech.serv00.net/gmr.php?prompt={text}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise an exception for non-200 status codes
                result = await response.json()
                if 'response' not in result:
                    raise ValueError("Invalid API response: 'response' key missing")
                return result['response'].strip()
    except Exception as e:
        logger.error(f"Grammar check API error: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}gra", e, None)
        raise

async def grammar_check(client: Client, message: Message):
    # Check if the message is a reply
    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text.strip()
    else:
        # Check if command has text
        user_input = message.text.split(maxsplit=1)
        if len(user_input) < 2:
            await client.send_message(
                message.chat.id,
                "**❌ Provide some text or reply to a message to fix grammar.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        user_input = user_input[1].strip()

    # Proceed with grammar check
    checking_message = await client.send_message(
        message.chat.id,
        "**Checking And Fixing Grammar Please Wait...✨**",
        parse_mode=ParseMode.MARKDOWN
    )
    try:
        corrected_text = await check_grammar(user_input)
        await checking_message.edit(
            text=f"{corrected_text}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error processing grammar check: {e}")
        # Notify admins
        await notify_admin(client, f"{COMMAND_PREFIX}gra", e, message)
        # Send user-facing error message
        await checking_message.edit(
            text="**❌ Sorry, Grammar Check API Failed**",
            parse_mode=ParseMode.MARKDOWN
        )

def setup_gmr_handler(app: Client):
    app.add_handler(
        MessageHandler(
            grammar_check,
            filters.command(["gra"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
