from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from pyrogram.enums import ParseMode
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from config import COMMAND_PREFIX, BAN_REPLY
from utils import notify_admin, LOGGER
from core import banned_users
import os
import pytz
import pycountry
import re

executor = ThreadPoolExecutor()

async def fetch_data(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        return None

def get_timezone_from_coordinates(lat, lon):
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=lat, lng=lon)
        if timezone_str:
            return pytz.timezone(timezone_str)
    except Exception as e:
        LOGGER.error(f"Timezone lookup failed: {str(e)}")
    timezone_mapping = {
        'BD': 'Asia/Dhaka', 'IN': 'Asia/Kolkata', 'PK': 'Asia/Karachi',
        'US': 'America/New_York', 'GB': 'Europe/London', 'FR': 'Europe/Paris',
        'DE': 'Europe/Berlin', 'JP': 'Asia/Tokyo', 'CN': 'Asia/Shanghai',
        'AU': 'Australia/Sydney', 'CA': 'America/Toronto', 'BR': 'America/Sao_Paulo',
        'RU': 'Europe/Moscow', 'AE': 'Asia/Dubai', 'SA': 'Asia/Riyadh'
    }
    return pytz.timezone(timezone_mapping.get('BD', 'UTC'))

def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name if country else country_code
    except Exception as e:
        LOGGER.error(f"Country name lookup failed: {str(e)}")
        return country_code

def create_weather_image(weather_data, output_path="weather_output.png"):
    current = weather_data["current"]
    try:
        timezone = get_timezone_from_coordinates(weather_data["lat"], weather_data["lon"])
        local_time = datetime.now(timezone)
        time_text = local_time.strftime("%I:%M %p")
    except Exception as e:
        LOGGER.error(f"Time formatting failed: {str(e)}")
        time_text = datetime.now().strftime("%I:%M %p")
    
    main_title = "Current Weather"
    temp_text = f"{current['temp']}°C"
    condition_text = current["weather"]
    realfeel_text = f"RealFeel® {current['feels_like']}°C"
    country_name = get_country_name(weather_data['country_code'])
    location_text = f"{weather_data['city']}, {country_name}"
    
    img_width, img_height = 1200, 600
    background_color = (30, 39, 50)
    white = (255, 255, 255)
    light_gray = (200, 200, 200)

    img = Image.new("RGB", (img_width, img_height), color=background_color)
    draw = ImageDraw.Draw(img)

    try:
        font_bold_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_regular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception as e:
        LOGGER.error(f"Font loading failed: {str(e)}")
        font_bold_large = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((1140, 30), time_text, font=font_regular, fill=light_gray, anchor="ra")
    draw.text((40, 40), main_title, font=font_bold, fill=white)

    icon_x, icon_y = 320, 230
    for i in range(3):
        y = icon_y + i * 15
        draw.line([(icon_x, y), (icon_x + 60, y)], fill=light_gray, width=5)

    temp_x = 500
    temp_y = 180
    draw.text((temp_x, temp_y), temp_text, font=font_bold_large, fill=white)
    draw.text((temp_x + 30, temp_y + 130), condition_text, font=font_regular, fill=light_gray)
    draw.text((temp_x + 10, temp_y + 180), realfeel_text, font=font_small, fill=light_gray)
    draw.text((40, 520), location_text, font=font_regular, fill=light_gray)

    img.save(output_path)
    return output_path

