# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

BASE_URL = "https://api.binance.com/api/v3/ticker/24hr"

async def fetch_crypto_data():
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, requests.get, BASE_URL)
        response.raise_for_status()
        LOGGER.info("Successfully fetched crypto data from Binance API")
        return response.json()
    except Exception as e:
        LOGGER.error(f"Failed to fetch crypto data: {e}")
        raise

def get_top_gainers(data, top_n=5):
    sorted_data = sorted(data, key=lambda x: float(x['priceChangePercent']), reverse=True)
    return sorted_data[:top_n]

def get_top_losers(data, top_n=5):
    sorted_data = sorted(data, key=lambda x: float(x['priceChangePercent']))
    return sorted_data[:top_n]

def format_crypto_info(data, start_index=0):
    result = ""
    for idx, item in enumerate(data, start=start_index + 1):
        result += (
            f"<b>{idx}. Symbol:</b> {item['symbol']}\n"
            f"  <b>💳Change:</b> {item['priceChangePercent']}%\n"
            f"  <b>💵Last Price:</b> {item['lastPrice']}\n"
            f"  <b>📈24h High:</b> {item['highPrice']}\n"
            f"  <b>📉24h Low:</b> {item['lowPrice']}\n"
            f"  <b>💰24h Volume:</b> {item['volume']}\n"
            f"  <b>✅24h Quote Volume:</b> {item['quoteVolume']}\n\n"
        )
    return result

def setup_binance_handler(app: Client):
    @app.on_message(filters.command(["gainers", "losers"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_command(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /{message.command[0]}")
            return

        command = message.command[0]
        fetching_message = await client.send_message(message.chat.id, f"<b>Fetching {command}...✨</b>", parse_mode=ParseMode.HTML)
        
        try:
            data = await fetch_crypto_data()
            top_n = 5
            if command == "gainers":
                top_cryptos = get_top_gainers(data, top_n)
                title = "Gainers"
            else:
                top_cryptos = get_top_losers(data, top_n)
                title = "Losers"

            formatted_info = format_crypto_info(top_cryptos)
            await fetching_message.delete()
            response_message = f"<b>🔥 List Of Top {title}:</b>\n\n{formatted_info}"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Next", callback_data=f"{command}_1")]
            ])
            await client.send_message(message.chat.id, response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            LOGGER.info(f"Sent top {title.lower()} to chat {message.chat.id}")

        except Exception as e:
            await fetching_message.delete()
            await client.send_message(message.chat.id, f"<b>❌ Sorry Binance API Dead</b>", parse_mode=ParseMode.HTML)
            LOGGER.error(f"Error processing /{command}: {e}")
            # Notify admins about the error
            await notify_admin(client, f"/{command}", e, message)

    @app.on_callback_query(filters.regex(r"^(gainers|losers)_\d+"))
    async def handle_pagination(client: Client, callback_query: CallbackQuery):
        # Check if user is banned
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await callback_query.message.edit_text("**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use pagination for {callback_query.data}")
            return

        command, page = callback_query.data.split('_')
        page = int(page)
        next_page = page + 1
        prev_page = page - 1

        try:
            data = await fetch_crypto_data()
            top_n = 5
            if command == "gainers":
                top_cryptos = get_top_gainers(data, top_n * next_page)[(page-1)*top_n:page*top_n]
                title = "Gainers"
            else:
                top_cryptos = get_top_losers(data, top_n * next_page)[(page-1)*top_n:page*top_n]
                title = "Losers"

            formatted_info = format_crypto_info(top_cryptos, start_index=(page-1)*top_n)
            response_message = f"<b>🔥 List Of Top {title}:</b>\n\n{formatted_info}"

            keyboard_buttons = []
            if prev_page > 0:
                keyboard_buttons.append(InlineKeyboardButton("Previous", callback_data=f"{command}_{prev_page}"))
            if len(top_cryptos) == top_n:
                keyboard_buttons.append(InlineKeyboardButton("Next", callback_data=f"{command}_{next_page}"))

            keyboard = InlineKeyboardMarkup([keyboard_buttons])
            await callback_query.message.edit_text(response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            LOGGER.info(f"Updated pagination for {command} (page {page}) in chat {callback_query.message.chat.id}")

        except Exception as e:
            await callback_query.message.edit_text(f"<b>❌ Sorry Bro Binance API Dead</b>", parse_mode=ParseMode.HTML)
            LOGGER.error(f"Error in pagination for {command} (page {page}): {e}")
            # Notify admins about the error
            await notify_admin(client, f"/{command} pagination", e, callback_query.message)