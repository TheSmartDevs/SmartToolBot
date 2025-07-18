import re
import os
import random
import aiohttp
import asyncio
import pycountry
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import BIN_KEY, COMMAND_PREFIX, CC_GEN_LIMIT, MULTI_CCGEN_LIMIT, BAN_REPLY
from core import banned_users
from utils import notify_admin, LOGGER

def is_amex_bin(bin_str):
    clean_bin = bin_str.replace('x', '').replace('X', '')
    if len(clean_bin) >= 2:
        return clean_bin[:2] in ['34', '37']
    return False

def extract_bin_from_text(text):
    patterns = [
        r'(?:BIN|bin)[:\s]*(\d{6,16}[xX]{0,10}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?)?)',
        r'(?:\.gen|/gen)\s+(\d{6,16}[xX]{0,10}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?)?)',
        r'(?:^|\s)(\d{6,16}[xX]{0,10}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?)?)(?:\s|$)',
        r'(\d{6,16}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?))',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^0-9xX|:/]', '', match)
            base_digits = clean_match.replace('x', '').replace('X', '').replace('|', '').replace(':', '').replace('/', '')
            if 6 <= len(base_digits) <= 16:
                LOGGER.info(f"Extracted BIN: {clean_match} from text using pattern: {pattern}")
                return clean_match
    return None

async def get_bin_info(bin, client, message):
    headers = {'x-api-key': BIN_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://data.handyapi.com/bin/{bin}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = f"API returned status code {response.status}"
                    LOGGER.error(error_msg)
                    await client.send_message(message.chat.id, f"**Error: {error_msg}**")
                    return None
    except Exception as e:
        error_msg = f"Error fetching BIN info: {str(e)}"
        LOGGER.error(error_msg)
        await client.send_message(message.chat.id, f"**Error: {error_msg}**")
        await notify_admin(client, "/gen", e, message)
        return None

def luhn_algorithm(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0

def calculate_luhn_check_digit(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return (10 - (checksum % 10)) % 10

def generate_credit_card(bin, amount, month=None, year=None, cvv=None):
    cards = []
    is_amex = is_amex_bin(bin)
    target_length = 14 if is_amex else 15
    cvv_length = 4 if is_amex else 3
    for _ in range(amount):
        while True:
            card_body = ''.join([str(random.randint(0, 9)) if char.lower() == 'x' else char for char in bin])
            remaining_digits = target_length - len(card_body)
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)
            if luhn_algorithm(card_number):
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])
                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

def parse_input(user_input):
    bin = None
    month = None
    year = None
    cvv = None
    amount = 10
    match = re.match(
        r"^(\d{6,16}[xX]{0,10}|\d{6,15})"
        r"(?:[|:/](\d{2}))?"
        r"(?:[|:/](\d{2,4}))?"
        r"(?:[|:/]([0-9]{3,4}|xxx|rnd)?)?"
        r"(?:\s+(\d{1,4}))?$",
        user_input.strip(), re.IGNORECASE
    )
    if match:
        bin, month, year, cvv, amount = match.groups()
        if bin:
            has_x = 'x' in bin.lower()
            bin_length = len(bin)
            if has_x and bin_length > 16:
                return None, None, None, None, None
            if not has_x and (bin_length < 6 or bin_length > 15):
                return None, None, None, None, None
        if cvv and cvv.lower() not in ['xxx', 'rnd']:
            is_amex = is_amex_bin(bin) if bin else False
            expected_cvv_length = 4 if is_amex else 3
            if len(cvv) != expected_cvv_length:
                return None, None, None, None, None
        if cvv and cvv.lower() in ['xxx', 'rnd'] or cvv is None:
            cvv = None
        if year and len(year) == 2:
            year = f"20{year}"
        amount = int(amount) if amount else 10
    return bin, month, year, cvv, amount

