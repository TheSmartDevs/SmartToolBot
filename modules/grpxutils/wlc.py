#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import random
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import DEVELOPER_USER_ID

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define the synchronous welcome handler
def setup_wlc_handler(app):
    @app.on_message(filters.new_chat_members)
    def auto_welcome(client, msg: Message):
        first = msg.from_user.first_name or 'N/A'
        last = msg.from_user.last_name or ''
        mention = msg.from_user.mention
        username = msg.from_user.username
        id = msg.from_user.id
        group_name = msg.chat.title

        caption = f'''
<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>♧ Welcome {mention} ♧</b>
<b>♧ To The Amazing {group_name} ♧</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>◇ User ID : </b><code>{id}</code>
<b>◇ Full Name : </b>{first} {last}
<b>◇ Username : </b>@{username}
<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
'''

        # Log the welcome message details
        logging.info(f"New member joined: {username} (ID: {id}) in {group_name}")

        # Send the welcome message with a photo and inline buttons
        client.send_photo(
            chat_id=msg.chat.id,
            photo="https://t.me/BotsDevZone/261",
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Me", url="https://t.me/ItsSmartToolBot?startgroup=new&admin=post_messages+delete_messages+edit_messages+pin_messages+change_info+invite_users+promote_members"),
                 InlineKeyboardButton("My Dev👨‍💻", user_id=DEVELOPER_USER_ID)]
            ])
        )

    @app.on_message(filters.left_chat_member)
    def farewell_message(client, msg: Message):
        username = msg.from_user.username or 'A user'

        farewell_text = f"<b> <code> {username} </code>  Very Sad To See You Leave From This Community ❤️‍🩹 Hope You Will Return Soon☺️</b>"

        # Log the farewell message details
        logging.info(f"Member left: {username}")

        client.send_message(
            chat_id=msg.chat.id,
            text=farewell_text
        )
