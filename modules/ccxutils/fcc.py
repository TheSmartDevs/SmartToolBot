# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import re
import os
import time
from pyrogram import Client, filters, handlers
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import COMMAND_PREFIX, MAX_TXT_SIZE
from utils import notify_admin, LOGGER  # Import notify_admin and LOGGER from utils
from core import banned_users

# Function to filter valid CC details from a file
async def filter_valid_cc(content):
    """Filter valid credit card details from the file content and return only CC number, expiration date, and CVV."""
    LOGGER.info("Filtering valid credit card details from the file content.")
    valid_cc_patterns = [
        re.compile(r'^(\d{16}\|\d{2}\|\d{2}\|\d{3})\|.*$'),  # 16 digits | 2 digits month | 2 digits year | 3 digits CVV
        re.compile(r'^(\d{16}\|\d{2}\|\d{2}\|\d{4})\|.*$'),  # 16 digits | 2 digits month | 2 digits year | 4 digits CVV
        re.compile(r'^(\d{16}\|\d{2}\|\d{4}\|\d{3})\|.*$'),  # 16 digits | 2 digits month | 4 digits year | 3 digits CVV
        re.compile(r'^(\d{16}\|\d{2}\|\d{4}\|\d{4})\|.*$'),  # 16 digits | 2 digits month | 4 digits year | 4 digits CVV
        re.compile(r'^(\d{13}\|\d{2}\|\d{2}\|\d{3})\|.*$'),  # 13 digits | 2 digits month | 2 digits year | 3 digits CVV
        re.compile(r'^(\d{13}\|\d{2}\|\d{2}\|\d{4})\|.*$'),  # 13 digits | 2 digits month | 2 digits year | 4 digits CVV
        re.compile(r'^(\d{13}\|\d{2}\|\d{4}\|\d{3})\|.*$'),  # 13 digits | 2 digits month | 4 digits year | 3 digits CVV
        re.compile(r'^(\d{13}\|\d{2}\|\d{4}\|\d{4})\|.*$'),  # 13 digits | 2 digits month | 4 digits year | 4 digits CVV
        re.compile(r'^(\d{19}\|\d{2}\|\d{2}\|\d{3})\|.*$'),  # 19 digits | 2 digits month | 2 digits year | 3 digits CVV
        re.compile(r'^(\d{19}\|\d{2}\|\d{2}\|\d{4})\|.*$'),  # 19 digits | 2 digits month | 2 digits year | 4 digits CVV
        re.compile(r'^(\d{19}\|\d{2}\|\d{4}\|\d{3})\|.*$'),  # 19 digits | 2 digits month | 4 digits year | 3 digits CVV
        re.compile(r'^(\d{19}\|\d{2}\|\d{4}\|\d{4})\|.*$'),  # 19 digits | 2 digits month | 4 digits year | 4 digits CVV
        re.compile(r'^(\d{16}\|\d{2}\|\d{2,4}\|\d{3,4})$'),  # 16 digits | 2 digits month | 2 or 4 digits year | 3 or 4 digits CVV
        re.compile(r'(\d{15,16})\|(\d{1,2})/(\d{2,4})\|(\d{3,4})\|'),    # cc|mm/yy|cvv|
        re.compile(r'(\d{15,16})\s*(\d{2})\s*(\d{2,4})\s*(\d{3,4})'),    # cc mm/yy cvv
        re.compile(r'(\d{15,16})\|(\d{4})(\d{2})\|(\d{3,4})\|'),          # cc|yyyymm|cvv|
        re.compile(r'(\d{15,16})\|(\d{3,4})\|(\d{4})(\d{2})\|'),          # cc|cvv|yyyymm|
        re.compile(r'(\d{15,16})\|(\d{3,4})\|(\d{2})\|(\d{2})\|'),        # cc|cvv|mm|yy|
        re.compile(r'(\d{15,16})\|(\d{2})\|(\d{2})\|(\d{3})\|'),          # cc|mm|yy|cvv
        re.compile(r'(\d{15,16})\s*(\d{1,2})\s*(\d{2})\s*(\d{3,4})'),     # cc mm yy cvv (spaces)
        re.compile(r'(\d{15,16})\|(\d{2})\|(\d{2})\|(\d{3,4})\|'),        # cc|mm|yy|cvv|additional fields
        re.compile(r'(\d{15,16})\s*(\d{3,4})\s*(\d{1,2})\s*(\d{2,4})'),   # cc cvv mm yy
        re.compile(r'(\d{13,19})\s+(\d{2}/\d{2,4})\s+(\d{3,4})')         # cc mm/yy cvv
    ]

    valid_ccs = []
    for line in content:
        stripped_line = line.strip()
        LOGGER.info(f"Processing line: {stripped_line}")
        matched = False
        for pattern in valid_cc_patterns:
            match = pattern.match(stripped_line)
            if match:
                if len(match.groups()) >= 4:
                    cc = match.group(1)
                    month = match.group(2)
                    year = match.group(3)
                    cvv = match.group(4)
                    if "/" in month or "/" in year:
                        month = month.replace("/", "|")
                        year = year.replace("/", "|")
                    if len(year) == 2:
                        year = "20" + year
                    cc_details = f"{cc}|{month}|{year}|{cvv}"
                    LOGGER.info(f"Matched line: {cc_details}")
                    valid_ccs.append(cc_details)
                    matched = True
                    break
                elif len(match.groups()) == 3:
                    cc = match.group(1)
                    exp_date = match.group(2)
                    cvv = match.group(3)
                    exp_date = exp_date.replace("/", "|")
                    if len(exp_date.split("|")[1]) == 2:
                        exp_date = exp_date.replace("|", "|20", 1)
                    cc_details = f"{cc}|{exp_date}|{cvv}"
                    LOGGER.info(f"Matched line: {cc_details}")
                    valid_ccs.append(cc_details)
                    matched = True
                    break
                elif len(match.groups()) == 1:
                    cc_details = match.group(1)
                    parts = cc_details.split("|")
                    if len(parts) >= 3 and len(parts[2]) == 2:
                        parts[2] = "20" + parts[2]
                        cc_details = "|".join(parts)
                    LOGGER.info(f"Matched line: {cc_details}")
                    valid_ccs.append(cc_details)
                    matched = True
                    break
        if not matched:
            LOGGER.info(f"No match for line: {stripped_line}")

    LOGGER.info(f"Found {len(valid_ccs)} valid credit card details.")
    return valid_ccs

