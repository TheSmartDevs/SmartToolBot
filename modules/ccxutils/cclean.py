import re
from datetime import datetime
import os
import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import COMMAND_PREFIX, MAX_TXT_SIZE, UPDATE_CHANNEL_URL

VALID_CARD_TYPES = {
    'Visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
    'Mastercard': r'^5[1-5][0-9]{14}$',
    'Amex': r'^3[47][0-9]{13}$',
    'Discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$'
}

def is_valid_card_number(card_number: str) -> bool:
    card_number = re.sub(r'[^0-9]', '', card_number)
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    total = 0
    reverse_digits = card_number[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n = (n // 10) + (n % 10)
        total += n
    if total % 10 != 0:
        return False
    return any(re.match(pattern, card_number) for pattern in VALID_CARD_TYPES.values())

def is_valid_expiration(exp_month: str, exp_year: str) -> bool:
    try:
        month = int(exp_month)
        year = int(exp_year)
        if year < 100:
            year += 2000
        if month < 1 or month > 12:
            return False
        current_date = datetime.now()
        card_exp_date = datetime(year, month, 1)
        return card_exp_date >= current_date
    except (ValueError, TypeError):
        return False

async def clean_credit_cards(client: Client, message: Message):
    start_time = time.time()
    processing_msg = None
    input_file = None
    output_file = None
    try:
        if not message.reply_to_message or not message.reply_to_message.document:
            await client.send_message(
                chat_id=message.chat.id,
                text="<b>❌ Please reply to a text file containing credit card details.</b>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
            )
            return
        file_size = message.reply_to_message.document.file_size
        if file_size > MAX_TXT_SIZE:
            await client.send_message(
                chat_id=message.chat.id,
                text="<b>Max Allowed File Size Is 15 MB</b>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
            )
            return
        processing_msg = await client.send_message(
            chat_id=message.chat.id,
            text="<b>Cleaning Up The Credit Cards</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
        )
        file_id = message.reply_to_message.document.file_id
        input_file = await client.download_media(
            file_id,
            file_name=f"SmartUtil_Cleaned"
        )
        if not os.path.exists(input_file):
            await client.send_message(
                chat_id=message.chat.id,
                text="<b>❌ Failed To Process The File</b>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
            )
            return
        valid_cards = []
        invalid_count = 0
        total_count = 0
        start_processing = time.time()
        with open(input_file, 'r', encoding='utf-8') as file:
            for line in file:
                total_count += 1
                line = line.strip()
                if not line:
                    continue
                parts = re.split(r'[|,;:\s]+', line)
                if len(parts) >= 3:
                    card_num = parts[0].strip()
                    exp_month = parts[1].strip()
                    exp_year = parts[2].strip()
                    if is_valid_card_number(card_num) and is_valid_expiration(exp_month, exp_year):
                        valid_cards.append(f"{card_num}|{exp_month}|{exp_year}\n")
                    else:
                        invalid_count += 1
        processing_time = time.time() - start_processing
        time_taken = time.time() - start_time
        output_file = f"cc_results_{len(valid_cards)}.txt"
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(valid_cards)
        caption = (
            f"<b>🔍 CC Cleaned Successfully 📋</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>• Total Cards:</b>  {total_count}\n"
            f"<b>• Valid Cards:</b>  {len(valid_cards)}\n"
            f"<b>• Invalid Cards:</b>  {invalid_count}\n"
            f"<b>• Time Taken:</b>  {time_taken:.2f}\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>🔍 Smart CC Cleaner → Activated  ✅</b>"
        )
        if processing_msg:
            try:
                await processing_msg.delete()
            except:
                pass
        if valid_cards:
            await client.send_document(
                chat_id=message.chat.id,
                document=output_file,
                caption=caption,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text="<b>❌ No valid credit cards found in the file.</b>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
            )
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>Sorry Bro Server Dead</b>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])
        )
        if processing_msg:
            try:
                await processing_msg.delete()
            except:
                pass
    finally:
        for file_path in [input_file, output_file]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

def setup_cln_handler(app: Client):
    @app.on_message(
        filters.command(["ccc", "clean"], prefixes=COMMAND_PREFIX) &
        (filters.group | filters.private)
    )
    async def cc_clean_handler(client: Client, message: Message):
        await clean_credit_cards(client, message)
