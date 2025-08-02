import pytz
import pycountry
from datetime import datetime
import calendar
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import LOGGER
from config import COMMAND_PREFIX, BAN_REPLY
from core import banned_users
import threading
import os
import time

def get_flag(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if not country:
            return None, "🏳️"
        country_name = country.name
        
        flag_emoji = ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper())
        if not all(0x1F1E6 <= ord(c) <= 0x1F1FF for c in flag_emoji):  
            return country_name, "🏳️"  
        return country_name, flag_emoji
    except Exception as e:
        LOGGER.error(f"Error in get_flag: {str(e)}")
        return None, "🏳️"

async def create_centered_calendar_image(country_name, time_str, date_str, output_path):
    outer_width, outer_height = 1340, 740
    inner_width, inner_height = 1300, 700
    background_color = (0, 0, 0)
    inner_color = (30, 39, 50)
    border_color = (255, 215, 0)
    text_white = (255, 255, 255)
    text_yellow = (255, 215, 0)
    img = Image.new("RGB", (outer_width, outer_height), color=background_color)
    draw = ImageDraw.Draw(img)
    font_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
    font_date = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
    font_country = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
    bbox_time = draw.textbbox((0, 0), time_str, font=font_time)
    time_top = bbox_time[1]
    time_bottom = bbox_time[3]
    time_width = bbox_time[2] - bbox_time[0]
    visual_h_time = time_bottom - time_top
    bbox_date = draw.textbbox((0, 0), date_str, font=font_date)
    date_top = bbox_date[1]
    date_bottom = bbox_date[3]
    date_width = bbox_date[2] - bbox_date[0]
    visual_h_date = date_bottom - date_top
    bbox_country = draw.textbbox((0, 0), country_name, font=font_country)
    country_top = bbox_country[1]
    country_bottom = bbox_country[3]
    country_width = bbox_country[2] - bbox_country[0]
    visual_h_country = country_bottom - country_top
    gap_time_date = 60
    gap_date_country = 40
    gap_country_credit = 20
    total_visual_height = visual_h_time + gap_time_date + visual_h_date + gap_date_country + visual_h_country + gap_country_credit
    start_y = ((outer_height - inner_height) // 2 + (inner_height - total_visual_height) // 2) - time_top
    draw.rectangle([(20, 20), (20 + inner_width - 1, 20 + inner_height - 1)], fill=inner_color)
    draw.rectangle([(20, 20), (20 + inner_width - 1, 20 + inner_height - 1)], outline=border_color, width=5)
    x_time = (inner_width - time_width) // 2 + 20
    draw.text((x_time, start_y), time_str, font=font_time, fill=text_white)
    date_y = start_y + time_bottom + gap_time_date - date_top
    x_date = (inner_width - date_width) // 2 + 20
    draw.text((x_date, date_y), date_str, font=font_date, fill=text_white)
    country_y = date_y + date_bottom + gap_date_country - country_top
    x_country = (inner_width - country_width) // 2 + 20
    draw.text((x_country, country_y), country_name, font=font_country, fill=text_yellow)
    credit_text = "Smart Time By @ISmartCoder"
    bbox_credit = draw.textbbox((0, 0), credit_text, font=font_country)
    credit_width = bbox_credit[2] - bbox_credit[0]
    credit_y = country_y + country_bottom + gap_country_credit - country_top
    x_credit = (inner_width - credit_width) // 2 + 20
    draw.text((x_credit, credit_y), credit_text, font=font_country, fill=text_white)
    img.save(output_path)
    return output_path

async def create_calendar_image(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        country_name = country.name if country else "Unknown"
        
        time_zones = {
            "gb": ["Europe/London"],
            "ae": ["Asia/Dubai"]
        }.get(country_code, pytz.country_timezones.get(country_code))
        if time_zones:
            tz = pytz.timezone(time_zones[0])
            now = datetime.now(tz)
            time_str = now.strftime("%I:%M:%S %p")
            date_str = now.strftime("%d %b, %Y (%A)")
        else:
            time_str = "00:00:00 AM"
            date_str = "Unknown Date"
        await create_centered_calendar_image(country_name, time_str, date_str, f"calendar_{country_code}.png")
        def delete_image():
            time.sleep(20)
            if os.path.exists(f"calendar_{country_code}.png"):
                os.remove(f"calendar_{country_code}.png")
        threading.Thread(target=delete_image, daemon=True).start()
    except Exception as e:
        LOGGER.error(f"Error creating calendar image: {str(e)}")

async def get_calendar_markup(year, month, country_code):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    prev_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    prev_year = year - 1 if month == 1 else year
    next_year = year + 1 if month == 12 else year
    navigation_buttons = [
        InlineKeyboardButton("<", callback_data=f"nav_{country_code}_{prev_year}_{prev_month}"),
        InlineKeyboardButton(">", callback_data=f"nav_{country_code}_{next_year}_{next_month}"),
    ]
    days_buttons = [[InlineKeyboardButton(day, callback_data=f"alert_{country_code}_{year}_{month}") for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]]]
    day_buttons = []
    for week in month_days:
        day_row = []
        for day in week:
            if day == 0:
                day_row.append(InlineKeyboardButton(" ", callback_data=f"alert_{country_code}_{year}_{month}"))
            else:
                button_text = str(day)
                callback_data = f"day_{country_code}_{month:02d}_{day:02d}"
                day_row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        day_buttons.append(day_row)
    country = pycountry.countries.get(alpha_2=country_code)
    country_name = country.name
    flag_emoji = get_flag(country_code)[1]
    time_zones = {
        "gb": ["Europe/London"],
        "ae": ["Asia/Dubai"]
    }.get(country_code, pytz.country_timezones.get(country_code))
    if time_zones:
        tz = pytz.timezone(time_zones[0])
        now_tz = datetime.now(tz)
        current_time = now_tz.strftime("%I:%M:%S %p")
    else:
        now_tz = datetime.now()
        current_time = "00:00:00 AM"
    keyboard = []
    if month == now_tz.month and year == now_tz.year:
        keyboard.append([
            InlineKeyboardButton(f"{calendar.month_name[month]} {year} 📅", callback_data=f"alert_{country_code}_{year}_{month}"),
            InlineKeyboardButton(f"{now_tz.strftime('%d %b, %Y')}", callback_data=f"alert_{country_code}_{year}_{month}")
        ])
        keyboard.append([
            InlineKeyboardButton(f" {flag_emoji} {country_name} | {current_time}", callback_data=f"alert_{country_code}_{year}_{month}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data=f"alert_{country_code}_{year}_{month}")
        ])
    keyboard += days_buttons + day_buttons + [navigation_buttons]
    return InlineKeyboardMarkup(keyboard)

async def get_time_and_calendar(country_input, year=None, month=None):
    country_code = None
    try:
        country_input = country_input.lower().strip()
        
        if country_input in ["uk", "united kingdom"]:
            country_code = "gb"
        elif country_input in ["uae", "united arab emirates"]:
            country_code = "ae"
        else:
            try:
                country = pycountry.countries.search_fuzzy(country_input)[0]
                country_code = country.alpha_2
            except LookupError:
                country_code = country_input.upper().strip()
                if len(country_code) != 2 or not pycountry.countries.get(alpha_2=country_code):
                    raise ValueError("Invalid country code or name")
        country = pycountry.countries.get(alpha_2=country_code)
        country_name, flag_emoji = get_flag(country_code)
        if not country_name:
            country_name = "Unknown"
        time_zones = {
            "gb": ["Europe/London"],
            "ae": ["Asia/Dubai"]
        }.get(country_code, pytz.country_timezones.get(country_code))
        if time_zones:
            tz = pytz.timezone(time_zones[0])
            now = datetime.now(tz)
            time_str = now.strftime("%I:%M:%S %p")
        else:
            now = datetime.now()
            time_str = "00:00:00 AM"
        if year is None or month is None:
            year = now.year
            month = now.month
        date_str = now.strftime("%d %b, %Y (%A)")
        message = f"📅 {flag_emoji} <b>{country_name} Calendar | ⏰ {time_str} 👇</b>"
        calendar_markup = await get_calendar_markup(year, month, country_code)
        await create_calendar_image(country_code)
        return (message, calendar_markup, country_code, year, month)
    except ValueError as e:
        raise ValueError(str(e))

def setup_time_handler(app: Client):
    @app.on_message(filters.command(["time", "calendar"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_time_command(client, message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(
                message.chat.id,
                BAN_REPLY,
                parse_mode=ParseMode.HTML
            )
            return
        if len(message.command) < 2:
            await client.send_message(
                message.chat.id,
                "<b>❌ Ensure you provide a valid country code or name.</b>",
                parse_mode=ParseMode.HTML
            )
            return
        country_input = message.command[1].lower().strip()
        try:
            header_text, calendar_markup, country_code, year, month = await get_time_and_calendar(country_input)
            sent_message = await client.send_photo(
                message.chat.id,
                photo=f"calendar_{country_code}.png",
                caption=header_text,
                parse_mode=ParseMode.HTML,
                reply_markup=calendar_markup
            )
        except ValueError as e:
            LOGGER.error(f"ValueError in handle_time_command: {str(e)}")
            await client.send_message(
                message.chat.id,
                "<b>❌ Ensure you provide a valid country code or name.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            LOGGER.error(f"Exception in handle_time_command: {str(e)}")
            await client.send_message(
                message.chat.id,
                "<b>The Country Is Not In My Database</b>",
                parse_mode=ParseMode.HTML
            )
    @app.on_callback_query(filters.regex(r'^nav_'))
    async def handle_calendar_nav(client, callback_query):
        try:
            _, country_code, year, month = callback_query.data.split('_')
            year = int(year)
            month = int(month)
            header_text, calendar_markup, _, _, _ = await get_time_and_calendar(country_code, year, month)
            await create_calendar_image(country_code)
            await callback_query.message.edit_caption(
                caption=header_text,
                parse_mode=ParseMode.HTML,
                reply_markup=calendar_markup
            )
            await callback_query.answer()
        except Exception as e:
            LOGGER.error(f"Exception in handle_calendar_nav: {str(e)}")
            await callback_query.answer(f"Sorry Invalid Button Query", show_alert=True)
    @app.on_callback_query(filters.regex(r'^alert_'))
    async def handle_alert(client, callback_query):
        await callback_query.answer("This Is The Button For Calendar", show_alert=True)
    @app.on_callback_query(filters.regex(r'^day_'))
    async def handle_day_click(client, callback_query):
        try:
            _, country_code, month, day = callback_query.data.split('_')
            month = int(month)
            day = int(day)
            await callback_query.answer(f"{day} {calendar.month_name[month]} - No holiday", show_alert=True)
        except Exception as e:
            LOGGER.error(f"Exception in handle_day_click: {str(e)}")
            await callback_query.answer(f"Sorry Invalid Button Query", show_alert=True)
