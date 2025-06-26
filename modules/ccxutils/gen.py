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
from core import banned_users

def is_amex_bin(bin_str):
    """Check if the BIN is for an AMEX card (starts with 34 or 37)."""
    # Extract first 2 digits from BIN, handling 'x' characters
    clean_bin = bin_str.replace('x', '').replace('X', '')
    if len(clean_bin) >= 2:
        first_two = clean_bin[:2]
        return first_two in ['34', '37']
    return False

async def get_bin_info(bin, client, message):
    """Fetch BIN information from the API."""
    headers = {'x-api-key': BIN_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://data.handyapi.com/bin/{bin}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = f"API returned status code {response.status}"
                    print(error_msg)
                    await client.send_message(message.chat.id, f"**Error: {error_msg}**")
                    return None
    except Exception as e:
        error_msg = f"Error fetching BIN info: {str(e)}"
        print(error_msg)
        await client.send_message(message.chat.id, f"**Error: {error_msg}**")
        return None

# Luhn Algorithm
def luhn_algorithm(card_number):
    """Validate card number using Luhn algorithm."""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0

# Luhn check digit calculation
def calculate_luhn_check_digit(card_number):
    """Calculate the Luhn check digit for a card number."""
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]  # Odd digits (from last)
    even_digits = digits[-2::-2]  # Even digits

    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))  # Sum digits of doubled number

    check_digit = (10 - (checksum % 10)) % 10
    return check_digit

# Card number generation
def generate_credit_card(bin, amount, month=None, year=None, cvv=None):
    """Generate credit cards based on BIN with random digits for 'x'."""
    cards = []
    is_amex = is_amex_bin(bin)
    target_length = 14 if is_amex else 15  # 14 + 1 check digit = 15 for AMEX, 15 + 1 = 16 for others
    cvv_length = 4 if is_amex else 3
    
    for _ in range(amount):
        while True:
            # Replace 'x' with random digits
            card_body = ''.join([str(random.randint(0, 9)) if char.lower() == 'x' else char for char in bin])
            remaining_digits = target_length - len(card_body)  # Calculate digits needed, excluding check digit
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])

            # Calculate Luhn check digit
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)

            # Validate using Luhn algorithm
            if luhn_algorithm(card_number):
                # Expiry month and year
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)

                # CVV (4 digits for AMEX, 3 for others)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])

                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                print(f"Generated card: {card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

def parse_input(user_input):
    """Parse user input for BIN, month, year, CVV, and amount."""
    bin = None
    month = None
    year = None
    cvv = None
    amount = 10

    # Regex to handle BINs with 'x' up to 16 digits, or 6-15 digits without 'x'
    match = re.match(
        r"^(\d{6,16}[xX]{0,10}|\d{6,15})"  # BIN with optional 'x' or 6-15 digits
        r"(?:[|:/](\d{2}))?"               # Month (optional)
        r"(?:[|:/](\d{2,4}))?"             # Year (optional)
        r"(?:[|:/](\d{3,4}))?"             # CVV (optional)
        r"(?:\s+(\d{1,4}))?$",             # Amount (optional)
        user_input.strip()
    )

    if match:
        bin, month, year, cvv, amount = match.groups()
        # Validate BIN length
        if bin:
            has_x = 'x' in bin.lower()
            bin_length = len(bin)
            if has_x and bin_length > 16:
                return None, None, None, None, None
            if not has_x and (bin_length < 6 or bin_length > 15):
                return None, None, None, None, None
        
        # Validate CVV based on card type
        if cvv:
            is_amex = is_amex_bin(bin) if bin else False
            expected_cvv_length = 4 if is_amex else 3
            if len(cvv) != expected_cvv_length:
                return None, None, None, None, None
        
        if year and len(year) == 2:
            year = f"20{year}"
        amount = int(amount) if amount else 10
    else:
        return None, None, None, None, None

    return bin, month, year, cvv, amount

def generate_custom_cards(bin, amount, month=None, year=None, cvv=None):
    """Generate credit cards for BINs without 'x'."""
    cards = []
    is_amex = is_amex_bin(bin)
    target_length = 14 if is_amex else 15  # 14 + 1 check digit = 15 for AMEX, 15 + 1 = 16 for others
    cvv_length = 4 if is_amex else 3
    
    for _ in range(amount):
        while True:
            card_body = bin.replace('x', '').replace('X', '')  # Remove any 'x' characters
            remaining_digits = target_length - len(card_body)  # Calculate digits needed
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])

            # Calculate Luhn check digit
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)

            # Validate using Luhn algorithm
            if luhn_algorithm(card_number):
                # Expiry month and year
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)

                # CVV (4 digits for AMEX, 3 for others)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])

                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                print(f"Generated card: {card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

def get_flag(country_code):
    """Get country name and flag emoji from country code."""
    country = pycountry.countries.get(alpha_2=country_code)
    if not country:
        raise ValueError("Invalid country code")

    country_name = country.name
    flag_emoji = chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))
    return country_name, flag_emoji

def get_country_code_from_name(country_name):
    """Get country code from country name."""
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except LookupError:
        raise ValueError("Invalid country name")

