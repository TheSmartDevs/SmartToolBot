#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import pytz
import pycountry
from datetime import datetime
import calendar
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_holidays
from config import COMMAND_PREFIX

async def get_calendar_markup(year, month, country_code):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now()

    # Navigation buttons
    prev_month = month - 1 if month > 1 else 12
    next_month = month + 1 if month < 12 else 1
    prev_year = year - 1 if month == 1 else year
    next_year = year + 1 if month == 12 else year

    navigation_buttons = [
        InlineKeyboardButton("<", callback_data=f"nav_{country_code}_{prev_year}_{prev_month}"),
        InlineKeyboardButton("Today", callback_data=f"nav_{country_code}_{now.year}_{now.month}"),
        InlineKeyboardButton(">", callback_data=f"nav_{country_code}_{next_year}_{next_month}"),
    ]

    # Days of the week header
    days_buttons = [[InlineKeyboardButton(day, callback_data="ignore") 
                   for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]]]

    # Get holidays for the country
    country_holidays = get_holidays(country_code)

    # Calendar days
    day_buttons = []
    for week in month_days:
        day_row = []
        for day in week:
            if day == 0:
                day_row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                holiday_info = country_holidays.get((month, day))
                if holiday_info:
                    button_text = f"🔴 {day}"
                    callback_data = f"hol_{country_code}_{month:02d}_{day:02d}"
                else:
                    button_text = str(day)
                    callback_data = f"day_{country_code}_{month:02d}_{day:02d}"

                if day == now.day and month == now.month and year == now.year:
                    button_text = f"🔵 {day}"

                day_row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        day_buttons.append(day_row)

    # Get country info
    country = pycountry.countries.get(alpha_2=country_code)
    if not country:
        raise ValueError("Invalid country code")

    country_name = country.name
    flag_emoji = "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code)

    # Get timezone
    time_zones = pytz.country_timezones.get(country_code)
    if not time_zones:
        raise ValueError("No timezone found for this country")

    tz = pytz.timezone(time_zones[0])
    now = datetime.now(tz)
    current_time = now.strftime("%I:%M:%S %p")

    # Build keyboard
    keyboard = [
        [InlineKeyboardButton(f"{calendar.month_name[month]} {year} 🟢", callback_data="ignore"),
         InlineKeyboardButton(f"{now.strftime('%d %b, %Y')}", callback_data="ignore")],
        [InlineKeyboardButton(f"📅 {flag_emoji} {country_name} | {current_time}", callback_data="ignore")]
    ] + days_buttons + day_buttons + [navigation_buttons]

    return InlineKeyboardMarkup(keyboard)

async def get_time_and_calendar(country_code):
    country = pycountry.countries.get(alpha_2=country_code)
    if not country:
        raise ValueError("Invalid country code")

    country_name = country.name
    flag_emoji = "".join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code)

    time_zones = pytz.country_timezones.get(country_code)
    if not time_zones:
        raise ValueError("No timezone found for this country")

    tz = pytz.timezone(time_zones[0])
    now = datetime.now(tz)
    time_str = now.strftime("%I:%M:%S %p")
    
    # Get today's holiday
    country_holidays = get_holidays(country_code)
    today_holiday = country_holidays.get((now.month, now.day))
    
    # Prepare message
    message = f"📅 {flag_emoji} <b>{country_name} Calendar | ⏰ {time_str} 👇</b>"
    
    # Add today's holiday if exists
    if today_holiday:
        message += f"\n\n<b>🎊 Today's Holiday:</b> {today_holiday}"

    calendar_markup = await get_calendar_markup(now.year, now.month, country_code)

    return (message, calendar_markup)

def setup_time_handler(app: Client):
    @app.on_message(filters.command(["time", "calendar"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_time_command(client, message):
        if len(message.command) < 2:
            await client.send_message(
                message.chat.id,
                "<b>❌ Ensure you provide a valid country code.</b>",
                parse_mode=ParseMode.HTML
            )
            return

        country_code = message.command[1].upper().strip()
        
        try:
            header_text, calendar_markup = await get_time_and_calendar(country_code)
            await client.send_message(
                message.chat.id,
                header_text,
                parse_mode=ParseMode.HTML,
                reply_markup=calendar_markup
            )
        except ValueError as e:
            await client.send_message(
                message.chat.id,
                "<b>❌ Ensure you provide a valid country code.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
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
            calendar_markup = await get_calendar_markup(year, month, country_code)
            await callback_query.message.edit_reply_markup(reply_markup=calendar_markup)
            await callback_query.answer()
        except Exception as e:
            await callback_query.answer(f"Sorry My Database Locked", show_alert=True)

    @app.on_callback_query(filters.regex(r'^hol_'))
    async def handle_holiday_click(client, callback_query):
        try:
            _, country_code, month, day = callback_query.data.split('_')
            month = int(month)
            day = int(day)
            
            holidays = get_holidays(country_code)
            holiday_name = holidays.get((month, day))
            
            if holiday_name:
                await callback_query.answer(holiday_name, show_alert=True)
            else:
                await callback_query.answer("No holiday found", show_alert=True)
        except Exception as e:
            await callback_query.answer(f"Sorry My Database Locked", show_alert=True)

    @app.on_callback_query(filters.regex(r'^day_'))
    async def handle_day_click(client, callback_query):
        try:
            _, country_code, month, day = callback_query.data.split('_')
            month = int(month)
            day = int(day)
            
            holidays = get_holidays(country_code)
            holiday_name = holidays.get((month, day))
            
            if holiday_name:
                await callback_query.answer(holiday_name, show_alert=True)
            else:
                await callback_query.answer(f"{day} {calendar.month_name[month]} - No holiday", show_alert=True)
        except Exception as e:
            await callback_query.answer(f"Sorry My Database Locked", show_alert=True)

    @app.on_callback_query(filters.regex('^ignore$'))
    async def handle_ignore(client, callback_query):
        await callback_query.answer()