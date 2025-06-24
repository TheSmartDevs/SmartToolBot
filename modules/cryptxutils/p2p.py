# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# Note This Script Based On https://github.com/abirxdhack/Binance-P2P 
import aiohttp
import asyncio
import json
import os
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

# Binance API URL and headers
url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
headers = {
    "Content-Type": "application/json",
    "clienttype": "web",
    "lang": "en"
}

async def fetch_page(session, asset, fiat, trade_type, pay_type, page, rows=20, client=None, message=None):
    payload = {
        "asset": asset,
        "fiat": fiat,
        "tradeType": trade_type,
        "page": page,
        "rows": rows,
        "payTypes": [pay_type],
        "publisherType": None
    }
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                LOGGER.error(f"Error fetching page {page}: {response.status}")
                raise Exception(f"API request failed with status {response.status}")
            data = await response.json()
            LOGGER.info(f"Successfully fetched page {page} for {asset} in {fiat}")
            return data['data']
    except Exception as e:
        LOGGER.error(f"Exception occurred while fetching page {page}: {e}")
        if client and message:
            await notify_admin(client, "/p2p", e, message)
        return []

async def fetch_sellers(asset, fiat, trade_type, pay_type, client=None, message=None):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, asset, fiat, trade_type, pay_type, page, client=client, message=message) for page in range(1, 8)]  # Fetch first 7 pages
        results = await asyncio.gather(*tasks)
        all_sellers = [seller for result in results for seller in result if result]
        LOGGER.info(f"Fetched {len(all_sellers)} sellers for {asset} in {fiat}")
        return all_sellers[:131]

def process_sellers_to_json(sellers):
    processed = []
    for ad in sellers:
        adv = ad['adv']
        advertiser = ad['advertiser']
        processed.append({
            "seller": advertiser.get("nickName", "Unknown"),
            "price": f"{adv['price']} {adv['fiatUnit']}",
            "available_usdt": adv['surplusAmount'],
            "min_amount": f"{adv['minSingleTransAmount']} {adv['fiatUnit']}",
            "max_amount": f"{adv['maxSingleTransAmount']} {adv['fiatUnit']}",
            "completion_rate": f"{advertiser.get('monthFinishRate', 0) * 100:.2f}%",
            "trade_method": adv['tradeMethods'][0]['tradeMethodName'] if adv['tradeMethods'] else "Unknown"
        })
    return processed

def save_to_json_file(data, filename, client=None, message=None):
    try:
        os.makedirs('data', exist_ok=True)
        path = os.path.join('data', filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        LOGGER.info(f"Data saved to {path}")
        # Schedule file for deletion after 10 minutes
        asyncio.create_task(delete_file_after_delay(path, 10*60))
    except Exception as e:
        LOGGER.error(f"Error saving to {filename}: {e}")
        if client and message:
            asyncio.create_task(notify_admin(client, "/p2p", e, message))
        raise  # Re-raise to inform caller

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
        raise  # Re-raise to inform caller

async def delete_file_after_delay(file_path, delay):
    await asyncio.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
        LOGGER.info(f"Deleted file {file_path} after delay")

def generate_message(sellers, page):
    start = (page - 1) * 5
    end = start + 5
    selected_sellers = sellers[start:end]

    message = ""
    for i, seller in enumerate(selected_sellers, start=1):
        message += (f"**🧑‍💼 Seller:** `{seller['seller']}`\n"
                    f"**💵 Price:** `{seller['price']}`\n"
                    f"**💰 Available:** `{seller['available_usdt']} USDT`\n"
                    f"**📉 Min Amount:** `{seller['min_amount']}`\n"
                    f"**📈 Max Amount:** `{seller['max_amount']}`\n"
                    f"**✅ Completion Rate:** `{seller['completion_rate']}`\n"
                    f"**💳 Payment Method:** `{seller['trade_method']}`\n"
                    f"{'-'*40}\n")
    return message

def get_pay_type(fiat):
    pay_types = {
        "BDT": "bKash",
        "INR": "UPI"
        # Add more fiat to pay type mappings as needed
    }
    return pay_types.get(fiat.upper(), "Unknown")

async def p2p_handler(client, message):
    # Check if user is banned
    user_id = message.from_user.id if message.from_user else None
    # FIX: Await the banned_users.find_one as it's an async call
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use /p2p")
        return

    try:
        if len(message.command) != 2:
            await client.send_message(message.chat.id, "**Please provide a currency. e.g. /p2p BDT or /p2p INR**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return

        fiat = message.command[1].upper()
        asset = "USDT"
        trade_type = "SELL"
        pay_type = get_pay_type(fiat)
        filename = f"p2p_{asset}_{fiat}.json"

        LOGGER.info(f"Fetching P2P trades for {asset} in {fiat} using {pay_type}")

        loading_message = await client.send_message(message.chat.id, "**🔄 Fetching All P2P Trades**", parse_mode=ParseMode.MARKDOWN)

        sellers = await fetch_sellers(asset, fiat, trade_type, pay_type, client=client, message=message)
        if not sellers:
            await client.edit_message_text(message.chat.id, loading_message.id, "**❌ No sellers found or API error occurred**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"No sellers found for {asset} in {fiat}")
            return

        processed_sellers = process_sellers_to_json(sellers)
        save_to_json_file(processed_sellers, filename, client=client, message=message)
        message_text = generate_message(processed_sellers, 1)

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
    # Check if user is banned
    user_id = callback_query.from_user.id if callback_query.from_user else None
    # FIX: Await the banned_users.find_one as it's an async call
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await callback_query.message.edit_text("**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use next page for {callback_query.data}")
        return

    try:
        current_page = int(callback_query.data.split('_', 2)[1])
        filename = callback_query.data.split('_', 2)[2]

        sellers = load_from_json_file(filename, client=client, message=callback_query.message)

        next_page = current_page + 1
        if (next_page - 1) * 5 >= len(sellers):
            await callback_query.answer("❌ Data Expired Please Request Again To Get Latest Database")
            LOGGER.info(f"Data expired for next page {next_page} in chat {callback_query.message.chat.id}")
            return

        message_text = generate_message(sellers, next_page)
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
    # Check if user is banned
    user_id = callback_query.from_user.id if callback_query.from_user else None
    # FIX: Await the banned_users.find_one as it's an async call
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await callback_query.message.edit_text("**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Banned user {user_id} attempted to use previous page for {callback_query.data}")
        return

    try:
        current_page = int(callback_query.data.split('_', 2)[1])
        filename = callback_query.data.split('_', 2)[2]

        sellers = load_from_json_file(filename, client=client, message=callback_query.message)

        prev_page = current_page - 1
        if prev_page < 1:
            await callback_query.answer("❌ Data Expired Please Request Again To Get Latest Database")
            LOGGER.info(f"Data expired for previous page {prev_page} in chat {callback_query.message.chat.id}")
            return

        message_text = generate_message(sellers, prev_page)
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
