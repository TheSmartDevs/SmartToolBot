# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import re
import os
import random
import aiohttp
import asyncio
import pycountry
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import BIN_KEY, COMMAND_PREFIX, CC_GEN_LIMIT, MULTI_CCGEN_LIMIT
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users

async def get_bin_info(bin, client, message):
    headers = {'x-api-key': BIN_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://data.handyapi.com/bin/{bin}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    LOGGER.error(f"API returned status code {response.status}")
                    raise Exception(f"API returned status code {response.status}")
    except Exception as e:
        LOGGER.error(f"Error fetching BIN info: {str(e)}")
        # Notify admins about the error
        asyncio.create_task(notify_admin(client, "/gen", e, message))
        return None

# Luhn Algorithm
def luhn_algorithm(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10 == 0

# Card number generation
def generate_credit_card(bin, amount, month=None, year=None, cvv=None):
    cards = []
    for _ in range(amount):
        while True:
            # Replace 'x' with random digits
            card_body = ''.join([str(random.randint(0, 9)) if char.lower() == 'x' else char for char in bin])
            remaining_digits = 15 - len(card_body)  # Calculate how many digits we need to generate, excluding check digit
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])

            # Calculate the Luhn check digit for the entire 16 digits
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)

            # Validate using Luhn algorithm
            if luhn_algorithm(card_number):
                # Expiry month and year
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)

                # CVV (3 digits)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(3)])

                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                print(f"Generated card: {card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

def parse_input(user_input):
    bin = None
    month = None
    year = None
    cvv = None
    amount = 10

    # Fixed Issue Of Parse Input From Now Bot Only Accepts Bin From 6-15 Digits To Give Best Experience @abirxdhackz and @ISmartDevs
    match = re.match(
        r"^(\d{6,15}[xX]{0,12})"                # BIN with optional x
        r"(?:[|:/](\d{2}))?"                    # Month (optional)
        r"(?:[|:/](\d{2,4}))?"                  # Year (optional)
        r"(?:[|:/](\d{3,4}))?"                  # CVV (optional)
        r"(?:\s+(\d{1,4}))?$",                  # Amount (optional)
        user_input.strip()
    )

    if match:
        bin, month, year, cvv, amount = match.groups()
        if bin and (len(bin) < 6 or len(bin) > 15):
            return None, None, None, None, None
        if cvv and (len(cvv) < 3 or len(cvv) > 4):
            return None, None, None, None, None
        if year and len(year) == 2:
            year = f"20{year}"
        amount = int(amount) if amount else 10
    else:
        return None, None, None, None, None

    return bin, month, year, cvv, amount

def generate_custom_cards(bin, amount, month=None, year=None, cvv=None):
    cards = []
    for _ in range(amount):
        while True:
            card_body = bin.replace('x', '')  # Ensure BIN does not contain 'x' characters
            remaining_digits = 15 - len(card_body)  # Calculate how many digits we need to generate, excluding check digit
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])

            # Calculate the Luhn check digit for the entire 16 digits
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)

            # Validate using Luhn algorithm
            if luhn_algorithm(card_number):
                # Expiry month and year
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)

                # CVV (3 digits)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(3)])

                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                print(f"Generated card: {card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

# Luhn check digit calculation
def calculate_luhn_check_digit(card_number):
    """Calculates the Luhn check digit to complete the card number to 16 digits."""
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]  # Odd digits (starting from the last one)
    even_digits = digits[-2::-2]  # Even digits

    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))  # Add the digits of the doubled number

    # Calculate the check digit to make the total sum a multiple of 10
    check_digit = (10 - (checksum % 10)) % 10
    return check_digit

def get_flag(country_code):
    # Get the country name and flag emoji
    country = pycountry.countries.get(alpha_2=country_code)
    if not country:
        raise ValueError("Invalid country code")

    country_name = country.name
    flag_emoji = chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))
    return country_name, flag_emoji

