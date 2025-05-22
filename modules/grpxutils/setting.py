# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pymongo import MongoClient
from config import COMMAND_PREFIX
import logging
import time
from core import group_settings, group_channel_bindings
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Button categories configuration
BUTTON_CATEGORIES = {
    "Media": [
        ("Picture", "picture"),
        ("Video", "video"),
        ("Music", "music"),
        ("GIF", "gift"),
    ],
    "Content Control": [
        ("Link", "link"),
        ("Hashtag", "hashtag"),
        ("Users", "users"),
        ("Address", "address")
    ],
    "Privacy Control": [
        ("Contact", "contact"),
        ("Forward", "forward")
    ],
    "Interaction Control": [
        ("Reply", "reply"),
        ("Game", "game"),
        ("Sticker", "sticker")
    ],
    "Others Control": [
        ("File", "file"),
        ("Voice", "voice")
    ]
}

def contains_links(text):
    """Check if text contains common link patterns without using regex"""
    if not text:
        return False
    
    link_prefixes = [
        "http",
        "https",
        "tiktok",
        "ref",
        "joinchat",
        "invite",
        "t.me",
        "www",
        "telegram.me",
        "telegram.dog"
    ]
    
    text = text.lower()
    return any(prefix in text for prefix in link_prefixes)

def get_group_settings(chat_id):
    """Retrieve or initialize group settings from the database."""
    try:
        settings = group_settings.find_one({"chat_id": chat_id})
        if not settings:
            default_settings = {
                "chat_id": chat_id,
                "picture": True, "link": True, "sticker": True, "file": True,
                "video": True, "music": True, "forward": True, "gift": True,
                "voice": True, "contact": True, "users": True, "hashtag": True,
                "address": True, "reply": True, "game": True
            }
            group_settings.insert_one(default_settings)
            return default_settings
        return settings
    except Exception as e:
        logger.error(f"Error retrieving group settings: {e}")
        return None

def update_group_setting(chat_id, key=None, value=None, reset=False, default_settings=None):
    """Update a specific group setting or reset all settings in the database."""
    try:
        if reset and default_settings:
            group_settings.replace_one(
                {"chat_id": chat_id},
                default_settings,
                upsert=True
            )
            return True
        elif key is not None:
            group_settings.update_one(
                {"chat_id": chat_id},
                {"$set": {key: value}},
                upsert=True
            )
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating group setting: {e}")
        return False

def get_categorized_buttons(settings, chat_id):
    """Create categorized inline keyboard buttons for settings."""
    keyboard = []
    
    for category, items in BUTTON_CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(category, callback_data="none")])
        for (display_name, key) in items:
            status = "Allowed" if settings.get(key, True) else "Blocked"
            keyboard.append([
                InlineKeyboardButton(display_name, callback_data=f"info_{key}"),
                InlineKeyboardButton(status, callback_data=f"toggle_{key}_{chat_id}")
            ])
    
    keyboard.append([
        InlineKeyboardButton("Close", callback_data="close_settings"),
        InlineKeyboardButton("Reset All", callback_data=f"reset_{chat_id}")
    ])
    
    return InlineKeyboardMarkup(keyboard)

