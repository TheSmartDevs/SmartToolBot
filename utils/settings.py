#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode, ChatType
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
import os
import logging
from dotenv import load_dotenv
from config import COMMAND_PREFIX, ADMIN_IDS

# Logging Setup
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load The Environment Variables
load_dotenv()

# Temp Session For Fix The Bug 🚫 Hey Gay 🏳️‍🌈 This Is Not For You This Only For Males👱‍♂️
user_session = {}

# Helper Function To Remove Duplicate VARS
def detect_duplicate_keys():
    """Log a warning for duplicate keys in the .env file."""
    with open(".env") as f:
        lines = f.readlines()
        seen_keys = set()
        duplicates = set()
        for line in lines:
            if '=' in line:
                key = line.split("=", 1)[0].strip()
                if key in seen_keys:
                    duplicates.add(key)
                seen_keys.add(key)
        if duplicates:
            logger.warning(f"Duplicate keys found in .env: {', '.join(duplicates)}")

detect_duplicate_keys()

# Helper function to load environment variables
def load_env_vars():
    """Load all unique environment variables from the .env file."""
    with open(".env") as f:
        lines = f.readlines()
        variables = {}
        seen_keys = set()  # Use a set to track unique keys
        for line in lines:
            if '=' in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key not in seen_keys:  # Only add unique keys
                    variables[key] = value
                    seen_keys.add(key)
        return variables

def update_env_var(key, value):
    """Update a specific environment variable in the .env file."""
    env_vars = load_env_vars()
    env_vars[key] = value
    with open(".env", "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

config_keys = load_env_vars()
ITEMS_PER_PAGE = 10  

def build_menu(page=0):
    """Build the inline keyboard menu for settings."""
    keys = list(config_keys.keys())  # Extract unique keys from config_keys dictionary
    start, end = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
    current_keys = keys[start:end]

    rows = []
    for i in range(0, len(current_keys), 2):  # Two buttons per row
        buttons = [
            InlineKeyboardButton(current_keys[i], callback_data=f"settings_edit_{current_keys[i]}")
        ]
        if i + 1 < len(current_keys):  
            buttons.append(InlineKeyboardButton(current_keys[i + 1], callback_data=f"settings_edit_{current_keys[i + 1]}"))
        rows.append(buttons)

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"settings_page_{page - 1}"))
    if end < len(keys):
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"settings_page_{page + 1}"))
    if nav_buttons:
        if page == 0:  # For the first page, combine "Next" and "Close" buttons in the same row
            nav_buttons.append(InlineKeyboardButton("Close ❌", callback_data="settings_closesettings"))
            rows.append(nav_buttons)
        else:
            rows.append(nav_buttons)

    # Close button for other pages
    if page > 0:
        rows.append([InlineKeyboardButton("Close ❌", callback_data="settings_closesettings")])

    return InlineKeyboardMarkup(rows)

