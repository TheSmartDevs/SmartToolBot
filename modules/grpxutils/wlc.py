# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import random
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import DEVELOPER_USER_ID
from utils import LOGGER

# Define the asynchronous welcome handler
def setup_wlc_handler(app):
    @app.on_message(filters.new_chat_members)
    async def auto_welcome(client, msg: Message):
        group_name = msg.chat.title
        added_by = msg.from_user.username or msg.from_user.first_name or 'Unknown' if msg.from_user else 'Unknown'

        # Iterate over new chat members to handle each one correctly
        for new_member in msg.new_chat_members:
            # Skip if the new member is a bot
            if new_member.is_bot:
                LOGGER.info(f"Bot {new_member.username or new_member.first_name} (ID: {new_member.id}) added to {group_name} by @{added_by}, skipping welcome.")
                continue

            # Extract user details
            first = new_member.first_name or 'N/A'
            last = new_member.last_name or ''
            full_name = f"{first} {last}".strip()
            username = new_member.username or 'N/A'
            user_id = new_member.id

            # Define the new welcome message
            caption = f'''
Wow, there's a new member! Yo <b>{full_name}</b> 👋 welcome to <b>{group_name}</b>! Don't forget to put your username so it's easy to tag. Don't forget to read the <b>rules</b> below.

<b>Rules:</b>
1. Polite and polite
2. Respect other users
3. NO CRINGE
'''

            # Log the welcome message details
            LOGGER.info(f"New user @{username} (ID: {user_id}) joined {group_name}, added by @{added_by}.")

            # Send the welcome message with a photo and inline button
            await client.send_photo(
                chat_id=msg.chat.id,
                photo="https://telegra.ph/file/36be820a8775f0bfc773e.jpg",
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("My Dev 👨‍💻", user_id=DEVELOPER_USER_ID)]
                ])
            )

    @app.on_message(filters.left_chat_member)
    async def farewell_message(client, msg: Message):
        username = msg.left_chat_member.username or msg.left_chat_member.first_name or 'A user'
        user_id = msg.left_chat_member.id

        # Define the farewell message
        farewell_text = f"<b>Nice Knowing You, @{username}!</b>"

        # Log the farewell message details
        LOGGER.info(f"User @{username} (ID: {user_id}) left {msg.chat.title}.")

        # Send the farewell message
        await client.send_message(
            chat_id=msg.chat.id,
            text=farewell_text,
            parse_mode=ParseMode.HTML
        )
