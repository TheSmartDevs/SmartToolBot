# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import re
import os
import time
from pyrogram import Client, filters, handlers
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import COMMAND_PREFIX, MAX_TXT_SIZE, UPDATE_CHANNEL_URL, BAN_REPLY
from core import banned_users
from utils import LOGGER, notify_admin

async def filter_emails(content):
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    emails = [line.split(':')[0].strip() for line in content if email_pattern.match(line.split(':')[0])]
    return emails

async def filter_email_pass(content):
    email_pass_pattern = re.compile(r'^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}):(.+)$')
    email_passes = []
    for line in content:
        match = email_pass_pattern.match(line)
        if match:
            email = match.group(1)
            password = match.group(2).split()[0]
            email_passes.append(f"{email}:{password}")
    return email_passes

async def handle_fmail_command(client, message: Message):
    start_time = time.time()
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        return

    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
        await client.send_message(message.chat.id, "**⚠️ Reply to a message with a text file❌**", parse_mode=ParseMode.MARKDOWN)
        return

    temp_msg = await client.send_message(message.chat.id, "**Fetching And Filtering Mails...✨**", parse_mode=ParseMode.MARKDOWN)
    
    file_path = await message.reply_to_message.download()
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_size_mb > MAX_TXT_SIZE:
        await temp_msg.delete()
        await client.send_message(message.chat.id, "**⚠️ File size exceeds the 15MB limit❌**", parse_mode=ParseMode.MARKDOWN)
        os.remove(file_path)
        return

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()

    emails = await filter_emails(content)
    if not emails:
        await temp_msg.delete()
        await client.send_message(message.chat.id, "**❌ No valid emails found in the file.**", parse_mode=ParseMode.MARKDOWN)
        os.remove(file_path)
        return

    if message.from_user:
        user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        user_profile_url = f"https://t.me/{message.from_user.username}" if message.from_user.username else None
        user_link = f'[{user_full_name}]({user_profile_url})' if user_profile_url else user_full_name
    else:
        group_name = message.chat.title or "this group"
        group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
        user_link = f'[{group_name}]({group_url})'

    time_taken = round(time.time() - start_time, 2)
    total_lines = len(content)
    total_mails = len(emails)

    caption = (
        f"**Smart Mail Extraction Complete ✅**\n"
        f"**━━━━━━━━━━━━━━━━━**\n"
        f"**⊗ Total Size:** `{file_size_mb:.2f} MB`\n"
        f"**⊗ Total Mails:** `{total_mails}`\n"
        f"**⊗ Total Lines:** `{total_lines}`\n"
        f"**⊗ Time Taken:** `{time_taken} seconds`\n"
        f"**━━━━━━━━━━━━━━━━━**\n"
        f"**Requested By {user_link}**"
    )

    button = InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])

    if len(emails) > 10:
        file_name = "ProcessedFile.txt"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write("\n".join(emails))
        await temp_msg.delete()
        await client.send_document(message.chat.id, file_name, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=button)
        os.remove(file_name)
    else:
        formatted_emails = '\n'.join(f'`{email}`' for email in emails)
        await temp_msg.delete()
        await client.send_message(message.chat.id, f"{caption}\n\n{formatted_emails}", parse_mode=ParseMode.MARKDOWN, reply_markup=button)
    
    os.remove(file_path)

async def handle_fpass_command(client, message: Message):
    start_time = time.time()
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
        return

    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
        await client.send_message(message.chat.id, "**⚠️ Reply to a message with a text file.**", parse_mode=ParseMode.MARKDOWN)
        return

    temp_msg = await client.send_message(message.chat.id, "**Filtering And Extracting Mail Pass...✨**", parse_mode=ParseMode.MARKDOWN)
    
    file_path = await message.reply_to_message.download()
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_size_mb > MAX_TXT_SIZE:
        await temp_msg.delete()
        await client.send_message(message.chat.id, "**⚠️ File size exceeds the 15MB limit❌**", parse_mode=ParseMode.MARKDOWN)
        os.remove(file_path)
        return

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()

    email_passes = await filter_email_pass(content)
    if not email_passes:
        await temp_msg.delete()
        await client.send_message(message.chat.id, "**❌ No Mail Pass Combo Found**", parse_mode=ParseMode.MARKDOWN)
        os.remove(file_path)
        return

    if message.from_user:
        user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        user_profile_url = f"https://t.me/{message.from_user.username}" if message.from_user.username else None
        user_link = f'[{user_full_name}]({user_profile_url})' if user_profile_url else user_full_name
    else:
        group_name = message.chat.title or "this group"
        group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
        user_link = f'[{group_name}]({group_url})'

    time_taken = round(time.time() - start_time, 2)
    total_lines = len(content)
    total_mails = len(email_passes)
    total_pass = len(email_passes)

    caption = (
        f"**Smart Mail-Pass Combo Process Complete ✅**\n"
        f"**━━━━━━━━━━━━━━━━━**\n"
        f"**⊗ Total Size:** `{file_size_mb:.2f} MB`\n"
        f"**⊗ Total Mails:** `{total_mails}`\n"
        f"**⊗ Total Pass:** `{total_pass}`\n"
        f"**⊗ Total Lines:** `{total_lines}`\n"
        f"**⊗ Time Taken:** `{time_taken} seconds`\n"
        f"**━━━━━━━━━━━━━━━━━**\n"
        f"**Requested By {user_link}**"
    )

    button = InlineKeyboardMarkup([[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]])

    if len(email_passes) > 10:
        file_name = "ProcessedFile.txt"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write("\n".join(email_passes))
        await temp_msg.delete()
        await client.send_document(message.chat.id, file_name, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=button)
        os.remove(file_name)
    else:
        formatted_email_passes = '\n'.join(f'`{email_pass}`' for email_pass in email_passes)
        await temp_msg.delete()
        await client.send_message(message.chat.id, f"{caption}\n\n{formatted_email_passes}", parse_mode=ParseMode.MARKDOWN, reply_markup=button)
    
    os.remove(file_path)

def setup_fmail_handlers(app: Client):
    app.add_handler(handlers.MessageHandler(handle_fmail_command, filters.command(["fmail"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
    app.add_handler(handlers.MessageHandler(handle_fpass_command, filters.command(["fpass"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))
