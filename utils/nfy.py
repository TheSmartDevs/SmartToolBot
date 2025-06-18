import logging
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType, ParseMode
from config import OWNER_ID, DEVELOPER_USER_ID, UPDATE_CHANNEL_URL


async def notify_admin(client: Client, command: str, error: Exception, message: Message):
    try:
        user = message.from_user
        user_id = user.id
        chat_id = message.chat.id
        user_fullname = f"{user.first_name} {user.last_name or ''}".strip()

        # Determine ChatID field value
        if message.chat.type == ChatType.PRIVATE:
            chat_id_display = user_id
        else:
            chat_id_display = chat_id

        # Format current time and date
        now = datetime.now()
        formatted_time = now.strftime('%I:%M %p')
        formatted_date = now.strftime('%d-%m-%Y')

        # Formatted bug message
        error_message = (
            "**🔍 New Bug Found In Smart Tools 📋**\n"
            "**━━━━━━━━━━━━━━━━**\n"
            f"**• COMMAND:** `{command}`\n"
            f"**• ISSUE:** `{str(error)}`\n"
            f"**• USER'S NAME:** `{user_fullname}`\n"
            f"**• USERID:** `{user_id}`\n"
            f"**• ChatID:** `{chat_id_display}`\n"
            f"**• TIME:** `{formatted_time}`\n"
            f"**• DATE:** `{formatted_date}`\n"
            "**━━━━━━━━━━━━━━━━**\n"
            "**🔍 Always Fix Bug & Keep Bot Pro 📋**"
        )

        # Inline buttons
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("User's Profile", user_id=user_id),
                    InlineKeyboardButton("Developer", user_id=DEVELOPER_USER_ID)
                ],
                [
                    InlineKeyboardButton("Updates Channel", url=UPDATE_CHANNEL_URL)
                ]
            ]
        )

        # Send the message
        await client.send_message(
            chat_id=OWNER_ID,
            text=error_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logging.error(f"Error in notify_admin: {e}")