async def is_admin(client, user_id, chat_id):
    """Check if a user is an admin in the group."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

async def delete_message_with_delay(client, chat_id, message_id, delay=10):
    """Delete a message after a specified delay."""
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

def extract_channel_username(input_text):
    """Extract the channel username from input text."""
    input_text = input_text.strip()
    if input_text.startswith("https://t.me/"):
        return input_text.split("https://t.me/")[1].lstrip('@')
    elif input_text.startswith("t.me/"):
        return input_text.split("t.me/")[1].lstrip('@')
    elif input_text.startswith("@"):
        return input_text.lstrip('@')
    return input_text

def safe_starts_with_prefix(_, __, m):
    """Safely check if message starts with a prefix, handling decoding errors."""
    try:
        return m.text and m.text[0] in ['/', '.', ',', '!']
    except UnicodeDecodeError:
        return False

def setup_setting_handlers(app):
    """Set up all handlers for both settings and channel features."""

    @app.on_message(filters.command(["setting"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_setting_group(client, message: Message):
        try:
            user_id = message.from_user.id if message.from_user else None
            chat_id = message.chat.id

            if not user_id or not await is_admin(client, user_id, chat_id):
                await client.send_message(
                    chat_id,
                    "This command is only for group admins.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            settings = get_group_settings(chat_id)
            if not settings:
                await client.send_message(
                    chat_id,
                    "Could not load group settings.",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            bot_username = (await client.get_me()).username
            group_name = (await client.get_chat(chat_id)).title
            
            try:
                await client.send_message(
                    user_id,
                    f"{group_name} Group Settings\n\n"
                    "Manage what content is allowed in your group\n\n"
                    "Allowed | Blocked\n",
                    reply_markup=get_categorized_buttons(settings, chat_id),
                    parse_mode=ParseMode.MARKDOWN
                )
                await client.send_message(
                    chat_id,
                    f"Settings menu sent to your PM. Check @{bot_username}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Error sending settings PM: {e}")
                await client.send_message(
                    chat_id,
                    "Please start a chat with me first to receive settings.",
                    parse_mode=ParseMode.MARKDOWN
                )

        except Exception as e:
            logger.error(f"Error in handle_setting_group: {e}")
            await client.send_message(
                chat_id,
                "I cannot message you.",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_callback_query(filters.regex(r"^toggle_"))
    async def handle_toggle(client, callback_query):
        try:
            data = callback_query.data.split("_")
            if len(data) < 3:
                await callback_query.answer("Invalid request", show_alert=True)
                return

            key, chat_id = data[1], int(data[2])
            user_id = callback_query.from_user.id

            if not await is_admin(client, user_id, chat_id):
                await callback_query.answer("This is only for group admins.", show_alert=True)
                return

            settings = get_group_settings(chat_id)
            if not settings:
                await callback_query.answer("Settings not found", show_alert=True)
                return

            new_value = not settings.get(key, True)
            if update_group_setting(chat_id, key, new_value):
                updated_settings = get_group_settings(chat_id)
                await callback_query.edit_message_reply_markup(
                    get_categorized_buttons(updated_settings, chat_id)
                )
                await callback_query.answer(
                    f"{key.capitalize()} is now {'Allowed' if new_value else 'Blocked'}"
                )
            else:
                await callback_query.answer("Failed to update", show_alert=True)

        except Exception as e:
            logger.error(f"Error in handle_toggle: {e}")
            await callback_query.answer("Database error", show_alert=True)

    @app.on_callback_query(filters.regex(r"^close_settings$"))
    async def handle_close_settings(client, callback_query):
        try:
            await callback_query.message.delete()
            await callback_query.answer("Settings menu closed")
        except Exception as e:
            logger.error(f"Error closing settings menu: {e}")
            await callback_query.answer("Failed to close settings", show_alert=True)

    @app.on_callback_query(filters.regex(r"^reset_"))
    async def handle_reset_settings(client, callback_query):
        try:
            chat_id = int(callback_query.data.split("_")[1])
            user_id = callback_query.from_user.id

            if not await is_admin(client, user_id, chat_id):
                await callback_query.answer("This is only for group admins.", show_alert=True)
                return

            default_settings = {
                "chat_id": chat_id,
                "picture": True, "link": True, "sticker": True, "file": True,
                "video": True, "music": True, "forward": True, "gift": True,
                "voice": True, "contact": True, "users": True, "hashtag": True,
                "address": True, "reply": True, "game": True
            }

            if update_group_setting(chat_id, None, None, reset=True, default_settings=default_settings):
                await callback_query.edit_message_reply_markup(
                    get_categorized_buttons(default_settings, chat_id)
                )
                await callback_query.answer("All settings have been reset to default")
            else:
                await callback_query.answer("Failed to reset settings", show_alert=True)

        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            await callback_query.answer("Error resetting settings", show_alert=True)

    @app.on_message(filters.command(["setchannel"], prefixes=["/", ".", ",", "!"]) & filters.group)
    async def handle_setchannel(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(client, user_id, chat_id):
            await client.send_message(chat_id, "This command is only for group admins.", parse_mode=ParseMode.MARKDOWN)
            return

        if len(message.command) < 2:
            await client.send_message(chat_id, "Please provide a channel username.", parse_mode=ParseMode.MARKDOWN)
            return

        channel_input = " ".join(message.command[1:])
        channel_username = extract_channel_username(channel_input)

        try:
            channel = await client.get_chat(channel_username)
            if channel.type != ChatType.CHANNEL:
                await client.send_message(chat_id, "The provided username is not a channel.", parse_mode=ParseMode.MARKDOWN)
                return

            group_channel_bindings.update_one(
                {"chat_id": chat_id},
                {"$set": {"channel_id": channel.id, "channel_username": channel_username}},
                upsert=True
            )
            await client.send_message(
                chat_id,
                f"Channel @{channel_username} has been connected to this chat.\n"
                "Group members must join the channel to send messages.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error fetching channel details: {e}")
            await client.send_message(
                chat_id,
                "Failed to set channel. Ensure bot is admin in both group and channel.",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_message(filters.command(["delchannel"], prefixes=["/", ".", ",", "!"]) & filters.group)
    async def handle_delchannel(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(client, user_id, chat_id):
            await client.send_message(chat_id, "This command is only for group admins.", parse_mode=ParseMode.MARKDOWN)
            return

        binding = group_channel_bindings.find_one({"chat_id": chat_id})
        if not binding:
            await client.send_message(chat_id, "No channel is currently connected to this chat.", parse_mode=ParseMode.MARKDOWN)
            return

        group_channel_bindings.delete_one({"chat_id": chat_id})
        await client.send_message(chat_id, "The channel connection has been removed.", parse_mode=ParseMode.MARKDOWN)

    @app.on_message(
        filters.group & 
        ~filters.service & 
        ~filters.create(safe_starts_with_prefix)
    )
    async def handle_group_message(client, message: Message):
        try:
            chat_id = message.chat.id
            user_id = message.from_user.id if message.from_user else None

            if user_id and await is_admin(client, user_id, chat_id):
                return

            binding = group_channel_bindings.find_one({"chat_id": chat_id})
            if binding:
                channel_id = binding["channel_id"]
                try:
                    member = await client.get_chat_member(channel_id, user_id)
                    if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                        await message.delete()
                        channel_username = binding["channel_username"]
                        user_full_name = message.from_user.first_name
                        group_name = (await client.get_chat(chat_id)).title
                        await client.send_message(
                            chat_id,
                            f"Sorry, {user_full_name}, to write in {group_name}\n"
                            f"You must join @{channel_username}",
                            reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton("Join Now", url=f"https://t.me/{channel_username}")]]
                            ),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                except UserNotParticipant:
                    await message.delete()
                    channel_username = binding["channel_username"]
                    user_full_name = message.from_user.first_name
                    group_name = (await client.get_chat(chat_id)).title
                    await client.send_message(
                        chat_id,
                        f"Sorry, {user_full_name}, to write in {group_name}\n"
                        f"You must join @{channel_username}",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Join Now", url=f"https://t.me/{channel_username}")]]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                except Exception as e:
                    logger.error(f"Error checking channel membership: {e}")
                    await message.delete()
                    await client.send_message(chat_id, "You must join the channel.", parse_mode=ParseMode.MARKDOWN)
                    return

            settings = get_group_settings(chat_id)
            if not settings:
                return

            if message.text or message.caption:
                text_content = message.text or message.caption
                
                if not settings["link"] and contains_links(text_content):
                    await message.delete()
                    warning_msg = await client.send_message(
                        chat_id,
                        f"Links are not allowed in this group.\n"
                        f"Message from: {message.from_user.mention if message.from_user else 'Unknown user'}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await delete_message_with_delay(client, chat_id, warning_msg.id)
                    return

                if not settings["users"] and "@" in text_content:
                    await message.delete()
                    warning_msg = await client.send_message(
                        chat_id,
                        "Mentioning users is not allowed in this group.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await delete_message_with_delay(client, chat_id, warning_msg.id)
                    return

                if not settings["hashtag"] and "#" in text_content:
                    await message.delete()
                    warning_msg = await client.send_message(
                        chat_id,
                        "Hashtags are not allowed in this group.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await delete_message_with_delay(client, chat_id, warning_msg.id)
                    return

            if message.reply_to_message and not settings["reply"]:
                await message.delete()
                warning_msg = await client.send_message(
                    chat_id,
                    "Replies are not allowed in this group.",
                    parse_mode=ParseMode.MARKDOWN
                )
                await delete_message_with_delay(client, chat_id, warning_msg.id)
                return

            if (message.forward_from or message.forward_from_chat) and not settings["forward"]:
                await message.delete()
                warning_msg = await client.send_message(
                    chat_id,
                    "Forwarded messages are not allowed in this group.",
                    parse_mode=ParseMode.MARKDOWN
                )
                await delete_message_with_delay(client, chat_id, warning_msg.id)
                return

            content_checks = [
                (message.photo, "picture", "Pictures"),
                (message.sticker, "sticker", "Stickers"),
                (message.document, "file", "Files"),
                (message.video, "video", "Videos"),
                (message.audio, "music", "Music"),
                (message.animation, "gift", "GIFs"),
                (message.voice, "voice", "Voice messages"),
                (message.contact, "contact", "Contacts"),
                (message.location or message.venue, "address", "Locations"),
                (message.dice or message.game, "game", "Games")
            ]

            for content, setting_key, error_msg in content_checks:
                if content and not settings.get(setting_key, True):
                    await message.delete()
                    warning_msg = await client.send_message(
                        chat_id,
                        f"{error_msg} are not allowed in this group.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await delete_message_with_delay(client, chat_id, warning_msg.id)
                    break

        except Exception as e:
            logger.error(f"Error in handle_group_message: {e}")