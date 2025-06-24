# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import BIN_KEY, COMMAND_PREFIX
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users

async def get_bin_info(bin, client, message):
    headers = {'x-api-key': BIN_KEY}
    try:
        response = requests.get(f"https://data.handyapi.com/bin/{bin}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            LOGGER.error(f"API returned status code {response.status_code}")
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        LOGGER.error(f"Error retrieving info for BIN: {bin} - {e}")
        # Notify admins about the error
        await notify_admin(client, "/mbin", e, message)
        return None

def get_flag_emoji(country_code):
    if len(country_code) == 2:
        return chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))
    return ''

def setup_mbin_handler(app: Client):
    @app.on_message(filters.command(["mbin"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def bin_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        LOGGER.info(f"Received /mbin command from user: {message.from_user.id}")
        bins = []
        
        # Check if the command is a reply to a text file
        if message.reply_to_message and message.reply_to_message.document:
            file_name = await message.reply_to_message.download()
            with open(file_name, 'r') as file:
                bins = [line.strip() for line in file.readlines() if line.strip()]
            os.remove(file_name)
            LOGGER.info(f"BINs extracted from the uploaded file by user: {message.from_user.id}")
        else:
            # Otherwise, get bins from the command input
            input_text = message.text.split(maxsplit=1)
            if len(input_text) < 2:
                await client.send_message(message.chat.id, "**Provide a valid BIN (6 digits) or reply to a text file containing BINs❌**", parse_mode=ParseMode.MARKDOWN)
                LOGGER.warning(f"Invalid BIN input by user: {message.from_user.id}")
                return
            bins = input_text[1].split()

        if len(bins) > 20:
            await client.send_message(message.chat.id, "**You can check up to 20 BINs at a time❌**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"User {message.from_user.id} tried to fetch more than 20 BINs")
            return

        invalid_bins = [bin for bin in bins if len(bin) != 6 or not bin.isdigit()]
        if invalid_bins:
            await client.send_message(message.chat.id, f"**Invalid BINs provided ❌** {' '.join(invalid_bins)}", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid BIN formats from user: {message.from_user.id} - {invalid_bins}")
            return

        fetching_message = await client.send_message(message.chat.id, "**Fetching BINs Info...✨**", parse_mode=ParseMode.MARKDOWN)
        results = []

        async def fetch_bin_info(bin):
            bin_info = await get_bin_info(bin, client, message)
            if isinstance(bin_info, dict):
                if bin_info.get('Status') == "SUCCESS":
                    country_code = bin_info.get('Country', {}).get('A2', '')
                    country_name = bin_info.get('Country', {}).get('Name', 'N/A')
                    flag_emoji = get_flag_emoji(country_code) if country_code else ''
                    info = f"• **BIN**: `{bin}`\n"
                    info += f"• **INFO**: {bin_info.get('CardTier', 'N/A')} - {bin_info.get('Type', 'N/A')} - {bin_info.get('Scheme', 'N/A')}\n"
                    info += f"• **BANK**: {bin_info.get('Issuer', 'N/A')}\n"
                    info += f"• **COUNTRY**: {country_name} {flag_emoji}\n\n"
                    return info
                else:
                    error_message = bin_info.get('Status', 'Unknown error')
                    LOGGER.error(f"Error for BIN: {bin} - {error_message}")
                    return f"• **BIN**: `{bin}`\n• **INFO**: {error_message}\n\n"
            else:
                LOGGER.error(f"Invalid bin_info format or response for BIN: {bin} - {bin_info}")
                return f"• **BIN**: `{bin}`\n• **INFO**: Not Found\n\n"

        tasks = [fetch_bin_info(bin) for bin in bins]
        results = await asyncio.gather(*tasks)

        response_text = "🔍 **BIN Details 📋**\n━━━━━━━━━━━━━━━━━━\n" + "".join(results)
        await fetching_message.edit(response_text, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"BIN info sent to user: {message.from_user.id}")
