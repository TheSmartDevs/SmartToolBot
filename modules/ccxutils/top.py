# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
import time
from collections import Counter
from pyrogram import Client, filters, handlers
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import COMMAND_PREFIX, MAX_TXT_SIZE, UPDATE_CHANNEL_URL, BAN_REPLY
from utils import LOGGER
from core import banned_users

async def handle_topbin_command(client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(
            message.chat.id,
            BAN_REPLY,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        return

    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
        await client.send_message(
            message.chat.id,
            "**Reply to a text file containing credit cards to check top bins❌**",
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
            "**File size exceeds the 15MB limit❌**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        return

    temp_msg = await client.send_message(
        message.chat.id,
        "**Finding Top Bins...**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
        )
    )
    start_time = time.time()
    file_path = await message.reply_to_message.download()
    with open(file_path, 'r') as file:
        content = file.readlines()

    bin_counter = Counter([line.strip()[:6] for line in content if len(line.strip()) >= 6])
    top_bins = bin_counter.most_common(20)
    end_time = time.time()
    time_taken = end_time - start_time

    if not top_bins:
        await temp_msg.delete()
        await client.send_message(
            message.chat.id,
            "**❌ No BIN data found in the file.**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        os.remove(file_path)
        return

    response_message = (
        f"**Smart Top Bin Find → Successful  ✅**\n"
        f"**━━━━━━━━━━━━━━━━━**\n"
    )
    for bin, count in top_bins:
        response_message += f"**⊗ BIN:** `{bin}` - **Amount:** `{count}`\n"
    response_message += (
        f"**━━━━━━━━━━━━━━━━━**\n"
        f"**Smart Top Bin Finder → Activated  ✅**"
    )

    await temp_msg.delete()
    await client.send_message(
        message.chat.id,
        response_message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
        )
    )
    os.remove(file_path)

def setup_topbin_handler(app: Client):
    app.add_handler(
        handlers.MessageHandler(
            handle_topbin_command,
            filters.command(["topbin"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
