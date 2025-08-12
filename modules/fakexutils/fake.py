import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from core import banned_users
import pycountry
from smartfaker import Faker
from utils import LOGGER

def get_flag(country_code, client=None, message=None):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if not country:
            return None, "🏚"
        country_name = country.name
        flag_emoji = chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))
        return country_name, flag_emoji
    except Exception as e:
        error_msg = f"Error in get_flag: {str(e)}"
        LOGGER.error(error_msg)
        return None, "🏚"

def resolve_country(input_str):
    input_str = input_str.strip().upper()
    if len(input_str) == 2:
        country = pycountry.countries.get(alpha_2=input_str)
        if country:
            return country.alpha_2, country.name
    try:
        country = pycountry.countries.search_fuzzy(input_str)[0]
        return country.alpha_2, country.name
    except LookupError:
        return None, None

def setup_fake_handler(app: Client):
    @app.on_message(filters.command(["fake", "rnd"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def fake_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /fake")
            return

        if len(message.command) <= 1:
            await client.send_message(message.chat.id, "**❌ Please Provide A Country Code or Name**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return

        country_input = message.command[1]
        country_code, country_name = resolve_country(country_input)
        if not country_code:
            if country_input == "UK":
                country_code, country_name = "GB", "United Kingdom"
            else:
                await client.send_message(message.chat.id, "**❌ Invalid Country Code or Name**", parse_mode=ParseMode.MARKDOWN)
                LOGGER.warning(f"Invalid country input: {country_input}")
                return

        generating_message = await client.send_message(message.chat.id, "**Generating Fake Address...**", parse_mode=ParseMode.MARKDOWN)

        try:
            fake = Faker()
            address = await fake.address(country_code, 1)
            _, flag_emoji = get_flag(country_code, client, message)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Copy Postal Code", copy_text=address['postal_code'])]
            ])
            await generating_message.edit_text(
                f"**Address for {address['country']} {flag_emoji}**\n"
                f"**━━━━━━━━━━━━━**\n"
                f"**- Street :** `{address['building_number']} {address['street_name']}`\n"
                f"**- Street Name :** `{address['street_name']}`\n"
                f"**- Currency :** `{address['currency']}`\n"
                f"**- Full Name :** `{address['person_name']}`\n"
                f"**- City/Town/Village :** `{address['city']}`\n"
                f"**- Gender :** `{address['gender']}`\n"
                f"**- Postal Code :** `{address['postal_code']}`\n"
                f"**- Phone Number :** `{address['phone_number']}`\n"
                f"**- State :** `{address['state']}`\n"
                f"**- Country :** `{address['country']}`\n"
                f"**━━━━━━━━━━━━━**\n"
                f"**Click Below Button For Code 👇**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            LOGGER.info(f"Sent fake address for {country_code} in chat {message.chat.id}")
        except Exception as e:
            LOGGER.error(f"Fake address generation error for country '{country_code}': {e}")
            await generating_message.edit_text("**❌ Sorry, Fake Address Generation Failed**", parse_mode=ParseMode.MARKDOWN)
