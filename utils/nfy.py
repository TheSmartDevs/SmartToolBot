import logging
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, DEVELOPER_USER_ID

async def notify_admin(client: Client, command: str, error: Exception, message: Message):
    try:
        user = message.from_user
        user_fullname = f"{user.first_name} {user.last_name or ''}".strip()
        user_id = user.id
        error_message = (
            "**✘ Hey Sir, New Bug Found ↯**\n\n"
            f"**✘ Command: `{command}` ↯**\n"
            f"**✘ Issue: `{str(error)}` ↯**\n"
            f"**✘ User: `{user_fullname}` (ID: {user_id}) ↯**\n"
            f"**✘ Chat ID: `{message.chat.id}` ↯**\n"
            f"**✘ Time: `{message.date.strftime('%Y-%m-%d %H:%M:%S')}` ↯**"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✘ Dev ↯", user_id=DEVELOPER_USER_ID)]
            ]
        )
        try:
            await client.send_message(
                chat_id=OWNER_ID,
                text=error_message,
                reply_markup=keyboard
            )
        except Exception as admin_error:
            logging.error(f"Failed to notify admin {OWNER_ID}: {admin_error}")
    except Exception as e:
        logging.error(f"Error in notify_admin: {e}")
