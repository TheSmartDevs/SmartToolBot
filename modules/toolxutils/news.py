# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import requests
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import NEWS_API_KEY, COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Use LOGGER and notify_admin
from core import banned_users           # Use banned_users
import pycountry

def get_country_name(country_code: str) -> str:
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name if country else country_code.upper()
    except Exception:
        return country_code.upper()

def fetch_news(country_code: str, page_token: str | None = None) -> dict:
    url = f"https://newsdata.io/api/1/news?country={country_code}&apikey={NEWS_API_KEY}"
    if page_token:
        url += f"&page={page_token}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        response_json = response.json()
        LOGGER.info(f"Fetched news for {country_code}: {response_json}")
        if response_json.get("status") == "error":
            raise ValueError(response_json.get("results", {}).get("message", "Error fetching news"))
        return response_json
    except requests.exceptions.RequestException as e:
        LOGGER.error(f"Network error fetching news for {country_code}: {e}")
        raise
    except Exception as e:
        LOGGER.error(f"Error fetching news for {country_code}: {e}")
        raise

async def send_news(
    client: Client,
    chat_id: int,
    data: dict,
    country_code: str,
    prev_page_token: str | None = None,
    next_page_token: str | None = None,
    message_id: int | None = None
):
    news_list = data.get("results", [])
    if not news_list:
        error_msg = "**No News Available**"
        if message_id:
            await client.edit_message_text(
                chat_id,
                message_id,
                error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await client.send_message(
                chat_id,
                error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
        return

    text = f"**Top Headlines ({get_country_name(country_code)})**\n\n"
    for news in news_list:
        title = news.get('title', 'No title')
        source_name = news.get('source_name', 'Unknown source')
        pub_date = news.get('pubDate', 'Unknown date')
        link = news.get('link', '#')
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"📰 **Title**: {title}\n"
        text += f"🏢 **Source**: {source_name}\n"
        text += f"⏰ **Published**: {pub_date}\n"
        text += f"🔗 [Read More]({link})\n\n"

    buttons = []
    if prev_page_token:
        buttons.append(InlineKeyboardButton("Previous", callback_data=f"{country_code}_prev_{prev_page_token}"))
    if next_page_token:
        buttons.append(InlineKeyboardButton("Next", callback_data=f"{country_code}_next_{next_page_token}"))

    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
    if message_id:
        await client.edit_message_text(
            chat_id,
            message_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await client.send_message(
            chat_id,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN
        )

def setup_news_handler(app: Client):
    @app.on_message(filters.command(["news"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def news(client: Client, message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(
                message.chat.id,
                "**✘Sorry You're Banned From Using Me↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        temp_message = None
        try:
            if len(message.command) < 2:
                await client.send_message(
                    message.chat.id,
                    "**Please provide a country code (e.g., /news us)**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            country_code = message.command[1].lower()
            LOGGER.info(f"Received news request for country code: {country_code}")
            country_name = get_country_name(country_code)
            temp_message = await client.send_message(
                message.chat.id,
                f"**Searching News for {country_name}**",
                parse_mode=ParseMode.MARKDOWN
            )
            data = fetch_news(country_code)
            await send_news(
                client,
                message.chat.id,
                data,
                country_code,
                next_page_token=data.get("nextPage"),
                message_id=temp_message.id
            )
        except Exception as e:
            LOGGER.error(f"Error handling news command: {e}")
            error_msg = "**News API Error**"
            await notify_admin(client, f"{COMMAND_PREFIX}news", e, message)
            if temp_message:
                await client.edit_message_text(
                    message.chat.id,
                    temp_message.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    message.chat.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )

    @app.on_callback_query(filters.regex(r"(\w+)_prev_(.+)"))
    async def prev_page(client: Client, callback_query):
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await callback_query.answer("✘Sorry You're Banned From Using Me↯", show_alert=True)
            return

        temp_message = None
        try:
            country_code, prev_page_token = callback_query.data.split("_")[0], callback_query.data.split("_")[2]
            LOGGER.info(f"Fetching previous page for {country_code}, token: {prev_page_token}")
            country_name = get_country_name(country_code)
            temp_message = await client.send_message(
                callback_query.message.chat.id,
                f"**Searching News for {country_name}**",
                parse_mode=ParseMode.MARKDOWN
            )
            data = fetch_news(country_code, prev_page_token)
            await send_news(
                client,
                callback_query.message.chat.id,
                data,
                country_code,
                prev_page_token=None,  # No previous page for the previous fetch
                next_page_token=data.get("nextPage"),
                message_id=temp_message.id
            )
        except Exception as e:
            LOGGER.error(f"Error handling previous page: {e}")
            error_msg = "**News API Error**"
            await notify_admin(client, f"{COMMAND_PREFIX}news_prev", e, callback_query.message)
            if temp_message:
                await client.edit_message_text(
                    callback_query.message.chat.id,
                    temp_message.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    callback_query.message.chat.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )

    @app.on_callback_query(filters.regex(r"(\w+)_next_(.+)"))
    async def next_page(client: Client, callback_query):
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await callback_query.answer("✘Sorry You're Banned From Using Me↯", show_alert=True)
            return

        temp_message = None
        try:
            country_code, next_page_token = callback_query.data.split("_")[0], callback_query.data.split("_")[2]
            LOGGER.info(f"Fetching next page for {country_code}, token: {next_page_token}")
            country_name = get_country_name(country_code)
            temp_message = await client.send_message(
                callback_query.message.chat.id,
                f"**Searching News for {country_name}**",
                parse_mode=ParseMode.MARKDOWN
            )
            data = fetch_news(country_code, next_page_token)
            await send_news(
                client,
                callback_query.message.chat.id,
                data,
                country_code,
                prev_page_token=next_page_token,  # Current token becomes previous for next fetch
                next_page_token=data.get("nextPage"),
                message_id=temp_message.id
            )
        except Exception as e:
            LOGGER.error(f"Error handling next page: {e}")
            error_msg = "**News API Error**"
            await notify_admin(client, f"{COMMAND_PREFIX}news_next", e, callback_query.message)
            if temp_message:
                await client.edit_message_text(
                    callback_query.message.chat.id,
                    temp_message.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    callback_query.message.chat.id,
                    error_msg,
                    parse_mode=ParseMode.MARKDOWN
                )