def generate_custom_cards(bin, amount, month=None, year=None, cvv=None):
    cards = []
    is_amex = is_amex_bin(bin)
    target_length = 14 if is_amex else 15
    cvv_length = 4 if is_amex else 3
    for _ in range(amount):
        while True:
            card_body = bin.replace('x', '').replace('X', '')
            remaining_digits = target_length - len(card_body)
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)
            if luhn_algorithm(card_number):
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])
                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

def get_flag(country_code, client=None, message=None):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if not country:
            raise ValueError("Invalid country code")
        country_name = country.name
        flag_emoji = chr(0x1F1E6 + ord(country_code[0]) - ord('A')) + chr(0x1F1E6 + ord(country_code[1]) - ord('A'))
        return country_name, flag_emoji
    except Exception as e:
        error_msg = f"Error in get_flag: {str(e)}"
        LOGGER.error(error_msg)
        if client and message:
            asyncio.create_task(notify_admin(client, "/gen", e, message))
        raise

def get_country_code_from_name(country_name, client=None, message=None):
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except Exception as e:
        error_msg = f"Error in get_country_code_from_name: {str(e)}"
        LOGGER.error(error_msg)
        if client and message:
            asyncio.create_task(notify_admin(client, "/gen", e, message))
        raise

def setup_gen_handler(app: Client):
    @app.on_message(filters.command(["gen"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def generate_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += f" {message.from_user.last_name}"

        if message.reply_to_message and message.reply_to_message.text:
            user_input = message.reply_to_message.text
            extracted_bin = extract_bin_from_text(user_input)
            if extracted_bin:
                user_input = extracted_bin
                LOGGER.info(f"Using extracted BIN from reply text: {extracted_bin}")
            else:
                user_input = message.reply_to_message.text
        elif message.reply_to_message and message.reply_to_message.caption:
            user_input = message.reply_to_message.caption
            extracted_bin = extract_bin_from_text(user_input)
            if extracted_bin:
                user_input = extracted_bin
                LOGGER.info(f"Using extracted BIN from reply caption: {extracted_bin}")
            else:
                user_input = message.reply_to_message.caption
        else:
            user_input = message.text.split(maxsplit=1)
            if len(user_input) == 1:
                await client.send_message(message.chat.id, "**Provide a valid BIN or reply to a message with a valid BIN ❌**")
                return
            user_input = user_input[1]

        bin, month, year, cvv, amount = parse_input(user_input)
        if not bin:
            LOGGER.error(f"Invalid BIN: {user_input}")
            await client.send_message(message.chat.id, "**Sorry Bin Must Be 6-15 Digits or Up to 16 Digits with 'x' ❌**")
            return
        if cvv is not None:
            is_amex = is_amex_bin(bin)
            expected_cvv_length = 4 if is_amex else 3
            if len(cvv) != expected_cvv_length:
                cvv_type = "4 digits for AMEX" if is_amex else "3 digits for non-AMEX"
                await client.send_message(message.chat.id, f"**Invalid CVV format. CVV must be {cvv_type} ❌**")
                return
        if amount > CC_GEN_LIMIT:
            await client.send_message(message.chat.id, f"**You can only generate up to {CC_GEN_LIMIT} credit cards ❌**")
            return

        bin_info = await get_bin_info(bin[:6], client, message)
        if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
            return

        bank = bin_info.get("Issuer")
        country_name = bin_info["Country"].get("Name", "Unknown")
        card_type = bin_info.get("Type", "Unknown")
        card_scheme = bin_info.get("Scheme", "Unknown")
        bank_text = bank.upper() if bank else "Unknown"
        country_code = bin_info["Country"]["A2"]
        country_name, flag_emoji = get_flag(country_code, client, message)
        bin_info_text = f"{card_scheme.upper()} - {card_type.upper()}"

        progress_message = await client.send_message(message.chat.id, "**Generating Credit Cards...**")
        LOGGER.info("Generating Credit Cards...")
        cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)

        if amount <= 10:
            card_text = "\n".join([f"`{card}`" for card in cards])
            await progress_message.delete()
            response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {bin_info_text}"
            callback_data = f"regenerate|{user_input.replace(' ', '_')}|{user_id}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Re-Generate", callback_data=callback_data)]])
            await client.send_message(message.chat.id, response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        else:
            file_name = f"{bin} x {amount}.txt"
            try:
                with open(file_name, "w") as file:
                    file.write("\n".join(cards))
                await progress_message.delete()
                caption = f"**🔍 Multiple CC Generate Successful 📋**\n**━━━━━━━━━━━━━━━━**\n**• BIN:** {bin}\n**• INFO:** {bin_info_text}\n**• BANK:** {bank_text}\n**• COUNTRY:** {country_name} {flag_emoji}\n**━━━━━━━━━━━━━━━━**\n**👁 Thanks For Using Our Tool ✅**"
                await client.send_document(message.chat.id, document=file_name, caption=caption, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                await client.send_message(message.chat.id, "**Sorry Bro API Response Unavailable**")
                LOGGER.error(f"Error saving cards to file: {str(e)}")
                await notify_admin(client, "/gen", e, message)
            finally:
                if os.path.exists(file_name):
                    os.remove(file_name)

    @app.on_message(filters.reply & filters.regex(r'^(?:BIN|bin)[:\s]*(\d{6,16}[xX]{0,10}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?)?)|(?:\.gen|/gen)\s+(\d{6,16}[xX]{0,10}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?)?)|(?:^|\s)(\d{6,16}[xX]{0,10}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?)?)(?:\s|$)|(\d{6,16}(?:[|:/]\d{2}(?:[|:/]\d{2,4}(?:[|:/]\d{3,4})?)?))') & (filters.private | filters.group))
    async def auto_generate_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            return
        user_full_name = message.from_user.first_name
        if message.from_user.last_name:
            user_full_name += f" {message.from_user.last_name}"

        if message.reply_to_message:
            reply_text = None
            if message.reply_to_message.text:
                reply_text = message.reply_to_message.text
                LOGGER.info(f"Extracting from text message")
            elif message.reply_to_message.caption:
                reply_text = message.reply_to_message.caption
                LOGGER.info(f"Extracting from media caption")
            if reply_text:
                extracted_bin = extract_bin_from_text(reply_text)
            if extracted_bin:
                user_input = extracted_bin
                LOGGER.info(f"Auto-extracted BIN from reply: {extracted_bin}")
                bin, month, year, cvv, amount = parse_input(user_input)
                if not bin:
                    return
                if cvv is not None:
                    is_amex = is_amex_bin(bin)
                    expected_cvv_length = 4 if is_amex else 3
                    if len(cvv) != expected_cvv_length:
                        return
                if amount > CC_GEN_LIMIT:
                    return

                bin_info = await get_bin_info(bin[:6], client, message)
                if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
                    return

                bank = bin_info.get("Issuer")
                country_name = bin_info["Country"].get("Name", "Unknown")
                card_type = bin_info.get("Type", "Unknown")
                card_scheme = bin_info.get("Scheme", "Unknown")
                bank_text = bank.upper() if bank else "Unknown"
                country_code = bin_info["Country"]["A2"]
                country_name, flag_emoji = get_flag(country_code, client, message)
                bin_info_text = f"{card_scheme.upper()} - {card_type.upper()}"

                progress_message = await client.send_message(message.chat.id, "**Generating Credit Cards...**")
                LOGGER.info("Auto-generating Credit Cards...")
                cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)

                if amount <= 10:
                    card_text = "\n".join([f"`{card}`" for card in cards])
                    await progress_message.delete()
                    response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {bin_info_text}"
                    callback_data = f"regenerate|{user_input.replace(' ', '_')}|{user_id}"
                    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Re-Generate", callback_data=callback_data)]])
                    await client.send_message(message.chat.id, response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
                else:
                    file_name = f"{bin} x {amount}.txt"
                    try:
                        with open(file_name, "w") as file:
                            file.write("\n".join(cards))
                        await progress_message.delete()
                        caption = f"**🔍 Multiple CC Generate Successful 📋**\n**━━━━━━━━━━━━━━━━**\n**• BIN:** {bin}\n**• INFO:** {bin_info_text}\n**• BANK:** {bank_text}\n**• COUNTRY:** {country_name} {flag_emoji}\n**━━━━━━━━━━━━━━━━**\n**👁 Thanks For Using Our Tool ✅**"
                        await client.send_document(message.chat.id, document=file_name, caption=caption, parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        await client.send_message(message.chat.id, "**Sorry Bro API Response Unavailable**")
                        LOGGER.error(f"Error saving cards to file: {str(e)}")
                        await notify_admin(client, "/gen", e, message)
                    finally:
                        if os.path.exists(file_name):
                            os.remove(file_name)

    @app.on_callback_query(filters.regex(r"regenerate\|(.+)\|(\d+)"))
    async def regenerate_callback(client: Client, callback_query):
        user_id = callback_query.from_user.id if callback_query.from_user else None
        original_user_id = int(callback_query.data.split('|')[-1])
        user_full_name = callback_query.from_user.first_name
        if callback_query.from_user.last_name:
            user_full_name += f" {callback_query.from_user.last_name}"

        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(callback_query.message.chat.id, BAN_REPLY)
            return

        if user_id != original_user_id:
            original_user = await client.get_users(original_user_id)
            original_user_name = original_user.first_name
            if original_user.last_name:
                original_user_name += f" {original_user.last_name}"
            await callback_query.answer(f"Action Disallowed. This Button Only For {original_user_name}", show_alert=True)
            return

        original_input = callback_query.data.split('|', 2)[1].replace('_', ' ')
        bin, month, year, cvv, amount = parse_input(original_input)
        if not bin:
            await callback_query.answer("Sorry Bin Must Be 6-15 Digits or Up to 16 Digits with 'x' ❌", show_alert=True)
            return
        if cvv is not None:
            is_amex = is_amex_bin(bin)
            expected_cvv_length = 4 if is_amex else 3
            if len(cvv) != expected_cvv_length:
                cvv_type = "4 digits for AMEX" if is_amex else "3 digits for non-AMEX"
                await callback_query.answer(f"Invalid CVV format. CVV must be {cvv_type} ❌", show_alert=True)
                return
        if amount > CC_GEN_LIMIT:
            await callback_query.answer(f"You can only generate up to {CC_GEN_LIMIT} credit cards ❌", show_alert=True)
            return

        bin_info = await get_bin_info(bin[:6], client, callback_query.message)
        if not bin_info or bin_info.get("Status") != "SUCCESS" or not isinstance(bin_info.get("Country"), dict):
            return

        bank = bin_info.get("Issuer")
        country_name = bin_info["Country"].get("Name", "Unknown")
        card_type = bin_info.get("Type", "Unknown")
        card_scheme = bin_info.get("Scheme", "Unknown")
        bank_text = bank.upper() if bank else "Unknown"
        country_code = bin_info["Country"]["A2"]
        country_name, flag_emoji = get_flag(country_code, client, callback_query.message)
        bin_info_text = f"{card_scheme.upper()} - {card_type.upper()}"

        cards = generate_custom_cards(bin, amount, month, year, cvv) if 'x' in bin.lower() else generate_credit_card(bin, amount, month, year, cvv)
        card_text = "\n".join([f"`{card}`" for card in cards[:10]])
        response_text = f"**BIN ⇾ {bin}**\n**Amount ⇾ {amount}**\n\n{card_text}\n\n**Bank:** {bank_text}\n**Country:** {country_name} {flag_emoji}\n**BIN Info:** {bin_info_text}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Re-Generate", callback_data=f"regenerate|{original_input.replace(' ', '_')}|{user_id}")]])
        await callback_query.message.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