def setup_gen_handler(app: Client):
    """Set up the /gen command handler for the bot."""
    @app.on_message(filters.command(["gen"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def generate_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘ Sorry You're Banned From Using Me ↯**")
            return

        user_input = message.text.split(maxsplit=1)
        if len(user_input) == 1:
            await client.send_message(message.chat.id, "**Provide a valid BIN ❌**")
            return

        user_input = user_input[1]
        bin, month, year, cvv, amount = parse_input(user_input)

        if not bin:
            print(f"Invalid BIN: {bin}")
            await client.send_message(message.chat.id, "**Sorry Bin Must Be 6-15 Digits or Up to 16 Digits with 'x' ❌**")
            return

        # Check CVV validity based on card type
        if cvv is not None:
            is_amex = is_amex_bin(bin)
            expected_cvv_length = 4 if is_amex else 3
            if len(cvv) != expected_cvv_length:
                cvv_type = "4 digits for AMEX" if is_amex else "3 digits for non-AMEX"
                await client.send_message(message.chat.id, f"**Invalid CVV format. CVV must be {cvv_type} ❌**")
                return

        if amount > CC_GEN_LIMIT:
            await client.send_message(message.chat.id, "**You can only generate up to 2000 credit cards ❌**")
            return

        # Fetch BIN info
        bin_info = await get_bin_info(bin[:6], client, message)
        if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
            return  # Error message already sent by get_bin_info

        bank = bin_info.get("Issuer")
        country_name = bin_info["Country"].get("Name", "Unknown")
        card_type = bin_info.get("Type", "Unknown")
        card_scheme = bin_info.get("Scheme", "Unknown")
        bank_text = bank.upper() if bank else "Unknown"

        country_code = bin_info["Country"]["A2"]
        country_name, flag_emoji = get_flag(country_code)
        bin_info_text = f"{card_scheme.upper()} - {card_type.upper()}"

        # Notify user that the bot is generating cards
        progress_message = await client.send_message(message.chat.id, "**Generating Credit Cards...**")
        print("Generating Credit Cards...")

        # Generate credit cards
        cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)

        if amount <= 10:
            card_text = "\n".join([f"`{card}`" for card in cards])
            await progress_message.delete()
            response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {bin_info_text}"
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
                caption = (
                    f"**🔍 Multiple CC Generate Successful 📋**\n"
                    f"**━━━━━━━━━━━━━━━━**\n"
                    f"**• BIN:** {bin}\n"
                    f"**• INFO:** {bin_info_text}\n"
                    f"**• BANK:** {bank_text}\n"
                    f"**• COUNTRY:** {country_name} {flag_emoji}\n"
                    f"**━━━━━━━━━━━━━━━━**\n"
                    f"**👁 Thanks For Using Our Tool ✅**"
                )

                await client.send_document(message.chat.id, document=file_name, caption=caption, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await client.send_message(message.chat.id, "**Sorry Bro API Response Unavailable**")
                print(f"Error saving cards to file: {str(e)}")
            finally:
                if os.path.exists(file_name):
                    os.remove(file_name)

    @app.on_callback_query(filters.regex(r"regenerate\|(.+)"))
    async def regenerate_callback(client: Client, callback_query):
        """Handle regenerate callback for credit card generation."""
        # Check if user is banned
        user_id = callback_query.from_user.id if callback_query.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(callback_query.message.chat.id, "**✘ Sorry You're Banned From Using Me ↯**")
            return

        original_input = callback_query.data.split('|', 1)[1]
        original_input = original_input.replace('_', ' ')
        bin, month, year, cvv, amount = parse_input(original_input)

        if not bin:
            await callback_query.answer("Sorry Bin Must Be 6-15 Digits or Up to 16 Digits with 'x' ❌", show_alert=True)
            return

        # Check CVV validity based on card type
        if cvv is not None:
            is_amex = is_amex_bin(bin)
            expected_cvv_length = 4 if is_amex else 3
            if len(cvv) != expected_cvv_length:
                cvv_type = "4 digits for AMEX" if is_amex else "3 digits for non-AMEX"
                await callback_query.answer(f"Invalid CVV format. CVV must be {cvv_type} ❌", show_alert=True)
                return

        if amount > CC_GEN_LIMIT:
            await callback_query.answer("You can only generate up to 2000 credit cards ❌", show_alert=True)
            return

        # Fetch BIN information again
        bin_info = await get_bin_info(bin[:6], client, callback_query.message)
        if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
            return  # Error message already sent by get_bin_info

        bank = bin_info.get("Issuer")
        country_name = bin_info["Country"].get("Name", "Unknown")
        card_type = bin_info.get("Type", "Unknown")
        card_scheme = bin_info.get("Scheme", "Unknown")
        bank_text = bank.upper() if bank else "Unknown"

        country_code = bin_info["Country"]["A2"]
        country_name, flag_emoji = get_flag(country_code)
        bin_info_text = f"{card_scheme.upper()} - {card_type.upper()}"

        # Generate new credit cards
        cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)

        card_text = "\n".join([f"`{card}`" for card in cards[:10]])
        response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {bin_info_text}"

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Re-Generate", callback_data=f"regenerate|{original_input.replace(' ', '_')}")]
        ])

        await callback_query.message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
