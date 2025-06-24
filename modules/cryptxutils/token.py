# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import requests
import asyncio
from pyrogram import Client as PyroClient, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

BASE_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol="

async def fetch_crypto_data(token=None):
    try:
        url = f"{BASE_URL}{token}USDT"
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, requests.get, url)
        response.raise_for_status()
        LOGGER.info(f"Successfully fetched data for {token}")
        return response.json()
    except Exception as e:
        LOGGER.error(f"Error fetching data for {token}: {e}")
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
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /price")
            return

        if len(message.command) < 2:
            await client.send_message(message.chat.id, "❌ <b>Please provide a token symbol</b>", parse_mode=ParseMode.HTML)
            LOGGER.warning(f"Invalid command format: {message.text}")
            return
        
        token = message.command[1].upper()
        fetching_message = await client.send_message(message.chat.id, f"<b>Fetching Token Price..✨</b>", parse_mode=ParseMode.HTML)
        
        try:
            data = await fetch_crypto_data(token)
            formatted_info = format_crypto_info(data)
            response_message = f"📈 <b>Price Info for {token}:</b>\n\n{formatted_info}"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Data Insight", url=f"https://www.binance.com/en/trading_insight/glass?id=44&token={token}"), 
                 InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{token}")]
            ])
            await fetching_message.edit(response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            LOGGER.info(f"Sent price info for {token} to chat {message.chat.id}")

        except Exception as e:
            LOGGER.error(f"Error processing /price for {token}: {e}")
            # Notify admins
            await notify_admin(client, "/price", e, message)
            # Send user-facing error message
            await fetching_message.edit(f"❌ <b>Nothing Detected From Binance Database</b>", parse_mode=ParseMode.HTML)

    @app.on_callback_query(filters.regex(r"refresh_(.*)"))
    async def handle_refresh_callback(client: PyroClient, callback_query: CallbackQuery):
        # Check if user is banned
        user_id = callback_query.from_user.id if callback_query.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await callback_query.message.edit_text("**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use refresh for {callback_query.data}")
            return

        token = callback_query.data.split("_")[1]
        try:
            data = await fetch_crypto_data(token)
            old_message = callback_query.message
            new_formatted_info = format_crypto_info(data)
            old_formatted_info = old_message.text.split("\n\n", 1)[1]

            if new_formatted_info.strip() == old_formatted_info.strip():
                await callback_query.answer("❌ No Changes Detected From Binance Database", show_alert=True)
                LOGGER.info(f"No changes detected for {token} in chat {callback_query.message.chat.id}")
            else:
                response_message = f"📈 <b>Price Info for {token}:</b>\n\n{new_formatted_info}"
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Data Insight", url=f"https://www.binance.com/en/trading_insight/glass?id=44&token={token}"), 
                     InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{token}")]
                ])
                await old_message.edit_text(response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
                await callback_query.answer("Token Price Updated✨", show_alert=True)
                LOGGER.info(f"Updated price info for {token} in chat {callback_query.message.chat.id}")

        except Exception as e:
            LOGGER.error(f"Error in refresh for {token}: {e}")
            # Notify admins
            await notify_admin(client, "/price refresh", e, callback_query.message)
            # Send user-facing error message
            await callback_query.answer("❌ No Changes Detected From Binance Database", show_alert=True)
