import aiohttp
import asyncio
import json
import os
import pycountry
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

url = "https://smartdb.vercel.app/api/bin"

async def fetch_bins(params, client=None, message=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    LOGGER.error(f"Error fetching data: {response.status}")
                    raise Exception(f"API request failed with status {response.status}")
                data = await response.json()
                if not data.get("data"):
                    LOGGER.error(f"API returned no data")
                    raise Exception("API returned no data")
                LOGGER.info(f"Successfully fetched {len(data['data'])} bins for params {params}")
                return data['data']
    except Exception as e:
        LOGGER.error(f"Exception occurred while fetching data: {e}")
        if client and message:
            await notify_admin(client, "/bindb or /binbank", e, message)
        return []

def process_bins_to_json(bins):
    processed = []
    for bin_data in bins:
        processed.append({
            "bin": bin_data.get("bin", "Unknown"),
            "bank": bin_data.get("issuer", "Unknown"),
            "country_code": bin_data.get("country_code", "Unknown"),
            "brand": bin_data.get("brand", "Unknown"),
            "category": bin_data.get("category", "Unknown"),
            "type": bin_data.get("type", "Unknown"),
            "website": bin_data.get("website", "")
        })
    return processed

def save_to_json_file(data, filename, client=None, message=None):
    try:
        os.makedirs('data', exist_ok=True)
        path = os.path.join('data', filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        LOGGER.info(f"Data saved to {path}")
        asyncio.create_task(delete_file_after_delay(path, 10*60))
    except Exception as e:
        LOGGER.error(f"Error saving to {filename}: {e}")
        if client and message:
            asyncio.create_task(notify_admin(client, "/bindb or /binbank", e, message))
        raise

def load_from_json_file(filename, client=None, message=None):
    try:
        path = os.path.join('data', filename)
        if not os.path.exists(path):
            LOGGER.error(f"File not found: {path}")
            raise Exception("File not found")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        LOGGER.error(f"Error loading from {filename}: {e}")
        if client and message:
            asyncio.create_task(notify_admin(client, "/bindb or /binbank", e, message))
        raise

async def delete_file_after_delay(file_path, delay):
    await asyncio.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
        LOGGER.info(f"Deleted file {file_path} after delay")

def generate_message(bins, page, identifier):
    start = (page - 1) * 5
    end = start + 5
    selected_bins = bins[start:end]

    message = f"**Smart Tool - Bin database 📋**\n**━━━━━━━━━━━━━━━━━━**\n\n"
    for i, bin_data in enumerate(selected_bins, start=start + 1):
        message += (f"{i}. **BIN:** {bin_data['bin']}\n"
                    f"**Bank:** {bin_data['bank']}\n"
                    f"**Country:** {bin_data['country_code']}\n\n")
    return message

async def bindb_handler(client, message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /bindb")
        return

    try:
        if len(message.command) != 2:
            await client.send_message(message.chat.id, "**Please provide a country name or code. e.g. /bindb BD or /bindb Bangladesh**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return

        country_input = message.command[1].upper()
        # Handle UK-specific case
        if country_input in ["UK", "UNITED KINGDOM"]:
            country_code = "GB"
            country_name = "United Kingdom"
        else:
            country = pycountry.countries.search_fuzzy(country_input)[0] if len(country_input) > 2 else pycountry.countries.get(alpha_2=country_input)
            if not country:
                await client.send_message(message.chat.id, "**Invalid country name or code**", parse_mode=ParseMode.MARKDOWN)
                LOGGER.warning(f"Invalid country input: {country_input}")
                return
            country_code = country.alpha_2.upper()
            country_name = country.name

        filename = f"bindb_{country_code}.json"

        LOGGER.info(f"Fetching BINs for country {country_name} ({country_code})")

        loading_message = await client.send_message(message.chat.id, f"**Finding Bins With Country {country_name}...**", parse_mode=ParseMode.MARKDOWN)

        params = {"country": country_code, "limit": 100}
        bins = await fetch_bins(params, client=client, message=message)
        if not bins:
            await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry No Bins Found**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"No bins found for country {country_code}")
            return

        processed_bins = process_bins_to_json(bins)
        save_to_json_file(processed_bins, filename, client=client, message=message)
        message_text = generate_message(processed_bins, 1, country_code)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Next", callback_data=f"bindb_next_1_{filename}")]
        ])

        await client.edit_message_text(message.chat.id, loading_message.id, message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Sent BINs for country {country_code} to chat {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in bindb_handler: {e}")
        await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry, an error occurred while fetching BIN data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/bindb", e, message)

async def binbank_handler(client, message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /binbank")
        return

    try:
        if len(message.command) < 2:
            await client.send_message(message.chat.id, "**Please provide a bank name. e.g. /binbank Pubali**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return

        bank_name = ' '.join(message.command[1:]).title()
        filename = f"binbank_{bank_name.replace(' ', '_')}.json"

        LOGGER.info(f"Fetching BINs for bank {bank_name}")

        loading_message = await client.send_message(message.chat.id, f"**Finding Bins With Bank {bank_name}...**", parse_mode=ParseMode.MARKDOWN)

        params = {"bank": bank_name, "limit": 100}
        bins = await fetch_bins(params, client=client, message=message)
        if not bins:
            await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry No Bins Found**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"No bins found for bank {bank_name}")
            return

        processed_bins = process_bins_to_json(bins)
        save_to_json_file(processed_bins, filename, client=client, message=message)
        message_text = generate_message(processed_bins, 1, bank_name)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Next", callback_data=f"binbank_next_1_{filename}")]
        ])

        await client.edit_message_text(message.chat.id, loading_message.id, message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Sent BINs for bank {bank_name} to chat {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in binbank_handler: {e}")
        await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry, an error occurred while fetching BIN data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/binbank", e, message)

async def next_page(client, callback_query):
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await callback_query.message.edit_text(BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use next page for {callback_query.data}")
        return

    try:
        data_parts = callback_query.data.split('_', 3)
        prefix, current_page, filename = data_parts[0], int(data_parts[2]), data_parts[3]

        bins = load_from_json_file(filename, client=client, message=callback_query.message)
        identifier = filename.split('_')[1].split('.')[0]

        next_page = current_page + 1
        if (next_page - 1) * 5 >= len(bins):
            await callback_query.answer("❌ Data Expired Please Request Again To Get Latest Database")
            LOGGER.info(f"Data expired for next page {next_page} in chat {callback_query.message.chat.id}")
            return

        message_text = generate_message(bins, next_page, identifier)
        prev_button = InlineKeyboardButton("◀️ Previous", callback_data=f"{prefix}_prev_{next_page}_{filename}")
        next_button = InlineKeyboardButton("▶️ Next", callback_data=f"{prefix}_next_{next_page}_{filename}")
        keyboard = InlineKeyboardMarkup([[prev_button, next_button]])

        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        LOGGER.info(f"Updated to next page {next_page} for {filename} in chat {callback_query.message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in next_page: {e}")
        await callback_query.message.edit_text("**Sorry, an error occurred while fetching data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/bindb or /binbank next", e, callback_query.message)

async def prev_page(client, callback_query):
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await callback_query.message.edit_text(BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use previous page for {callback_query.data}")
        return

    try:
        data_parts = callback_query.data.split('_', 3)
        prefix, current_page, filename = data_parts[0], int(data_parts[2]), data_parts[3]

        bins = load_from_json_file(filename, client=client, message=callback_query.message)
        identifier = filename.split('_')[1].split('.')[0]

        prev_page = current_page - 1
        if prev_page < 1:
            await callback_query.answer("❌ Data Expired Please Request Again To Get Latest Database")
            LOGGER.info(f"Data expired for previous page {prev_page} in chat {callback_query.message.chat.id}")
            return

        message_text = generate_message(bins, prev_page, identifier)
        prev_button = InlineKeyboardButton("◀️ Previous", callback_data=f"{prefix}_prev_{prev_page}_{filename}")
        next_button = InlineKeyboardButton("▶️ Next", callback_data=f"{prefix}_next_{prev_page}_{filename}")
        keyboard = InlineKeyboardMarkup([[prev_button, next_button]])

        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        LOGGER.info(f"Updated to previous page {prev_page} for {filename} in chat {callback_query.message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in prev_page: {e}")
        await callback_query.message.edit_text("**Sorry, an error occurred while fetching data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/bindb or /binbank prev", e, callback_query.message)

def setup_db_handlers(app: Client):
    app.add_handler(MessageHandler(bindb_handler, filters.command(["bindb"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
    app.add_handler(MessageHandler(binbank_handler, filters.command(["binbank"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
    app.add_handler(CallbackQueryHandler(next_page, filters.regex(r"(bindb|binbank)_next_\d+_(.+\.json)")))
    app.add_handler(CallbackQueryHandler(prev_page, filters.regex(r"(bindb|binbank)_prev_\d+_(.+\.json)")))
