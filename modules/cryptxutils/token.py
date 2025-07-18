# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import aiohttp
import asyncio
from pyrogram import Client as PyroClient, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

BASE_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol="

async def fetch_crypto_data(token=None):
    try:
        url = f"{BASE_URL}{token}USDT"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                LOGGER.info(f"Successfully fetched data for {token}")
                return await response.json()
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
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /price")
            return

        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += f" {message.from_user.last_name}"

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
                 InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{token}_{user_id}")]
            ])
            await fetching_message.edit(response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
            LOGGER.info(f"Sent price info for {token} to chat {message.chat.id}")

        except Exception as e:
            LOGGER.error(f"Error processing /price for {token}: {e}")
            await notify_admin(client, "/price", e, message)
            await fetching_message.edit(f"❌ <b>Nothing Detected From Binance Database</b>", parse_mode=ParseMode.HTML)

    @app.on_callback_query(filters.regex(r"refresh_(.*?)_(\d+)$"))
    async def handle_refresh_callback(client: PyroClient, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await callback_query.message.edit_text(BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use refresh for {callback_query.data}")
            return

        callback_data_parts = callback_query.data.split("_")
        token = callback_data_parts[1]
        original_user_id = int(callback_data_parts[2])

        user_full_name = callback_query.from_user.first_name
        if callback_query.from_user.last_name:
            user_full_name += f" {callback_query.from_user.last_name}"

        if user_id != original_user_id:
            original_user = await client.get_users(original_user_id)
            original_user_name = original_user.first_name
            if original_user.last_name:
                original_user_name += f" {original_user.last_name}"
            await callback_query.answer(f"Action Disallowed. This Button Only For {original_user_name}", show_alert=True)
            return

        try:
            data = await fetch_crypto_data(token)
            old_message = callback_query.message
            new_formatted_info = format_crypto_info(data)
            old_formatted_info = old_message.text.split("\n\n", 1)[1]

            if new_formatted_info.strip() == old_formatted_info.strip():
                await callback_query.answer("No changes detected from Binance Database")
                LOGGER.info(f"No changes detected for {token} in chat {callback_query.message.chat.id}")
            else:
                response_message = f"📈 <b>Price Info for {token}:</b>\n\n{new_formatted_info}"
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Data Insight", url=f"https://www.binance.com/en/trading_insight/glass?id=44&token={token}"), 
                     InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{token}_{user_id}")]
                ])
                await old_message.edit_text(response_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)
                await callback_query.answer("Price Updated Successfully!")
                LOGGER.info(f"Updated price info for {token} in chat {callback_query.message.chat.id}")

        except Exception as e:
            LOGGER.error(f"Error in refresh for {token}: {e}")
            await notify_admin(client, "/price refresh", e, callback_query.message)
            await callback_query.answer("❌ Nothing Detected From Binance Database", show_alert=True)