# Command to filter credit card details from a file
async def handle_fcc_command(client, message: Message):
    # Check if user is banned
    user_id = message.from_user.id if message.from_user else None
    # FIX: Await the banned_users.find_one as it's an async call
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
        return

    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
        await client.send_message(message.chat.id, "<b>⚠️ Reply to a text file to filter CC details❌</b>", parse_mode=ParseMode.HTML)
        LOGGER.warning("No valid text file provided for filtering.")
        return

    file_size_mb = message.reply_to_message.document.file_size / (1024 * 1024)
    if file_size_mb > MAX_TXT_SIZE:
        await client.send_message(message.chat.id, "<b>⚠️ File size exceeds the 15MB limit❌</b>", parse_mode=ParseMode.HTML)
        LOGGER.warning("File size exceeds the 15MB limit.")
        return

    temp_msg = await client.send_message(message.chat.id, "<b> Filtering CCs, Please Wait...✨ </b>", parse_mode=ParseMode.HTML)
    start_time = time.time()
    file_path = await message.reply_to_message.download()
    LOGGER.info(f"Downloaded file to {file_path}")
    with open(file_path, 'r') as file:
        content = file.readlines()

    valid_ccs = await filter_valid_cc(content)
    end_time = time.time()
    time_taken = end_time - start_time

    if not valid_ccs:
        await temp_msg.delete()
        await client.send_message(message.chat.id, "<b>❌ No valid credit card details found in the file.</b>", parse_mode=ParseMode.HTML)
        LOGGER.info("No valid credit card details found in the file.")
        os.remove(file_path)
        return

    if message.from_user:
        user_full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        user_profile_url = f"https://t.me/{message.from_user.username}" if message.from_user.username else None
        user_link = f'<a href="{user_profile_url}">{user_full_name}</a>' if user_profile_url else user_full_name
    else:
        group_name = message.chat.title or "this group"
        group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
        user_link = f'<a href="{group_url}">{group_name}</a>'

    if len(valid_ccs) > 10:
        file_name = f"Filtered_CCs_{len(valid_ccs)}.txt"
        with open(file_name, 'w') as f:
            f.write("\n".join(valid_ccs))
        caption = (
            f"<b>Here are the filtered cards:</b>\n"
            f"<b>━━━━━━━━━━━━━━</b>\n"
            f"<b>Total cards found:</b> <code>{len(valid_ccs)}</code>\n"
            f"<b>Time taken to validate:</b> <code>{time_taken:.2f} seconds</code>\n"
            f"<b>━━━━━━━━━━━━━━</b>\n"
            f"<b>Filtered By:</b> {user_link}\n"
            f"<b>📝 Extra Info:</b> <code>Use responsibly</code>\n"
            f"<b>🔍 Verified:</b> <code>Yes</code>"
        )
        await temp_msg.delete()
        await client.send_document(message.chat.id, file_name, caption=caption, parse_mode=ParseMode.HTML)
        LOGGER.info(f"Filtered cards saved to {file_name} and sent to the chat.")
        os.remove(file_name)
    else:
        formatted_ccs = "\n".join(valid_ccs)
        response_message = (
            f"<b>Total cards found: {len(valid_ccs)}</b>\n"
            f"<b>Time taken to validate:</b> <code>{time_taken:.2f} seconds</code>\n\n"
            f"<code>{formatted_ccs}</code>\n\n"
            f"<b>Filtered By:</b> {user_link}\n"
            f"<b>📝 Extra Info:</b> <code>Use responsibly</code>\n"
            f"<b>🔍 Verified:</b> <code>Yes</code>"
        )
        await temp_msg.delete()
        await client.send_message(message.chat.id, response_message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        LOGGER.info("Filtered cards sent to the chat directly.")

    os.remove(file_path)
    LOGGER.info(f"Temporary file {file_path} removed.")

# Setup handler for FCC command
def setup_fcc_handler(app: Client):
    app.add_handler(handlers.MessageHandler(handle_fcc_command, filters.command(["fcc", "filter"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