async def get_weather_data(city):
    async with aiohttp.ClientSession() as session:
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geocode_data = await fetch_data(session, geocode_url)
        if not geocode_data or "results" not in geocode_data or not geocode_data["results"]:
            return None
        result = geocode_data["results"][0]
        lat, lon = result["latitude"], result["longitude"]
        country_code = result.get("country_code", "").upper()
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,weathercode,"
            f"wind_speed_10m,wind_direction_10m&"
            f"hourly=temperature_2m,apparent_temperature,relative_humidity_2m,weathercode,"
            f"precipitation_probability&"
            f"daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,weathercode&"
            f"timezone=auto"
        )
        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={lat}&longitude={lon}&"
            f"hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone&"
            f"timezone=auto"
        )
        weather_data, aqi_data = await asyncio.gather(
            fetch_data(session, weather_url),
            fetch_data(session, aqi_url)
        )
        if not weather_data or not aqi_data:
            return None
        current = weather_data["current"]
        hourly = weather_data["hourly"]
        daily = weather_data["daily"]
        aqi = aqi_data["hourly"]
        weather_code = {
            0: "Clear", 1: "Scattered Clouds", 2: "Scattered Clouds", 3: "Overcast Clouds",
            45: "Fog", 48: "Haze", 51: "Light Drizzle", 53: "Drizzle",
            55: "Heavy Drizzle", 61: "Light Rain", 63: "Moderate Rain", 65: "Heavy Rain",
            66: "Freezing Rain", 67: "Heavy Freezing Rain", 71: "Light Snow",
            73: "Snow", 75: "Heavy Snow", 77: "Snow Grains", 80: "Showers",
            81: "Heavy Showers", 82: "Violent Showers", 95: "Thunderstorm",
            96: "Thunderstorm", 99: "Heavy Thunderstorm"
        }
        hourly_data = [
            (time.split("T")[1][:5], temp, weather_code.get(code, "Unknown"))
            for time, temp, code in zip(hourly["time"][:12], hourly["temperature_2m"][:12], hourly["weathercode"][:12])
        ]
        hourly_strings = []
        for time, temp, weather in hourly_data:
            hour = int(time[:2])
            time_format = f"{hour % 12 or 12} {'AM' if hour < 12 else 'PM'}"
            hourly_strings.append(f"{time_format}: {temp}°C {weather}")
        
        current_date = datetime.now()
        daily_strings = []
        for i in range(7):
            day_date = (current_date + timedelta(days=i)).strftime('%a, %b %d')
            min_temp = daily["temperature_2m_min"][i]
            max_temp = daily["temperature_2m_max"][i]
            weather = weather_code.get(daily["weathercode"][i], "Unknown")
            daily_strings.append(f"{day_date}: {min_temp} / {max_temp}°C {weather}")
        
        aqi_level = "Good" if aqi["pm2_5"][0] <= 12 else "Fair" if aqi["pm2_5"][0] <= 35 else "Moderate" if aqi["pm2_5"][0] <= 55 else "Poor"
        
        try:
            timezone = get_timezone_from_coordinates(lat, lon)
            local_time = datetime.now(timezone)
            current_time = local_time.strftime("%I:%M %p")
        except Exception as e:
            LOGGER.error(f"Timezone conversion failed: {str(e)}")
            current_time = datetime.now().strftime("%I:%M %p")
            
        return {
            "current": {
                "temp": current["temperature_2m"],
                "feels_like": current["apparent_temperature"],
                "humidity": current["relative_humidity_2m"],
                "wind_speed": current["wind_speed_10m"],
                "wind_dir": current["wind_direction_10m"],
                "weather": weather_code.get(current["weathercode"], "Unknown"),
                "sunrise": daily["sunrise"][0].split("T")[1][:5] + " AM",
                "sunset": daily["sunset"][0].split("T")[1][:5] + " PM",
                "time": current_time
            },
            "hourly": hourly_strings,
            "daily": daily_strings,
            "aqi": {
                "pm25": aqi["pm2_5"][0],
                "pm10": aqi["pm10"][0],
                "co": aqi["carbon_monoxide"][0],
                "no2": aqi["nitrogen_dioxide"][0],
                "o3": aqi["ozone"][0],
                "level": aqi_level
            },
            "city": city.capitalize(),
            "country": get_country_name(country_code),
            "country_code": country_code,
            "lat": lat,
            "lon": lon
        }

