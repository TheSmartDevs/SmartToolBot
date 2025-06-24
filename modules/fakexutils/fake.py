# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import pycountry
from config import COMMAND_PREFIX
from utils import LOGGER, get_locale_for_country, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

def setup_fake_handler(app: Client):
    @app.on_message(filters.command(["fake", "rnd"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def fake_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /fake")
            return

        if len(message.command) <= 1:
            await client.send_message(message.chat.id, "**❌ Please Provide A Country Code**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return
        
        country_code = message.command[1].upper()
        country = pycountry.countries.get(alpha_2=country_code) or pycountry.countries.get(name=country_code)
        
        if not country:
            await client.send_message(message.chat.id, "**❌ Please Provide A Valid Country Code**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid country code: {country_code}")
            return
        
        # Fetch fake address from API for the country
        locale = get_locale_for_country(country.alpha_2) or f"{country.alpha_2.lower()}_{country.alpha_2.upper()}"
        api_url = f"https://fakerapi.it/api/v2/addresses?_quantity=1&_locale={locale}&_country_code={country.alpha_2}"
        
        generating_message = await client.send_message(message.chat.id, "**Generating Fake Address...✨**", parse_mode=ParseMode.MARKDOWN)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, requests.get, api_url)
            response.raise_for_status()  # Raise an exception for non-200 status codes
            
            data = response.json()['data'][0]
            await generating_message.edit_text(f"""
**Address for {data['country']}**
━━━━━━━━━━━━━━━━━
**Street:** `{data['street']}`
**Street Name:** `{data['streetName']}`
**Building Number:** `{data['buildingNumber']}`
**City/Town/Village:** `{data['city']}`
**Postal code:** `{data['zipcode']}`
**Country:** `{data['country']}`
""", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Sent fake address for {country_code} in chat {message.chat.id}")
        except (requests.RequestException, ValueError, KeyError) as e:
            LOGGER.error(f"Fake address API error for country '{country_code}': {e}")
            # Notify admins
            await notify_admin(client, "/fake", e, message)
            # Send user-facing error message
            await generating_message.edit_text("**❌ Sorry, Fake Address Generator API Failed**", parse_mode=ParseMode.MARKDOWN)
