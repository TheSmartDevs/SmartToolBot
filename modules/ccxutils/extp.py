# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import asyncio
import requests
import random
import pycountry
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BIN_KEY, COMMAND_PREFIX
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users

# Helper function to fetch BIN info
def get_bin_info(bin, client, message):
    headers = {'x-api-key': BIN_KEY}
    try:
        response = requests.get(f"https://data.handyapi.com/bin/{bin}", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            LOGGER.error(f"API returned status code {response.status_code}")
            raise Exception(f"API returned status code {response.status_code}")
    except Exception as e:
        LOGGER.error(f"Error fetching BIN info: {str(e)}")
        # Notify admins about the error
        asyncio.create_task(notify_admin(client, "/extp", e, message))
        return None

# Helper function to validate a number using Luhn's Algorithm
def luhn_algorithm(number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(number)
    checksum = 0
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0

# Helper function to generate valid extrapolated numbers using Luhn's Algorithm
def generate_extrapolated_numbers(bin, amount=5):
    extrapolated_numbers = set()
    while len(extrapolated_numbers) < amount:
        number = bin + ''.join(random.choices('0123456789', k=9))
        check_sum = 0
        reverse_digits = number[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 0:
                n = n * 2
                if n > 9:
                    n = n - 9
            check_sum += n
        last_digit = (10 - (check_sum % 10)) % 10
        final_number = number + str(last_digit)
        if luhn_algorithm(final_number):
            extrapolated_numbers.add(final_number)
    return list(extrapolated_numbers)

def get_flag_emoji(country_code):
    return chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))

def setup_extp_handler(app):
    @app.on_message(filters.command(["extp"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def extrapolate(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        command_parts = message.text.split()
        if len(command_parts) != 2 or not command_parts[1].isdigit() or len(command_parts[1]) != 6:
            await client.send_message(message.chat.id, "**❌Please provide a valid BIN**", parse_mode=ParseMode.MARKDOWN)
            return
        
        bin = command_parts[1]
        progress_message = await client.send_message(message.chat.id, "**Extrapolation In Progress...✨**", parse_mode=ParseMode.MARKDOWN)
        bin_info = get_bin_info(bin, client, message)
        if not bin_info or bin_info.get('Status') != 'SUCCESS':
            await progress_message.edit_text("**BIN Not Found In Database❌**", parse_mode=ParseMode.MARKDOWN)
            return
        
        extrapolated_numbers = generate_extrapolated_numbers(bin)
        formatted_numbers = [f"`{num[:random.randint(8, 12)] + 'x' * (len(num) - random.randint(8, 12))}`" for num in extrapolated_numbers]

        country_code = bin_info.get('Country', {}).get('A2', '')
        country_name = bin_info.get('Country', {}).get('Name', 'N/A')
        flag_emoji = get_flag_emoji(country_code) if country_code else ''
        
        result_message = (
            f"𝗘𝘅𝘁𝗿𝗮𝗽 ⇾ {bin}\n"
            f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {len(formatted_numbers)}\n\n"
            + "\n".join(formatted_numbers) + "\n\n"
            f"**𝗕𝗮𝗻𝗸:** {bin_info.get('Issuer', 'None')}\n"
            f"**𝗖𝗼𝘂𝗻𝘁𝗿𝘆:** {country_name} {flag_emoji}\n"
            f"**𝗕𝗜𝗡 𝗜𝗻𝗳𝗼:** {bin_info.get('CardTier', 'None')} - {bin_info.get('Type', 'None')} - {bin_info.get('Scheme', 'None')}"
        )

        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Re-Generate", callback_data=f"regenerate_{bin}")]]
        )

        await progress_message.delete()
        await client.send_message(message.chat.id, result_message, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

    @app.on_callback_query(filters.regex(r"^regenerate_\d{6}$"))
    async def regenerate_callback(client, callback_query):
        # Check if user is banned
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(callback_query.message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        bin = callback_query.data.split("_")[1]
        bin_info = get_bin_info(bin, client, callback_query.message)
        if not bin_info or bin_info.get('Status') != 'SUCCESS':
            await callback_query.message.edit_text("**❌Invalid BIN provided**", parse_mode=ParseMode.MARKDOWN)
            return

        extrapolated_numbers = generate_extrapolated_numbers(bin)
        formatted_numbers = [f"`{num[:random.randint(8, 12)] + 'x' * (len(num) - random.randint(8, 12))}`" for num in extrapolated_numbers]

        country_code = bin_info.get('Country', {}).get('A2', '')
        country_name = bin_info.get('Country', {}).get('Name', 'N/A')
        flag_emoji = get_flag_emoji(country_code) if country_code else ''
        
        regenerated_message = (
            f"𝗘𝘅𝘁𝗿𝗮𝗽 ⇾ {bin}\n"
            f"𝗔𝗺𝗼𝘂𝗻𝘁 ⇾ {len(formatted_numbers)}\n\n"
            + "\n".join(formatted_numbers) + "\n\n"
            f"**𝗕𝗮𝗻𝗸:** {bin_info.get('Issuer', 'None')}\n"
            f"**𝗖𝗼𝘂𝗻𝘁𝗿𝘆:** {country_name} {flag_emoji}\n"
            f"**𝗕𝗜𝗡 𝗜𝗻𝗳𝗼:** {bin_info.get('CardTier', 'None')} - {bin_info.get('Type', 'None')} - {bin_info.get('Scheme', 'None')}"
        )

        if callback_query.message.text != regenerated_message:
            await callback_query.message.edit_text(regenerated_message, parse_mode=ParseMode.MARKDOWN, reply_markup=callback_query.message.reply_markup)