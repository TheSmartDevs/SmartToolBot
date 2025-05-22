#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import requests
import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import COMMAND_PREFIX
from utils import get_weather_conditions, notify_admin  # Import notify_admin

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# A simple cache to store the last weather data for comparison
last_weather_data = {}

def get_weather(city_name):
    try:
        # 🌐 Get weather condition mappings
        weather_conditions = get_weather_conditions()

        # 💫 Fetch coordinates for the city
        location_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}"
        location_response = requests.get(location_url, timeout=10)
        location_response.raise_for_status()
        location_data = location_response.json()

        if location_data and "results" in location_data and location_data["results"]:
            lat = location_data["results"][0]["latitude"]
            lon = location_data["results"][0]["longitude"]

            # ⚡️ Fetch real-time weather info
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            weather_response = requests.get(weather_url, timeout=10)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            if "current_weather" in weather_data:
                current_weather = weather_data["current_weather"]
                temperature = current_weather["temperature"]
                feels_like = temperature  # Open-Meteo doesn't support "feels like"
                wind_speed = current_weather["windspeed"]
                weather_code = current_weather["weathercode"]

                # 🌟 Translate weather code to description
                weather_condition, weather_description = weather_conditions.get(weather_code, ("❓ Unknown", "Unknown description"))

                # 💥 Format the final weather report with buttons
                map_url = f"https://www.google.com/maps/search/{city_name.replace(' ', '+')}"
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Refresh", callback_data=f"refresh$weather_{city_name}"),
                     InlineKeyboardButton("🗺️ View Map", url=map_url)]
                ])

                weather_info = (
                    f"🌐 **Weather Report for:** `{city_name}`\n"
                    f"✨ **Temperature:** `{temperature}°C`\n"
                    f"⭐️ **Feels Like:** `{temperature}°C`\n"
                    f"🌬️ **Wind Speed:** `{wind_speed} m/s`\n"
                    f"💥 **Condition:** `{weather_condition}`\n"
                    f"👀 **Details:** `{weather_description}`"
                )

                # Check if data has changed, store the latest weather info in cache
                global last_weather_data
                if city_name in last_weather_data:
                    if last_weather_data[city_name] == weather_info:
                        return weather_info, keyboard, "No Change Detected From Database"

                # Update the cache with the new weather info
                last_weather_data[city_name] = weather_info

                return weather_info, keyboard, "Weather Info Refreshed!"
            else:
                logger.error("No current_weather data in API response")
                return "**💀 Sorry Bro Weather API Dead**", None, None
        else:
            logger.warning(f"No results found for city: {city_name}")
            return "**🚫 Sorry Bro The Region Not Supported**", None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching weather data for {city_name}: {e}")
        return "**💀 Sorry Bro Weather API Dead**", None, None
    except Exception as e:
        logger.error(f"Unexpected error fetching weather data for {city_name}: {e}")
        return "**💀 Sorry Bro Weather API Dead**", None, None

def setup_weather_handler(app):
    # Handler for the "/w" command to get weather info
    @app.on_message(filters.command(["w"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def weather(client, message):
        if len(message.command) < 2:
            await client.send_message(
                message.chat.id,
                "**Bro! Kindly Provide A City Name**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        city_name = ' '.join(message.command[1:])
        loading_message = await client.send_message(
            message.chat.id,
            "**Fetching Weather Data From Database**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            weather_info, keyboard, callback_message = get_weather(city_name)
            await client.edit_message_text(
                message.chat.id,
                loading_message.id,
                weather_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error in weather handler for {city_name}: {e}")
            error_msg = "**💀 Sorry Bro Weather API Dead**"
            await client.edit_message_text(
                message.chat.id,
                loading_message.id,
                error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
            # Notify admins of error
            await notify_admin(client, "/w", e, message)

    # Handler for "Refresh" button click (with a regex pattern)
    @app.on_callback_query(filters.regex(r"refresh\$weather_"))
    async def refresh_weather(client, callback_query):
        city_name = callback_query.data.split("_")[1]
        try:
            weather_info, keyboard, callback_message = get_weather(city_name)

            if callback_message == "No Change Detected From Database":
                # Show alert if no change in the data
                await client.answer_callback_query(
                    callback_query.id,
                    text="Sorry Bro Data Not Updated In API"
                )
            else:
                # Show success message if data has changed
                await client.answer_callback_query(
                    callback_query.id,
                    text="Bro Data Changed Successfully!"
                )

            await client.edit_message_text(
                callback_query.message.chat.id,
                callback_query.message.id,
                weather_info,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error in refresh_weather handler for {city_name}: {e}")
            error_msg = "**💀 Sorry Bro Weather API Dead**"
            await client.edit_message_text(
                callback_query.message.chat.id,
                callback_query.message.id,
                error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
            # Notify admins of error
            await notify_admin(client, "weather_refresh", e, callback_query.message)
