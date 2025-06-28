#Copyright @ISmartCoder
#Updates Channel: https://t.me/TheSmartDev
import re
import os
import time
from pyrogram import Client, filters, handlers
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import COMMAND_PREFIX, MAX_TXT_SIZE, UPDATE_CHANNEL_URL
from utils import notify_admin, LOGGER
from core import banned_users

async def filter_valid_cc(content):
    valid_cc_patterns = [
        re.compile(r'^(\d{16}\|\d{2}\|\d{2}\|\d{3})\|.*$'),
        re.compile(r'^(\d{16}\|\d{2}\|\d{2}\|\d{4})\|.*$'),
        re.compile(r'^(\d{16}\|\d{2}\|\d{4}\|\d{3})\|.*$'),
        re.compile(r'^(\d{16}\|\d{2}\|\d{4}\|\d{4})\|.*$'),
        re.compile(r'^(\d{13}\|\d{2}\|\d{2}\|\d{3})\|.*$'),
        re.compile(r'^(\d{13}\|\d{2}\|\d{2}\|\d{4})\|.*$'),
        re.compile(r'^(\d{13}\|\d{2}\|\d{4}\|\d{3})\|.*$'),
        re.compile(r'^(\d{13}\|\d{2}\|\d{4}\|\d{4})\|.*$'),
        re.compile(r'^(\d{19}\|\d{2}\|\d{2}\|\d{3})\|.*$'),
        re.compile(r'^(\d{19}\|\d{2}\|\d{2}\|\d{4})\|.*$'),
        re.compile(r'^(\d{19}\|\d{2}\|\d{4}\|\d{3})\|.*$'),
        re.compile(r'^(\d{19}\|\d{2}\|\d{4}\|\d{4})\|.*$'),
        re.compile(r'^(\d{16}\|\d{2}\|\d{2,4}\|\d{3,4})$'),
        re.compile(r'(\d{15,16})\|(\d{1,2})/(\d{2,4})\|(\d{3,4})\|'),
        re.compile(r'(\d{15,16})\s*(\d{2})\s*(\d{2,4})\s*(\d{3,4})'),
        re.compile(r'(\d{15,16})\|(\d{4})(\d{2})\|(\d{3,4})\|'),
        re.compile(r'(\d{15,16})\|(\d{3,4})\|(\d{4})(\d{2})\|'),
        re.compile(r'(\d{15,16})\|(\d{3,4})\|(\d{2})\|(\d{2})\|'),
        re.compile(r'(\d{15,16})\|(\d{2})\|(\d{2})\|(\d{3})\|'),
        re.compile(r'(\d{15,16})\s*(\d{1,2})\s*(\d{2})\s*(\d{3,4})'),
        re.compile(r'(\d{15,16})\|(\d{2})\|(\d{2})\|(\d{3,4})\|'),
        re.compile(r'(\d{15,16})\s*(\d{3,4})\s*(\d{1,2})\s*(\d{2,4})'),
        re.compile(r'(\d{13,19})\s+(\d{2}/\d{2,4})\s+(\d{3,4})')
    ]
    valid_ccs = []
    for line in content:
        stripped_line = line.strip()
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
                    valid_ccs.append(cc_details)
                    matched = True
                    break
                elif len(match.groups()) == 1:
                    cc_details = match.group(1)
                    parts = cc_details.split("|")
                    if len(parts) >= 3 and len(parts[2]) == 2:
                        parts[2] = "20" + parts[2]
                        cc_details = "|".join(parts)
                    valid_ccs.append(cc_details)
                    matched = True
                    break
        if not matched:
            continue
    return valid_ccs

async def handle_fcc_command(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(
            message.chat.id,
            "**✘Sorry You're Banned From Using Me↯**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        return

    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
        await client.send_message(
            message.chat.id,
            "**⚠️ Reply to a text file to filter CC details❌**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        return

    file_size_mb = message.reply_to_message.document.file_size / (1024 * 1024)
    if file_size_mb > MAX_TXT_SIZE:
        await client.send_message(
            message.chat.id,
            "**⚠️ File size exceeds the 15MB limit❌**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        return

    temp_msg = await client.send_message(
        message.chat.id,
        "**Filtering CCs, Please Wait...✨**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
        )
    )
    start_time = time.time()
    file_path = await message.reply_to_message.download()
    with open(file_path, 'r') as file:
        content = file.readlines()

    valid_ccs = await filter_valid_cc(content)
    end_time = time.time()
    time_taken = end_time - start_time

    if not valid_ccs:
        await temp_msg.delete()
        await client.send_message(
            message.chat.id,
            "**❌ No valid credit card details found in the file.**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        os.remove(file_path)
        return

    total_amount = len(valid_ccs)
    total_size = f"{os.path.getsize(file_path) / 1024:.2f} KB"
    total_lines = len(valid_ccs)

    if total_amount > 10:
        file_name = f"Filtered_CCs_{total_amount}.txt"
        with open(file_name, 'w') as f:
            f.write("\n".join(valid_ccs))
        caption = (
            f"**Smart CC Filtering → Successful  ✅**\n"
            f"**━━━━━━━━━━━━━━━━━**\n"
            f"**⊗ Total Amount:** {total_amount}\n"
            f"**⊗ Total Size:** {total_size}\n"
            f"**⊗ Total Lines:** {total_lines}\n"
            f"**━━━━━━━━━━━━━━━━━**\n"
            f"**Smart CC Filter → Activated  ✅**"
        )
        await temp_msg.delete()
        await client.send_document(
            message.chat.id,
            file_name,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        os.remove(file_name)
    else:
        formatted_ccs = "\n".join(f"`{cc}`" for cc in valid_ccs)
        response_message = (
            f"**Smart CC Filtering → Successful  ✅**\n"
            f"**━━━━━━━━━━━━━━━━━**\n"
            f"{formatted_ccs}\n"
            f"**━━━━━━━━━━━━━━━━━**\n"
            f"**Smart CC Filter → Activated  ✅**"
        )
        await temp_msg.delete()
        await client.send_message(
            message.chat.id,
            response_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )

    os.remove(file_path)

def setup_fcc_handler(app: Client):
    app.add_handler(
        handlers.MessageHandler(
            handle_fcc_command,
            filters.command(["fcc", "filter"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
