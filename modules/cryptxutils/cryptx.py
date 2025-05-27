# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import COMMAND_PREFIX
from utils import LOGGER, notify_admin  # Import LOGGER and notify_admin from utils
from core import banned_users  # Check if user is banned

# Temporary in-memory storage
price_storage = {}

async def get_binance_conversion_rate(base_coin: str, target_coin: str) -> float:
    """
    Fetch the conversion rate from Binance API for the base coin to the target coin.
    """
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={base_coin.upper()}{target_coin.upper()}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                LOGGER.error("API request failed with status code %s", response.status)
                raise Exception("API request failed")
            data = await response.json()
            LOGGER.info("Successfully fetched conversion rate for %s to %s", base_coin, target_coin)
            return float(data["price"])  # Use the "price" key for the conversion rate

def setup_coin_handler(app: Client):
    @app.on_message(filters.command(["cx"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def coin_handler(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use /cx")
            return

        if message.chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return

        command = message.text.split()
        if len(command) < 4:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Please Provide Valid Format /cx `<amount>` `<base_coin>` `<target_coin>`**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning("Invalid command format: %s", message.text)
            return

        try:
            amount = float(command[1])  # The amount the user wants to convert
        except ValueError:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Please Provide a Valid Amount**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning("Invalid amount provided: %s", command[1])
            return
        
        base_coin = command[2].upper()  # The coin the user is converting from
        target_coin = command[3].upper()  # The coin the user is converting to

        loading_msg = await client.send_message(
            chat_id=message.chat.id,
            text="**💥 SmartTools Fetching Database✨**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            # Get the conversion rate (price of 1 unit of the base_coin in terms of target_coin) from Binance API
            conversion_rate = await get_binance_conversion_rate(base_coin, target_coin)

            # Calculate the total amount in target coin based on the specified amount
            total_converted = round(conversion_rate * amount, 6)

            # Store the conversion rate for potential refresh
            price_storage[message.chat.id] = {"conversion_rate": conversion_rate, "total_converted": total_converted}

            # Send the result back to the user
            await loading_msg.edit_text(
                f"💥 **Coin Conversion Result:**\n\n"
                f"✨ **Base Coin:** `{base_coin}`\n"
                f"💥 **Convert Amount:** `{amount}`\n"
                f"⚡️ **Total in {target_coin}:** `{total_converted}`\n\n"
                f"🙈 **Target Coin:** `{target_coin}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("💰 Refresh", callback_data=f"refresh${base_coin}${target_coin}${amount}${total_converted}"),
                            InlineKeyboardButton("🌐 Binance Convert", url=f"https://www.binance.com/en/convert/{base_coin}/{target_coin}")
                        ]
                    ]
                )
            )
            LOGGER.info("Coin conversion result sent for %s to %s: %s %s", base_coin, target_coin, total_converted, target_coin)
        except Exception as e:
            await loading_msg.edit_text(
                "**Sorry, the API is down for the converter**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error("Exception occurred: %s", e)
            # Notify admins about the error
            await notify_admin(client, "/cx", e, message)

    @app.on_callback_query(filters.regex(r"refresh\$(\w+)\$(\w+)\$(\d+\.\d+|\d+)\$(\d+\.\d+|\d+)"))
    async def refresh_callback(client: Client, callback_query: CallbackQuery):
        # Check if user is banned
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await callback_query.message.edit_text("**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Banned user {user_id} attempted to use refresh for {callback_query.data}")
            return

        _, base_coin, target_coin, amount, previous_total_converted = callback_query.data.split("$")
        amount = float(amount)
        previous_total_converted = float(previous_total_converted)

        try:
            # Get the updated conversion rate from Binance API
            current_conversion_rate = await get_binance_conversion_rate(base_coin, target_coin)
            total_converted = round(current_conversion_rate * amount, 6)

            previous_data = price_storage.get(callback_query.message.chat.id, None)
            if not previous_data:
                await callback_query.answer("No previous data found.", show_alert=True)
                LOGGER.info("No previous data found for refresh in chat %s", callback_query.message.chat.id)
                return

            previous_conversion_rate = previous_data["conversion_rate"]
            previous_total_converted = previous_data["total_converted"]

            if current_conversion_rate == previous_conversion_rate:
                await callback_query.answer("No Change Detected From Binance Database❌", show_alert=True)
                LOGGER.info("No change detected for %s to %s", base_coin, target_coin)
            else:
                change_percentage = ((current_conversion_rate - previous_conversion_rate) / previous_conversion_rate) * 100
                last_rate = current_conversion_rate

                price_storage[callback_query.message.chat.id] = {"conversion_rate": current_conversion_rate, "total_converted": total_converted}

                await callback_query.message.edit_text(
                    f"**💥 Coin Conversion Result:**\n\n"
                    f"✨ **Base Coin:** `{base_coin}`\n"
                    f"💥 **Convert Amount:** `{amount}`\n"
                    f"⚡️ **Total in {target_coin}:** `{total_converted}`\n\n"
                    f"🙈 **Target Coin:** `{target_coin}`\n\n"
                    f"↕️ **Change:** `{change_percentage:.2f}%`\n"
                    f"💰 **Last Rate:** `{last_rate}`",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("💰 Refresh", callback_data=f"refresh${base_coin}${target_coin}${amount}${total_converted}"),
                                InlineKeyboardButton("🌐 Binance Convert", url=f"https://www.binance.com/en/convert/{base_coin}/{target_coin}")
                            ]
                        ]
                    )
                )
                await callback_query.answer("Token Conversion Updated✨", show_alert=True)
                LOGGER.info("Price updated for %s to %s: %s %s", base_coin, target_coin, total_converted, target_coin)
        except Exception as e:
            await callback_query.message.edit_text(
                "**Sorry, the API is down for the converter**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error("Exception occurred during refresh: %s", e)
            # Notify admins about the error
            await notify_admin(client, "/cx refresh", e, callback_query.message)