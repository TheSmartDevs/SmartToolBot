# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, MULTI_CCGEN_LIMIT
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users         # Check if user is banned

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
    check_digit = (10 - (checksum % 10)) % 10
    return check_digit

# Card number generation
def generate_credit_card(bin, amount, month=None, year=None, cvv=None):
    cards = []
    for _ in range(amount):
        while True:
            card_body = ''.join([str(random.randint(0, 9)) if char.lower() == 'x' else char for char in bin])
            remaining_digits = 15 - len(card_body)  # Calculate how many digits we need to generate, excluding check digit
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)
            if luhn_algorithm(card_number):
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(3)])
                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

def generate_custom_cards(bin, amount, month=None, year=None, cvv=None):
    cards = []
    for _ in range(amount):
        while True:
            card_body = bin.replace('x', '')  # Ensure BIN does not contain 'x' characters
            remaining_digits = 15 - len(card_body)  # Calculate how many digits we need to generate, excluding check digit
            card_body += ''.join([str(random.randint(0, 9)) for _ in range(remaining_digits)])
            check_digit = calculate_luhn_check_digit(card_body)
            card_number = card_body + str(check_digit)
            if luhn_algorithm(card_number):
                card_month = month or f"{random.randint(1, 12):02}"
                card_year = year or random.randint(2024, 2029)
                card_cvv = cvv or ''.join([str(random.randint(0, 9)) for _ in range(3)])
                cards.append(f"{card_number}|{card_month}|{card_year}|{card_cvv}")
                break
    return cards

# Setup handler for /mgn, /mgen, /multigen commands
def setup_multi_handler(app: Client):
    @app.on_message(filters.command(["mgn", "mgen", "multigen"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def multigen_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        # FIX: Await the banned_users.find_one as it's an async call
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        user_input = message.text.split()
        if len(user_input) < 3:
            await client.send_message(message.chat.id, "**Invalid Arguments ❌**\n**Use /mgen [BIN1] [BIN2] [BIN3]... [AMOUNT]**", parse_mode=ParseMode.MARKDOWN)
            return

        bins = user_input[1:-1]
        amount = int(user_input[-1])

        if amount > MULTI_CCGEN_LIMIT:
            await client.send_message(message.chat.id, "**You can only generate up to 2000 credit cards ❌**")
            return

        if any(len(bin) < 6 or len(bin) > 16 for bin in bins):
            await client.send_message(message.chat.id, "**Each BIN should be between 6 and 16 digits ❌**")
            return

        total_cards = []
        for bin in bins:
            total_cards.extend(generate_custom_cards(bin, amount, None, None, None) if 'x' in bin.lower() else generate_credit_card(bin, amount))

        valid_cards = [card for card in total_cards if luhn_algorithm(card.split('|')[0])]
        file_name = "Smart Tool ⚙️ Multigen.txt"
        try:
            with open(file_name, "w") as file:
                file.write("\n".join(valid_cards))
            if message.from_user:
                user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                user_link = f"[{user_full_name}](tg://user?id={message.from_user.id})"
            else:
                group_name = message.chat.title or "this group"
                group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
                user_link = f"[{group_name}]({group_url})"
            caption = (
                f"**🔥 Generated {len(valid_cards)} credit card numbers from all BIN 🔥**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🏦 **BINS:**\n" + "\n".join([f"• {bin}" for bin in bins]) + '\n'
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Generated By: {user_link}"
            )
            await client.send_document(message.chat.id, document=file_name, caption=caption, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await client.send_message(message.chat.id, "**Error generating cards ❌**", parse_mode=ParseMode.MARKDOWN)
            # Notify admins about the error
            await notify_admin(client, "/mgen", e, message)
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)
