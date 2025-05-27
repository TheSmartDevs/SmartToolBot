# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import ipaddress
import httpx  # Import httpx for asynchronous HTTP requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode  # Import ParseMode for Markdown formatting
from config import IPINFO_API_TOKEN, LOCATIONIQ_API_KEY, COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users           # Import banned_users from core

async def fetch_ip_details(ip_address: str, client: httpx.AsyncClient) -> dict | None:
    try:
        ip = ipaddress.ip_address(ip_address)
        if not isinstance(ip, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            raise ValueError("Invalid IP address format")
        url = f"https://ipinfo.io/{ip_address}?token={IPINFO_API_TOKEN}"
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except (ValueError, httpx.RequestError) as e:
        LOGGER.error(f"Error fetching IP details for {ip_address}: {e}")
        await notify_admin(None, f"{COMMAND_PREFIX}loc", e, None)
        return None

def generate_static_map_url(latitude: str, longitude: str) -> str:
    try:
        lat = float(latitude)
        lon = float(longitude)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude values")
        return f"https://maps.locationiq.com/v3/staticmap?key={LOCATIONIQ_API_KEY}&center={lat},{lon}&zoom=16&size=600x600&markers=icon:large-blue-cutout%7C{lat},{lon}"
    except (ValueError, TypeError) as e:
        LOGGER.error(f"Error generating static map URL: {e}")
        raise

def setup_loc_handler(app: Client):
    @app.on_message(filters.command(["loc"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def get_ip(client: Client, message):
        # Banned user check
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        # Prepare user or group info for caption
        if message.from_user:
            user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
            user_info = f"[{user_full_name}](tg://user?id={message.from_user.id})"
        else:
            group_name = message.chat.title or "this group"
            group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
            user_info = f"[{group_name}]({group_url})"

        # Extract IP address from command
        parts = message.text.split(maxsplit=1)
        ip_address = parts[1].strip() if len(parts) > 1 else ""
        if not ip_address:
            await client.send_message(
                message.chat.id,
                "**❌ Please provide an IP address**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Send a temporary message
        temp_msg = await client.send_message(
            message.chat.id,
            "**🔍 Fetching IP details...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            async with httpx.AsyncClient() as http_client:
                details = await fetch_ip_details(ip_address, http_client)
                if not details or 'loc' not in details:
                    await client.edit_message_text(
                        message.chat.id,
                        temp_msg.id,
                        "**❌ Invalid IP address or no details available**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await notify_admin(client, f"{COMMAND_PREFIX}loc", Exception("Invalid IP address or no details returned"), message)
                    return

                # Generate static map URL
                try:
                    lat, lon = details['loc'].split(',')
                    map_url = generate_static_map_url(lat, lon)
                    response = await http_client.get(map_url)
                    response.raise_for_status()

                    # Prepare caption and inline keyboard
                    caption = (
                        f"**🍀 Location Found 🔎**\n\n"
                        f"🛰 **IP Address**: `{details['ip']}`\n"
                        f"🌎 **Country**: `{details.get('country', 'N/A')}`\n"
                        f"💠 **Region**: `{details.get('region', 'N/A')}`\n"
                        f"🏠 **City**: `{details.get('city', 'N/A')}`\n"
                        f"✉️ **Postal Code**: `{details.get('postal', 'N/A')}`\n"
                        f"🗼 **Internet Provider**: `{details.get('org', 'N/A')}`\n"
                        f"🕢 **Time Zone**: `{details.get('timezone', 'N/A')}`\n"
                        f"〽️ **Location**: `{details.get('loc', 'N/A')}`\n\n"
                        f"🔥 **Requested By**: {user_info}"
                    )
                    inline_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "✈️ Open in Google Maps",
                            url=f"https://www.google.com/maps/search/?api=1&query={lat}%2C{lon}"
                        )]
                    ])

                    # Send photo with location details
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=map_url,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=inline_keyboard
                    )

                    # Delete the temporary message
                    await client.delete_messages(message.chat.id, temp_msg.id)

                except (httpx.RequestError, ValueError) as e:
                    LOGGER.error(f"Static map API request failed for {ip_address}: {e}")
                    await notify_admin(client, f"{COMMAND_PREFIX}loc", e, message)
                    # Fallback to sending location directly
                    lat, lon = details['loc'].split(',')
                    caption = (
                        f"**🍀 Location Found (Fallback) 🔎**\n\n"
                        f"🛰 **IP Address**: `{details['ip']}`\n"
                        f"🌎 **Country**: `{details.get('country', 'N/A')}`\n"
                        f"💠 **Region**: `{details.get('region', 'N/A')}`\n"
                        f"🏠 **City**: `{details.get('city', 'N/A')}`\n"
                        f"✉️ **Postal Code**: `{details.get('postal', 'N/A')}`\n"
                        f"🗼 **Internet Provider**: `{details.get('org', 'N/A')}`\n"
                        f"🕢 **Time Zone**: `{details.get('timezone', 'N/A')}`\n"
                        f"〽️ **Location**: `{details.get('loc', 'N/A')}`\n\n"
                        f"🔥 **Requested By**: {user_info}"
                    )
                    await client.send_location(
                        chat_id=message.chat.id,
                        latitude=float(lat),
                        longitude=float(lon)
                    )
                    await client.send_message(
                        chat_id=message.chat.id,
                        text=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )

                    # Edit the temporary message to indicate fallback
                    await client.edit_message_text(
                        message.chat.id,
                        temp_msg.id,
                        "**⚠️ Static Map Unavailable, Showing Location Directly**",
                        parse_mode=ParseMode.MARKDOWN
                    )

        except Exception as e:
            LOGGER.error(f"Error processing location for {ip_address}: {e}")
            await notify_admin(client, f"{COMMAND_PREFIX}loc", e, message)
            await client.edit_message_text(
                message.chat.id,
                temp_msg.id,
                "**❌ Location API Error**",
                parse_mode=ParseMode.MARKDOWN
            )