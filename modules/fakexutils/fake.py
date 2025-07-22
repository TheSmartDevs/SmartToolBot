import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from core import banned_users
import pycountry
from utils import LOGGER

def get_flag(country_code, client=None, message=None):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if not country:
            raise ValueError("Invalid country code")
        country_name = country.name
        flag_emoji = chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))
        return country_name, flag_emoji
    except Exception as e:
        error_msg = f"Error in get_flag: {str(e)}"
        LOGGER.error(error_msg)
        return None, "👁"

def setup_fake_handler(app: Client):
    @app.on_message(filters.command(["fake", "rnd"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def fake_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /fake")
            return

        if len(message.command) <= 1:
            await client.send_message(message.chat.id, "**❌ Please Provide A Country Code**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return
        
        country_code = message.command[1].upper()
        if country_code == "UK":
            country_code = "GB"
        
        country = pycountry.countries.get(alpha_2=country_code) or pycountry.countries.get(name=country_code)
        
        if not country:
            await client.send_message(message.chat.id, "**❌ Please Provide A Valid Country Code**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid country code: {country_code}")
            return
        
        api_url = f"https://smartfake.vercel.app/api/address?code={country.alpha_2}"
        
        generating_message = await client.send_message(message.chat.id, "**Generating Fake Address...**", parse_mode=ParseMode.MARKDOWN)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    _, flag_emoji = get_flag(country.alpha_2, client, message)
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("Copy Postal Code", copy_text=data['postal_code'])]
                    ])
                    await generating_message.edit_text(
                        f"**Address for {data['country']} {flag_emoji}**\n"
                        f"**━━━━━━━━━━━━━**\n"
                        f"**- Street :** `{data['street_address']}`\n"
                        f"**- Full Name :** `{data['person_name']}`\n"
                        f"**- City/Town/Village :** `{data['city']}`\n"
                        f"**- Gender :** `{data['gender']}`\n"
                        f"**- Postal Code :** `{data['postal_code']}`\n"
                        f"**- Phone Number :** `{data['phone_number']}`\n"
                        f"**- Country :** `{data['country']}`\n"
                        f"**━━━━━━━━━━━━━**\n"
                        f"**Click Below Button For Code 👇**",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                    LOGGER.info(f"Sent fake address for {country_code} in chat {message.chat.id}")
        except (aiohttp.ClientError, ValueError, KeyError) as e:
            LOGGER.error(f"Fake address API error for country '{country_code}': {e}")
            await generating_message.edit_text("**❌ Sorry, Fake Address Generator API Failed**", parse_mode=ParseMode.MARKDOWN)