def setup_settings_handler(app: Client):
    """Setup the settings handler for the Pyrogram app."""
    async def debug_all(client: Client, message: Message):
        """Catch-all handler to debug all group chat messages."""
        thread_id = getattr(message, "message_thread_id", None)
        is_reply = message.reply_to_message_id is not None
        logger.debug(f"Catch-all: user {message.from_user.id}, chat {message.chat.id}, text='{message.text}', "
                    f"chat_type={message.chat.type}, is_reply={is_reply}, reply_to={message.reply_to_message_id}, thread={thread_id}")

    async def show_settings(client: Client, message: Message):
        """Show the settings menu."""
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            try:
                chat = await client.get_chat(message.chat.id)
                permissions = chat.permissions
                if not permissions.can_send_messages:
                    logger.error(f"Bot lacks permission to send messages in chat {message.chat.id}")
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**Sorry Bro This Group Is Restricted**"
                    )
                    return
                logger.debug(f"Chat {message.chat.id} permissions: can_send_messages={permissions.can_send_messages}, "
                            f"can_read_messages={getattr(permissions, 'can_read_messages', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to check permissions in chat {message.chat.id}: {str(e)}")
                return

        if message.from_user.id not in ADMIN_IDS:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘Kids Not Allowed To Do This↯**"
            )
            return

        logger.info(f"Showing settings menu for user {message.from_user.id} in chat {message.chat.id}")
        await client.send_message(
            chat_id=message.chat.id,
            text="**Select a change or edit 👇**",
            reply_markup=build_menu()
        )

    async def paginate_menu(client: Client, callback_query: CallbackQuery):
        """Handle pagination in the settings menu."""
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        page = int(callback_query.data.split("_")[2])
        logger.info(f"Paginating to page {page} for user {callback_query.from_user.id}")
        await callback_query.edit_message_reply_markup(reply_markup=build_menu(page))
        await callback_query.answer()

    async def edit_var(client: Client, callback_query: CallbackQuery):
        """Handle the selection of a variable to edit."""
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        var_name = callback_query.data.split("_", 2)[2]
        if var_name not in config_keys:
            await callback_query.answer("Invalid variable selected.", show_alert=True)
            return

        user_session[callback_query.from_user.id] = {
            "var": var_name,
            "chat_id": callback_query.message.chat.id
        }
        logger.info(f"User {callback_query.from_user.id} started editing {var_name} in chat {callback_query.message.chat.id}")
        await callback_query.edit_message_text(
            text=f"**Editing `{var_name}`. Please send the new value below.**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="settings_cancel_edit")]])
        )

    async def cancel_edit(client: Client, callback_query: CallbackQuery):
        """Cancel the editing process."""
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        user_session.pop(callback_query.from_user.id, None)
        logger.info(f"User {callback_query.from_user.id} cancelled editing")
        await callback_query.edit_message_text("**Variable Editing Cancelled**")
        await callback_query.answer()

    async def update_value(client: Client, message: Message):
        """Update the value of a selected variable."""
        thread_id = getattr(message, "message_thread_id", None)
        is_reply = message.reply_to_message_id is not None
        logger.debug(f"Received text message from user {message.from_user.id} in chat {message.chat.id}: '{message.text}', "
                    f"chat_type={message.chat.type}, is_reply={is_reply}, reply_to_message_id={message.reply_to_message_id}, thread={thread_id}")

        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            try:
                chat = await client.get_chat(message.chat.id)
                permissions = chat.permissions
                if not permissions.can_send_messages:
                    logger.error(f"Bot lacks permission to send messages in chat {message.chat.id}")
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="**Sorry Bro This Group Is Restricted!**"
                    )
                    return
                logger.debug(f"Chat {message.chat.id} permissions: can_send_messages={permissions.can_send_messages}, "
                            f"can_read_messages={getattr(permissions, 'can_read_messages', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to check permissions in chat {message.chat.id}: {str(e)}")
                return

        session = user_session.get(message.from_user.id)
        if not session:
            logger.debug(f"No session found for user {message.from_user.id} in chat {message.chat.id}")
            return

        logger.info(f"Processing value update for user {message.from_user.id} in chat {message.chat.id}, session: {session}")

        if message.from_user.id not in ADMIN_IDS:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘Kids Not Allowed To Do This↯**"
            )
            user_session.pop(message.from_user.id, None)
            logger.info(f"Non-admin {message.from_user.id} attempted to update value")
            return

        var, val = session["var"], message.text.strip()
        update_env_var(var, val)
        config_keys[var] = val
        logger.info(f"Sending success message for {var} update in chat {message.chat.id}")
        await client.send_message(
            chat_id=message.chat.id,
            text=f"**`{var}` Has Been Successfully Updated To `{val}`. ✅**"
        )
        user_session.pop(message.from_user.id, None)
        load_dotenv(override=True)
        logger.info(f"Successfully updated {var} to '{val}' for user {message.from_user.id} in chat {message.chat.id}")

    async def close_menu(client: Client, callback_query: CallbackQuery):
        """Close the settings menu."""
        if callback_query.from_user.id not in ADMIN_IDS:
            await callback_query.answer("✘Kids Not Allowed To Do This↯", show_alert=True)
            return

        logger.info(f"Closing settings menu for user {callback_query.from_user.id}")
        await callback_query.edit_message_text("**Settings Menu Closed Successfully ✅**")
        await callback_query.answer()

    # Register handlers with group=1
    app.add_handler(MessageHandler(debug_all, filters.chat([ChatType.GROUP, ChatType.SUPERGROUP])), group=1)
    app.add_handler(MessageHandler(show_settings, filters.command(["settings"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)), group=1)
    app.add_handler(MessageHandler(update_value, filters.text), group=1)
    app.add_handler(CallbackQueryHandler(paginate_menu, filters.regex(r"^settings_page_(\d+)$")), group=1)
    app.add_handler(CallbackQueryHandler(edit_var, filters.regex(r"^settings_edit_(.+)")), group=1)
    app.add_handler(CallbackQueryHandler(cancel_edit, filters.regex(r"^settings_cancel_edit$")), group=1)
    app.add_handler(CallbackQueryHandler(close_menu, filters.regex(r"^settings_closesettings$")), group=1)
