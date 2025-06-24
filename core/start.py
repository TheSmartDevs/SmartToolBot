#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode, ChatType
import asyncio
from config import UPDATE_CHANNEL_URL, COMMAND_PREFIX
from core import banned_users

def setup_start_handler(app: Client):
    @app.on_message(filters.command(["start"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def start_message(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘ Sorry You're Banned From Using Me ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        chat_id = message.chat.id

        # Animation messages
        animation_message = await client.send_message(chat_id, "<b>Starting Smart Tool ⚙️...</b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.4)
        await client.edit_message_text(chat_id, animation_message.id, "<b>Generating Session Keys Please Wait...</b>", parse_mode=ParseMode.HTML)
        await asyncio.sleep(0.4)
        await client.delete_messages(chat_id, animation_message.id)

        if message.chat.type == ChatType.PRIVATE:
            # Extract full name in private chat
            full_name = "User"
            if message.from_user:
                first_name = message.from_user.first_name or ""
                last_name = message.from_user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()

            # Private Chat Message
            response_text = (
                f"<b>Hi {full_name}! Welcome To This Bot</b>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                f"<b>Smart Tool ⚙️</b>: The ultimate toolkit on Telegram, offering education, AI, downloaders, temp mail, credit cards, and more. Simplify your tasks with ease!\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                "<b>Don't forget to <a href='{UPDATE_CHANNEL_URL}'>Join Here</a> for updates!</b>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL)
            )
        elif message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            # Default to group name if user is anonymous admin
            group_name = message.chat.title if message.chat.title else "this group"

            # Check if user data is available (not anonymous admin)
            if message.from_user:
                first_name = message.from_user.first_name or ""
                last_name = message.from_user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()

                # Personalized response for non-anonymous users
                response_text = (
                    f"<b>Hi {full_name}! Welcome To This Bot</b>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    f"<b>Smart Tool ⚙️</b>: The ultimate toolkit on Telegram, offering education, AI, downloaders, temp mail, credit cards, and more. Simplify your tasks with ease!\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<b>Don't forget to <a href='{UPDATE_CHANNEL_URL}'>Join Here</a> for updates!</b>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL)
                )
            else:
                # If user is an anonymous admin, use group name only
                response_text = (
                    f"<b>Hi! Welcome {group_name} To This Bot</b>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    f"<b>Smart Tool ⚙️</b>: The ultimate toolkit on Telegram, offering education, AI, downloaders, temp mail, credit cards, and more. Simplify your tasks with ease!\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<b>Don't forget to <a href='{UPDATE_CHANNEL_URL}'>Join Here</a> for updates!</b>".format(UPDATE_CHANNEL_URL=UPDATE_CHANNEL_URL)
                )

        # Send message with inline buttons
        await client.send_message(
            chat_id=message.chat.id,
            text=response_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Main Menu", callback_data="main_menu")],
                [InlineKeyboardButton("ℹ️ About Me", callback_data="about_me"),
                 InlineKeyboardButton("📄 Policy & Terms", callback_data="policy_terms")]
            ]),
            disable_web_page_preview=True,
        )
