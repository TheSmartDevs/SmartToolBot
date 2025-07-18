# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import aiohttp
import asyncio
import json
import os
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

url = "https://smartbinancep2p-production-af69.up.railway.app/api/v1/p2p"

async def fetch_sellers(asset, fiat, trade_type, pay_type, client=None, message=None):
    params = {
        "asset": asset,
        "pay_type": pay_type,
        "trade_type": trade_type,
        "limit": 100
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    LOGGER.error(f"Error fetching data: {response.status}")
                    raise Exception(f"API request failed with status {response.status}")
                data = await response.json()
                if not data.get("success", False):
                    LOGGER.error(f"API returned success: false")
                    raise Exception("API returned success: false")
                LOGGER.info(f"Successfully fetched {len(data['data'])} sellers for {asset} in {fiat}")
                return data['data']
    except Exception as e:
        LOGGER.error(f"Exception occurred while fetching data: {e}")
        if client and message:
            await notify_admin(client, "/p2p", e, message)
        return []

def process_sellers_to_json(sellers, fiat):
    processed = []
    for seller in sellers:
        processed.append({
            "seller": seller.get("seller_name", "Unknown"),
            "price": f"{seller['price']} {fiat}",
            "available_usdt": f"{seller['available_amount']} USDT",
            "min_amount": f"{seller['min_order_amount']} {fiat}",
            "max_amount": f"{seller['max_order_amount']} {fiat}",
            "completion_rate": f"{seller['completion_rate']}%",
            "trade_method": ", ".join(seller['payment_methods']) if seller['payment_methods'] else "Unknown"
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
            asyncio.create_task(notify_admin(client, "/p2p", e, message))
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
            asyncio.create_task(notify_admin(client, "/p2p", e, message))
        raise

async def delete_file_after_delay(file_path, delay):
    await asyncio.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
        LOGGER.info(f"Deleted file {file_path} after delay")

def generate_message(sellers, page, fiat):
    start = (page - 1) * 10
    end = start + 10
    selected_sellers = sellers[start:end]

    message = f"💱 **Latest P2P USDT Trades for {fiat}** 👇\n\n"
    for i, seller in enumerate(selected_sellers, start=start + 1):
        message += (f"**{i}. Name:** {seller['seller']}\n"
                    f"**Price:** {seller['price']}\n"
                    f"**Payment Method:** {seller['trade_method']}\n"
                    f"**Crypto Amount:** {seller['available_usdt']}\n"
                    f"**Limit:** {seller['min_amount']} - {seller['max_amount']}\n\n")
    return message

async def p2p_handler(client, message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /p2p")
        return

    try:
        if len(message.command) != 2:
            await client.send_message(message.chat.id, "**Please provide a currency. e.g. /p2p BDT or /p2p SAR**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return

        fiat = message.command[1].upper()
        asset = "USDT"
        trade_type = "SELL"
        pay_type = fiat  # Use fiat directly as pay_type since API accepts any currency
        filename = f"p2p_{asset}_{fiat}.json"

        LOGGER.info(f"Fetching P2P trades for {asset} in {fiat} using {pay_type}")

        loading_message = await client.send_message(message.chat.id, "**🔄 Fetching All P2P Trades**", parse_mode=ParseMode.MARKDOWN)

        sellers = await fetch_sellers(asset, fiat, trade_type, pay_type, client=client, message=message)
        if not sellers:
            await client.edit_message_text(message.chat.id, loading_message.id, "**❌ No sellers found or API error occurred**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"No sellers found for {asset} in {fiat}")
            return

        processed_sellers = process_sellers_to_json(sellers, fiat)
        save_to_json_file(processed_sellers, filename, client=client, message=message)
        message_text = generate_message(processed_sellers, 1, fiat)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Next", callback_data=f"nextone_1_{filename}")]
        ])

        await client.edit_message_text(message.chat.id, loading_message.id, message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Sent P2P trades for {asset} in {fiat} to chat {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in p2p_handler: {e}")
        await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry, an error occurred while fetching P2P data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/p2p", e, message)

async def next_page(client, callback_query):
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await callback_query.message.edit_text(BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use next page for {callback_query.data}")
        return

    try:
        current_page = int(callback_query.data.split('_', 2)[1])
        filename = callback_query.data.split('_', 2)[2]

        sellers = load_from_json_file(filename, client=client, message=callback_query.message)
        fiat = filename.split('_')[2].split('.')[0]  # Extract fiat from filename

        next_page = current_page + 1
        if (next_page - 1) * 10 >= len(sellers):
            await callback_query.answer("❌ Data Expired Please Request Again To Get Latest Database")
            LOGGER.info(f"Data expired for next page {next_page} in chat {callback_query.message.chat.id}")
            return

        message_text = generate_message(sellers, next_page, fiat)
        prev_button = InlineKeyboardButton("◀️ Previous", callback_data=f"prevone_{next_page}_{filename}")
        next_button = InlineKeyboardButton("▶️ Next", callback_data=f"nextone_{next_page}_{filename}")
        keyboard = InlineKeyboardMarkup([[prev_button, next_button]])

        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        LOGGER.info(f"Updated to next page {next_page} for {filename} in chat {callback_query.message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in next_page: {e}")
        await callback_query.message.edit_text("**Sorry, an error occurred while fetching data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/p2p next", e, callback_query.message)

async def prev_page(client, callback_query):
    user_id = callback_query.from_user.id if callback_query.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await callback_query.message.edit_text(BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use previous page for {callback_query.data}")
        return

    try:
        current_page = int(callback_query.data.split('_', 2)[1])
        filename = callback_query.data.split('_', 2)[2]

        sellers = load_from_json_file(filename, client=client, message=callback_query.message)
        fiat = filename.split('_')[2].split('.')[0]  # Extract fiat from filename

        prev_page = current_page - 1
        if prev_page < 1:
            await callback_query.answer("❌ Data Expired Please Request Again To Get Latest Database")
            LOGGER.info(f"Data expired for previous page {prev_page} in chat {callback_query.message.chat.id}")
            return

        message_text = generate_message(sellers, prev_page, fiat)
        prev_button = InlineKeyboardButton("◀️ Previous", callback_data=f"prevone_{prev_page}_{filename}")
        next_button = InlineKeyboardButton("▶️ Next", callback_data=f"nextone_{prev_page}_{filename}")
        keyboard = InlineKeyboardMarkup([[prev_button, next_button]])

        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        await callback_query.answer()
        LOGGER.info(f"Updated to previous page {prev_page} for {filename} in chat {callback_query.message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in prev_page: {e}")
        await callback_query.message.edit_text("**Sorry, an error occurred while fetching data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/p2p prev", e, callback_query.message)

def setup_p2p_handler(app: Client):
    app.add_handler(MessageHandler(p2p_handler, (filters.private | filters.group) & filters.command("p2p", prefixes=COMMAND_PREFIX)))
    app.add_handler(CallbackQueryHandler(next_page, filters.regex(r"nextone_\d+_(.+\.json)")))
    app.add_handler(CallbackQueryHandler(prev_page, filters.regex(r"prevone_\d+_(.+\.json)")))
