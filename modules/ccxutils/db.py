import aiohttp
import asyncio
import json
import os
import pycountry
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users
from telegraph import Telegraph

country_url = "https://smartdb-production-9dbf.up.railway.app/api/bin"
bank_url = "https://smartdb-production-9dbf.up.railway.app/api/bin"

telegraph = Telegraph()
try:
    telegraph.create_account(
        short_name="SmartUtilBot",
        author_name="SmartUtilBot",
        author_url="https://t.me/TheSmartDevs"
    )
except Exception as e:
    LOGGER.error(f"Failed to create or access Telegraph account: {e}")

async def fetch_bins(params, client=None, message=None, endpoint="country"):
    try:
        async with aiohttp.ClientSession() as session:
            url = country_url if endpoint == "country" else bank_url
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    LOGGER.error(f"Error fetching data: {response.status}")
                    raise Exception(f"API request failed with status {response.status}")
                data = await response.json()
                if data.get("status") != "SUCCESS" or not data.get("data"):
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

async def create_telegraph_page(content: str) -> list:
    try:
        truncated_content = content[:40000]
        max_size_bytes = 20 * 1024
        pages = []
        page_content = ""
        current_size = 0
        lines = truncated_content.splitlines(keepends=True)
        for line in lines:
            line_bytes = line.encode('utf-8', errors='ignore')
            if current_size + len(line_bytes) > max_size_bytes and page_content:
                safe_content = page_content.replace('<', '&lt;').replace('>', '&gt;')
                html_content = f'<pre>{safe_content}</pre>'
                page = telegraph.create_page(
                    title="SmartBins",
                    html_content=html_content,
                    author_name="SmartUtilBot",
                    author_url="https://t.me/TheSmartDevs"
                )
                # Replace telegra.ph with graph.org in the URL
                graph_url = page['url'].replace('telegra.ph', 'graph.org')
                pages.append(graph_url)
                page_content = ""
                current_size = 0
                await asyncio.sleep(0.5)
            page_content += line
            current_size += len(line_bytes)
        if page_content:
            safe_content = page_content.replace('<', '&lt;').replace('>', '&gt;')
            html_content = f'<pre>{safe_content}</pre>'
            page = telegraph.create_page(
                title="SmartBins",
                html_content=html_content,
                author_name="SmartUtilBot",
                author_url="https://t.me/TheSmartDevs"
            )
            # Replace telegra.ph with graph.org in the URL
            graph_url = page['url'].replace('telegra.ph', 'graph.org')
            pages.append(graph_url)
            await asyncio.sleep(0.5)
        return pages
    except Exception as e:
        LOGGER.error(f"Failed to create Telegraph page: {e}")
        return []

def generate_message(bins, identifier):
    message = f"**Smart Tool - Bin database 📋**\n**━━━━━━━━━━━━━━━━━━**\n\n"
    for i, bin_data in enumerate(bins[:5], start=1):
        message += (f"{i}. **BIN:** `{bin_data['bin']}`\n"
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
        LOGGER.info(f"Fetching BINs for country {country_name} ({country_code})")
        loading_message = await client.send_message(message.chat.id, f"**Finding Bins With Country {country_name}...**", parse_mode=ParseMode.MARKDOWN)
        params = {"country": country_code, "limit": 8000}
        bins = await fetch_bins(params, client=client, message=message, endpoint="country")
        if not bins:
            await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry No Bins Found**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"No bins found for country {country_code}")
            return
        processed_bins = process_bins_to_json(bins)
        message_text = generate_message(processed_bins, country_code)
        keyboard = None
        if len(processed_bins) > 5:
            bins_content = json.dumps(processed_bins[5:], indent=2)
            content_size = len(bins_content.encode('utf-8'))
            telegraph_urls = await create_telegraph_page(bins_content)
            if telegraph_urls:
                buttons = []
                if content_size <= 20 * 1024:
                    buttons.append([InlineKeyboardButton("Full Output", url=telegraph_urls[0])])
                else:
                    for i in range(0, len(telegraph_urls), 2):
                        row = [
                            InlineKeyboardButton(f"Output {i+1}", url=telegraph_urls[i])
                        ]
                        if i + 1 < len(telegraph_urls):
                            row.append(InlineKeyboardButton(f"Output {i+2}", url=telegraph_urls[i+1]))
                        buttons.append(row)
                keyboard = InlineKeyboardMarkup(buttons)
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
        LOGGER.info(f"Fetching BINs for bank {bank_name}")
        loading_message = await client.send_message(message.chat.id, f"**Finding Bins With Bank {bank_name}...**", parse_mode=ParseMode.MARKDOWN)
        params = {"bank": bank_name, "limit": 8000}
        bins = await fetch_bins(params, client=client, message=message, endpoint="bank")
        if not bins:
            await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry No Bins Found**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.warning(f"No bins found for bank {bank_name}")
            return
        processed_bins = process_bins_to_json(bins)
        message_text = generate_message(processed_bins, bank_name)
        keyboard = None
        if len(processed_bins) > 5:
            bins_content = json.dumps(processed_bins[5:], indent=2)
            content_size = len(bins_content.encode('utf-8'))
            telegraph_urls = await create_telegraph_page(bins_content)
            if telegraph_urls:
                buttons = []
                if content_size <= 20 * 1024:
                    buttons.append([InlineKeyboardButton("Full Output", url=telegraph_urls[0])])
                else:
                    for i in range(0, len(telegraph_urls), 2):
                        row = [
                            InlineKeyboardButton(f"Output {i+1}", url=telegraph_urls[i])
                        ]
                        if i + 1 < len(telegraph_urls):
                            row.append(InlineKeyboardButton(f"Output {i+2}", url=telegraph_urls[i+1]))
                        buttons.append(row)
                keyboard = InlineKeyboardMarkup(buttons)
        await client.edit_message_text(message.chat.id, loading_message.id, message_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        LOGGER.info(f"Sent BINs for bank {bank_name} to chat {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Exception in binbank_handler: {e}")
        await client.edit_message_text(message.chat.id, loading_message.id, "**Sorry, an error occurred while fetching BIN data ❌**", parse_mode=ParseMode.MARKDOWN)
        await notify_admin(client, "/binbank", e, message)

def setup_db_handlers(app: Client):
    app.add_handler(MessageHandler(bindb_handler, filters.command(["bindb"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
    app.add_handler(MessageHandler(binbank_handler, filters.command(["binbank"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