def setup_weather_handler(app: Client):
    @app.on_message(filters.command(["wth"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def start(client, message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        
        parts = message.text.split()
        if len(parts) < 2 or not parts[1]:
            await client.send_message(message.chat.id, "**Please provide a city name. Example: `/wth Faridpur`**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            return
        
        city = parts[1].lower()
        loading_msg = await client.send_message(message.chat.id, "**Processing Weather Results**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        
        try:
            data = await get_weather_data(city)
            if not data:
                await client.edit_message_text(message.chat.id, loading_msg.id, f"🔍 Weather data unavailable for {city.capitalize()}. Please check the city name or try again later.", disable_web_page_preview=True)
                return
            
            current = data["current"]
            image_path = f"weather_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            create_weather_image(data, image_path)
            
            user_fullname = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
            keyboard = [
                [InlineKeyboardButton("🕒 12h Forecast", callback_data=f"12h_{user_id}"), InlineKeyboardButton("📅 7-Day Forecast", callback_data=f"7d_{user_id}")],
                [InlineKeyboardButton("🌬 Air Quality", callback_data=f"aqi_{user_id}"), InlineKeyboardButton("⚠️ Weather Alerts", callback_data=f"alert_{user_id}")],
                [InlineKeyboardButton("🔄 Refresh Current", callback_data=f"refresh_{user_id}"), InlineKeyboardButton("🗺 Maps & Radar", callback_data=f"map_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await client.delete_messages(message.chat.id, loading_msg.id)
            
            caption = (
                f"**🔍 Showing Weather for {data['city']}**\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"**🌍 Location:** {data['city']}, {data['country']}\n"
                f"**🕒 Time:** {current['time']}\n"
                f"**🌡 Temperature:** {current['temp']}°C (Feels like: {current['feels_like']}°C)\n"
                f"**💧 Humidity:** {current['humidity']}%\n"
                f"**🌬 Wind:** {current['wind_speed']} m/s from {current['wind_dir']}°\n"
                f"**🌅 Sunrise:** {current['sunrise']}\n"
                f"**🌆 Sunset:** {current['sunset']}\n"
                f"**🌤 Weather:** {current['weather']}\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"👁 Requested by: {user_fullname} (ID: {user_id})\n"
                f"👁 Please Use Below Buttons For Navigate ✅"
            )
            
            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_path,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            try:
                os.remove(image_path)
            except Exception as e:
                LOGGER.error(f"Failed to remove image {image_path}: {str(e)}")
                
        except Exception as e:
            LOGGER.error(f"Weather handler error: {str(e)}")
            await client.edit_message_text(message.chat.id, loading_msg.id, "****Sorry API Not Reachable ❌ **")
            await notify_admin(client, "/wth", e, message)

    @app.on_callback_query(filters.regex("^(12h|7d|aqi|alert|map|refresh|wth_menu)_(\d+)$"))
    async def button(client, callback_query):
        # Validate callback_data format
        match = re.match(r"^(12h|7d|aqi|alert|map|refresh|wth_menu)_(\d+)$", callback_query.data)
        if not match:
            LOGGER.error(f"Invalid callback_data format: {callback_query.data}")
            await client.answer_callback_query(
                callback_query.id,
                "Error: Invalid button data. Please try again.",
                show_alert=True
            )
            return
        
        action, original_user_id = match.groups()
        original_user_id = int(original_user_id)
        callback_user_id = callback_query.from_user.id if callback_query.from_user else None
        
        # Check if the user clicking the button is the same as the command initiator
        if callback_user_id != original_user_id:
            user_fullname = callback_query.message.caption.split("Requested by: ")[1].split(" (ID:")[0]
            await client.answer_callback_query(
                callback_query.id,
                f"Action Disallowed: This Button Only For {user_fullname}",
                show_alert=True
            )
            LOGGER.info(f"Unauthorized button access by user {callback_user_id} for {action} (intended for {original_user_id})")
            return
        
        city = callback_query.message.caption.split()[3].lower() if "for" in callback_query.message.caption else "dhaka"
        try:
            data = await get_weather_data(city)
            if not data:
                await client.edit_message_caption(callback_query.message.chat.id, callback_query.message.id, f"🔍 Weather data unavailable for {city.capitalize()}. Please try again later.")
                return
            current = data["current"]
            message_id = callback_query.message.id
            chat_id = callback_query.message.chat.id
            await client.answer_callback_query(callback_query.id, "Loading.....")
            
            user_fullname = f"{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}".strip()
            keyboard = (
                [[InlineKeyboardButton("🔙 Back", callback_data=f"wth_menu_{original_user_id}")]]
                if action in ["12h", "7d", "aqi", "alert", "map"]
                else [
                    [InlineKeyboardButton("🕒 12h Forecast", callback_data=f"12h_{original_user_id}"), InlineKeyboardButton("📅 7-Day Forecast", callback_data=f"7d_{original_user_id}")],
                    [InlineKeyboardButton("🌬 Air Quality", callback_data=f"aqi_{original_user_id}"), InlineKeyboardButton("⚠️ Weather Alerts", callback_data=f"alert_{original_user_id}")],
                    [InlineKeyboardButton("🔄 Refresh Current", callback_data=f"refresh_{original_user_id}"), InlineKeyboardButton("🗺 Maps & Radar", callback_data=f"map_{original_user_id}")]
                ]
            )
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if action == "12h":
                hourly_text = "\n".join(data['hourly'])
                message = (
                    f"🕒 12-Hour Forecast for {data['city']}\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"{hourly_text}\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Click Below Buttons To Navigate"
                )
                await client.edit_message_caption(chat_id, message_id, message, reply_markup=reply_markup)
            elif action == "7d":
                daily_text = "\n".join(data['daily'])
                message = (
                    f"📅 7-Day Forecast for {data['city']}\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"{daily_text}\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Click Below Buttons To Navigate"
                )
                await client.edit_message_caption(chat_id, message_id, message, reply_markup=reply_markup)
            elif action == "aqi":
                aqi = data["aqi"]
                message = (
                    f"🌬 Air Quality for {data['city']}\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"Overall AQI: {aqi['level']} 🟡\n"
                    f"CO: {aqi['co']} µg/m³\n"
                    f"NO2: {aqi['no2']} µg/m³\n"
                    f"O3: {aqi['o3']} µg/m³\n"
                    f"PM2.5: {aqi['pm25']} µg/m³\n"
                    f"PM10: {aqi['pm10']} µg/m³\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Click Below Buttons To Navigate"
                )
                await client.edit_message_caption(chat_id, message_id, message, reply_markup=reply_markup)
            elif action == "alert":
                message = (
                    f"🛡 Weather Alerts for {data['city']}\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"✅ No active weather alerts\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Click Below Buttons To Navigate"
                )
                await client.edit_message_caption(chat_id, message_id, message, reply_markup=reply_markup)
            elif action == "map":
                lat, lon = data["lat"], data["lon"]
                map_links = [
                    f"[🌡 Temperature Map](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=temperature&lat={lat}&lon={lon}&zoom=8)",
                    f"[☁️ Cloud Cover](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=clouds&lat={lat}&lon={lon}&zoom=8)",
                    f"[🌧 Precipitation](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=precipitation&lat={lat}&lon={lon}&zoom=8)",
                    f"[💨 Wind Speed](https://openweathermap.org/weormap?basemap=map&cities=true&layer=wind&lat={lat}&lon={lon}&zoom=8)",
                    f"[🌊 Pressure](https://openweathermap.org/weathermap?basemap=map&cities=true&layer=pressure&lat={lat}&lon={lon}&zoom=8)"
                ]
                maps_text = "\n".join(map_links)
                message = (
                    f"🗺 Weather Maps for {data['city']}\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"{maps_text}\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Click Below Buttons To Navigate"
                )
                await client.edit_message_caption(chat_id, message_id, message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            elif action == "refresh":
                new_data = await get_weather_data(city)
                if not new_data or (new_data and new_data["current"] == current):
                    await client.answer_callback_query(callback_query.id, "Data not changed.", show_alert=True)
                    return
                current = new_data["current"]
                new_image_path = f"weather_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                create_weather_image(new_data, new_image_path)
                
                caption = (
                    f"**🔍 Showing Weather for {new_data['city']}**\n"
                    f"**━━━━━━━━━━━━━━━━━**\n"
                    f"**🌍 Location:** {new_data['city']}, {new_data['country']}\n"
                    f"**🕒 Time:** {current['time']}\n"
                    f"**🌡 Temperature:** {current['temp']}°C (Feels like: {current['feels_like']}°C)\n"
                    f"**💧 Humidity:** {current['humidity']}%\n"
                    f"**🌬 Wind:** {current['wind_speed']} m/s from {current['wind_dir']}°\n"
                    f"**🌅 Sunrise:** {current['sunrise']}\n"
                    f"**🌆 Sunset:** {current['sunset']}\n"
                    f"**🌤 Weather:** {current['weather']}\n"
                    f"**━━━━━━━━━━━━━━━━━**\n"
                    f"👁 Requested by: {user_fullname} (ID: {original_user_id})\n"
                    f"👁 Please Use Below Buttons For Navigate ✅"
                )
                
                await client.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(media=new_image_path, caption=caption, parse_mode=ParseMode.MARKDOWN),
                    reply_markup=reply_markup
                )
                
                try:
                    os.remove(new_image_path)
                except Exception as e:
                    LOGGER.error(f"Failed to remove image {new_image_path}: {str(e)}")
            elif action == "wth_menu":
                caption = (
                    f"**🔍 Showing Weather for {data['city']}**\n"
                    f"**━━━━━━━━━━━━━━━━━**\n"
                    f"**🌍 Location:** {data['city']}, {data['country']}\n"
                    f"**🕒 Time:** {current['time']}\n"
                    f"**🌡 Temperature:** {current['temp']}°C (Feels like: {current['feels_like']}°C)\n"
                    f"**💧 Humidity:** {current['humidity']}%\n"
                    f"**🌬 Wind:** {current['wind_speed']} m/s from {current['wind_dir']}°\n"
                    f"**🌅 Sunrise:** {current['sunrise']}\n"
                    f"**🌆 Sunset:** {current['sunset']}\n"
                    f"**🌤 Weather:** {current['weather']}\n"
                    f"**━━━━━━━━━━━━━━━━━**\n"
                    f"👁 Requested by: {user_fullname} (ID: {original_user_id})\n"
                    f"👁 Please Use Below Buttons For Navigate ✅"
                )
                await client.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            LOGGER.error(f"Callback query error: {str(e)}")
            await client.edit_message_caption(chat_id, message_id, "**Sorry API Not Reachable ❌ **")
            await notify_admin(client, f"/wth callback {action}", e, callback_query.message)