def get_country_code_from_name(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except LookupError:
        raise ValueError("Invalid country name")

def setup_gen_handler(app: Client):
    @app.on_message(filters.command(["gen"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def generate_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        user_input = message.text.split(maxsplit=1)
        if len(user_input) == 1:
            await client.send_message(message.chat.id, "**Provide a valid BIN❌**")
            return

        user_input = user_input[1]
        bin, month, year, cvv, amount = parse_input(user_input)

        if not bin or len(bin) < 6 or len(bin) > 15:
            print(f"Invalid BIN length: {bin}")
            await client.send_message(message.chat.id, "**Sorry Bin Must Be 6-15 Digits ❌**")
            return

        if cvv is not None and (len(cvv) < 3 or len(cvv) > 4):
            await client.send_message(message.chat.id, "**Invalid CVV format. CVV must be 3 or 4 digits ❌**")
            return

        if amount > CC_GEN_LIMIT:
            await client.send_message(message.chat.id, "**You can only generate up to 2000 credit cards ❌**")
            return

        # Fetch BIN info
        bin_info = await get_bin_info(bin[:6], client, message)
        if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
            await client.send_message(message.chat.id, "**❌Sorry Bro Invalid Bin Provided**")
            return

        bank = bin_info.get("Issuer")
        country_name = bin_info["Country"].get("Name", "Unknown")
        card_type = bin_info.get("Type", "Unknown")
        card_scheme = bin_info.get("Scheme", "Unknown")
        bank_text = bank.upper() if bank else "Unknown"

        country_code = bin_info["Country"]["A2"]  # Use "A2" instead of "Code"
        country_name, flag_emoji = get_flag(country_code)
        bin_info_text = f"**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {card_scheme.upper()} - {card_type.upper()}"

        # Notify user that the bot is generating cards
        progress_message = await client.send_message(message.chat.id, "**Generating Credit Cards...**")
        print("Generating Credit Cards...")

        # Generate credit cards
        cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)

        if amount <= 10:
            card_text = "\n".join([f"`{card}`" for card in cards])
            await progress_message.delete()
            response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n{bin_info_text}"
            callback_data = f"regenerate|{user_input.replace(' ', '_')}"

            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Re-Generate", callback_data=callback_data)]]
            )
            await client.send_message(message.chat.id, response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        else:
            # Save cards to a file if amount is greater than 10
            file_name = f"{bin} x {amount}.txt"
            try:
                with open(file_name, "w") as file:
                    file.write("\n".join(cards))

                await progress_message.delete()
                if message.from_user:
                    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                    user_link = f"[{user_full_name}](tg://user?id={message.from_user.id})"
                else:
                    group_name = message.chat.title or "this group"
                    group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
                    user_link = f"[{group_name}]({group_url})"

                caption = f"{amount} {card_scheme.upper()} {card_type.upper()} credit card numbers for BIN {bin}\n━━━━━━━━━━━━━━━━━━\n{bin_info_text}\n━━━━━━━━━━━━━━━━━━\nGenerated By: {user_link}"

                await client.send_document(message.chat.id, document=file_name, caption=caption, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await client.send_message(message.chat.id, "**Sorry Bro API Response Unavailable**")
                LOGGER.error(f"Error saving cards to file: {str(e)}")
                # Notify admins about the error
                await notify_admin(client, "/gen", e, message)
            finally:
                if os.path.exists(file_name):
                    os.remove(file_name)

    @app.on_callback_query(filters.regex(r"regenerate\|(.+)"))
    async def regenerate_callback(client: Client, callback_query):
        # Check if user is banned
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(callback_query.message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        original_input = callback_query.data.split('|', 1)[1]
        original_input = original_input.replace('_', ' ')
        bin, month, year, cvv, amount = parse_input(original_input)

        if cvv is not None and (len(cvv) < 3 or len(cvv) > 4):
            await callback_query.answer("Invalid CVV format. CVV must be 3 or 4 digits ❌", show_alert=True)
            return

        if amount > CC_GEN_LIMIT:
            await callback_query.answer("You can only generate up to 2000 credit cards ❌", show_alert=True)
            return

        # Fetch BIN info again
        bin_info = await get_bin_info(bin[:6], client, callback_query.message)
        if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
            await callback_query.answer("❌Sorry Bro Invalid Bin Provided", show_alert=True)
            return

        bank = bin_info.get("Issuer")
        country_name = bin_info["Country"].get("Name", "Unknown")
        card_type = bin_info.get("Type", "Unknown")
        card_scheme = bin_info.get("Scheme", "Unknown")
        bank_text = bank.upper() if bank else "Unknown"

        country_code = bin_info["Country"]["A2"]  # Use "A2" instead of "Code"
        country_name, flag_emoji = get_flag(country_code)

        # Generate new credit cards
        cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)

        card_text = "\n".join([f"`{card}`" for card in cards[:10]])
        bin_info_text = f"**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {card_scheme.upper()} - {card_type.upper()}"
        response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n{bin_info_text}"

        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Re-Generate", callback_data=f"regenerate|{original_input.replace(' ', '_')}")]]
        )

        await callback_query.message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)