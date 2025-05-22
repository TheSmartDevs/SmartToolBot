# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import requests
import asyncio
import logging
from pyrogram import Client as PyroClient, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol="

async def fetch_crypto_data(token=None):
    try:
        url = f"{BASE_URL}{token}USDT"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching data from the provided URL: {e}")
        raise Exception("<b>❌ Data unavailable or invalid token symbol </b>")

def format_crypto_info(data):
    result = (
        f"📊 <b>Symbol:</b> {data['symbol']}\n"
        f"↕️ <b>Change:</b> {data['priceChangePercent']}%\n"
        f"💰 <b>Last Price:</b> {data['lastPrice']}\n"
        f"📈 <b>24h High:</b> {data['highPrice']}\n"
        f"📉 <b>24h Low:</b> {data['lowPrice']}\n"
        f"🔄 <b>24h Volume:</b> {data['volume']}\n"
        f"💵 <b>24h Quote Volume:</b> {data['quoteVolume']}\n\n"
    )
    return result

def setup_crypto_handler(app: PyroClient):
    @app.on_message(filters.command("price", prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_price_command(client: PyroClient, message: Message):
        if len(message.command) < 2:
            await client.send_message(message.chat.id, "❌ <b>Please provide a token symbol</b>", parse_mode=ParseMode.HTML)
            return
        
        token = message.command[1].upper()
        fetching_message = await client.send_message(message.chat.id, f" <b>Fetching Token Price..✨</b>", parse_mode=ParseMode.HTML)
        
        try:
            data = await fetch_crypto_data(token)
            formatted_info = format_crypto_info(data)
            response_message = f"📈 <b>Price Info for {token}:</b>\n\n{formatted_info}"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Data Insight", url=f"https://www.binance.com/en/trading_insight/glass?id=44&token={token}"), 
                 InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{token}")]
            ])
            await fetching_message.edit(f"📈 <b>Price Info for {token}:</b>\n\n{formatted_info}", parse_mode=ParseMode.HTML, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error fetching data for {token}: {e}")
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}price", e, message)
            # Send user-facing error message
            await fetching_message.edit(f"❌ <b>Nothing Detected From Binance Database</b>", parse_mode=ParseMode.HTML)

    @app.on_callback_query(filters.regex(r"refresh_(.*)"))
    async def handle_refresh_callback(client: PyroClient, callback_query: CallbackQuery):
        token = callback_query.data.split("_")[1]
        try:
            data = await fetch_crypto_data(token)
            old_message = callback_query.message
            new_formatted_info = format_crypto_info(data)
            old_formatted_info = old_message.text.split("\n\n", 1)[1]

            if new_formatted_info.strip() == old_formatted_info.strip():
                await callback_query.answer("❌ No Changes Detected From Binance Database", show_alert=True)
            else:
                response_message = f"📈 <b>Price Info for {token}:</b>\n\n{new_formatted_info}"
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Data Insight", url=f"https://www.binance.com/en/trading_insight/glass?id=44&token={token}"), 
                     InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{token}")]
                ])
                await old_message.edit_text(response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error fetching data for {token}: {e}")
            # Notify admins
            await notify_admin(client, "refresh_callback", e, callback_query.message)
            # Send user-facing error message
            await callback_query.answer(f"❌ No Changes Detected From Binance Database", show_alert=True)
