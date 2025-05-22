import asyncio
from datetime import datetime, timedelta
import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode
import pymongo
from config import OWNER_IDS, UPDATE_CHANNEL_URL, COMMAND_PREFIX, DEVELOPER_USER_ID
from core import user_activity_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_user_activity(user_id, is_group=False):
    """Update user or group activity in the MongoDB database."""
    now = datetime.utcnow()
    user = user_activity_collection.find_one({"user_id": user_id})
    if not user:
        user_activity_collection.insert_one({
            "user_id": user_id,
            "is_group": is_group,
            "last_activity": now,
            "daily": 0,
            "weekly": 0,
            "monthly": 0,
            "yearly": 0
        })
    else:
        user_activity_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_activity": now}},
            upsert=True
        )
        user_activity_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"daily": 1, "weekly": 1, "monthly": 1, "yearly": 1}}
        )

def is_admin(user_id):
    """Check if the user is an admin."""
    return user_id in OWNER_IDS

async def broadcast_handler(client: Client, message: Message):
    """Handle broadcast or send commands for admins."""
    if not is_admin(message.from_user.id):
        return await client.send_message(
            chat_id=message.chat.id,
            text="**✘Kids Not Allowed To Do This↯**"
        )

    is_broadcast = message.command[0].lower() in ["broadcast", "b"]

    if message.reply_to_message:
        # Admin replied to a message
        return await process_broadcast(client, message.reply_to_message, is_broadcast, message.chat.id)
    elif is_broadcast and len(message.command) > 1:
        # Admin provided text directly
        broadcast_text = " ".join(message.command[1:])
        return await process_broadcast(client, broadcast_text, is_broadcast, message.chat.id)
    else:
        # Wait for the next message
        action_type = "broadcast" if is_broadcast else "send"
        response = await client.send_message(
            chat_id=message.chat.id,
            text=f"**Please send the message you want to {action_type}.**"
        )

        async def broadcast_message_callback(client: Client, broadcast_msg: Message):
            if broadcast_msg.from_user.id == message.from_user.id and broadcast_msg.chat.id == message.chat.id:
                await process_broadcast(client, broadcast_msg, is_broadcast, message.chat.id)
                client.remove_handler(broadcast_message_handler, group=1)

        broadcast_message_handler = MessageHandler(
            broadcast_message_callback,
            filters.user(message.from_user.id) & filters.chat(message.chat.id)
        )
        client.add_handler(broadcast_message_handler, group=1)
        return response

async def process_broadcast(client: Client, content, is_broadcast=True, chat_id=None):
    """Process and send broadcast or forwarded messages."""
    if isinstance(content, str):
        broadcast_text = content
        broadcast_msg = None
    elif isinstance(content, Message):
        broadcast_msg = content
        broadcast_text = None
    else:
        logger.error("Invalid content type for broadcast")
        return await client.send_message(
            chat_id=chat_id,
            text="**Sorry This Content Not Allowed!**"
        )

    processing_message = await client.send_message(
        chat_id=chat_id,
        text=f'**💫 {"Broadcasting" if is_broadcast else "Sending"} Message In Progress 💫**'
    )

    user_ids = [user["user_id"] for user in user_activity_collection.find({"is_group": False})]
    group_ids = [group["user_id"] for group in user_activity_collection.find({"is_group": True})]

    successful_users = 0
    failed_users = 0
    successful_groups = 0
    failed_groups = 0
    broadcast_start_time = datetime.now()

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💥 Bot Updates 💥", url=UPDATE_CHANNEL_URL)]])

    for target_chat_id in user_ids + group_ids:
        try:
            if broadcast_text:
                await client.send_message(
                    chat_id=target_chat_id,
                    text=broadcast_text,
                    reply_markup=keyboard
                )
            elif broadcast_msg:
                if is_broadcast:
                    if broadcast_msg.text:
                        await client.send_message(
                            chat_id=target_chat_id,
                            text=broadcast_msg.text,
                            reply_markup=keyboard
                        )
                    elif broadcast_msg.photo:
                        await client.send_photo(
                            chat_id=target_chat_id,
                            photo=broadcast_msg.photo.file_id,
                            caption=broadcast_msg.caption or "",
                            reply_markup=keyboard
                        )
                    elif broadcast_msg.video:
                        await client.send_video(
                            chat_id=target_chat_id,
                            video=broadcast_msg.video.file_id,
                            caption=broadcast_msg.caption or "",
                            reply_markup=keyboard
                        )
                    elif broadcast_msg.audio:
                        await client.send_audio(
                            chat_id=target_chat_id,
                            audio=broadcast_msg.audio.file_id,
                            caption=broadcast_msg.caption or "",
                            reply_markup=keyboard
                        )
                    elif broadcast_msg.document:
                        await client.send_document(
                            chat_id=target_chat_id,
                            document=broadcast_msg.document.file_id,
                            caption=broadcast_msg.caption or "",
                            reply_markup=keyboard
                        )
                    else:
                        await client.copy_message(
                            chat_id=target_chat_id,
                            from_chat_id=broadcast_msg.chat.id,
                            message_id=broadcast_msg.id
                        )
                else:
                    await client.forward_messages(
                        chat_id=target_chat_id,
                        from_chat_id=broadcast_msg.chat.id,
                        message_ids=broadcast_msg.id
                    )
            if target_chat_id in user_ids:
                successful_users += 1
            else:
                successful_groups += 1
        except Exception as e:
            logger.error(f"Failed to send to {target_chat_id}: {e}")
            if target_chat_id in user_ids:
                failed_users += 1
            else:
                failed_groups += 1

    await processing_message.delete()

    broadcast_end_time = datetime.now()
    time_diff = broadcast_end_time - broadcast_start_time
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_taken = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    action_success = "Broadcast" if is_broadcast else "Forward"
    response_text = (
        f"**💥 {action_success} Successful! 💥**\n"
        "**✘━━━━━━━━━━━✘**\n"
        f"**👀 To Users:** `{successful_users}` ✨\n"
        f"**✘ Blocked Users:** `{failed_users}` ❄️\n"
        "**✘━━━━━━━━━━━✘**\n"
        f"**🌐 To Groups:** `{successful_groups}` 🌟\n"
        f"**✘ Blocked Groups:** `{failed_groups}` 💫\n"
        "**✘━━━━━━━━━━━✘**\n"
        f"**↯ Time Taken:** `{time_taken}` 🇧🇩"
    )

    return await client.send_message(
        chat_id=chat_id,
        text=response_text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("💥 Bot Updates 💥", url=UPDATE_CHANNEL_URL)]]
        )
    )

async def stats_handler(client: Client, message: Message):
    """Handle stats command to display bot usage statistics."""
    if not is_admin(message.from_user.id):
        return await client.send_message(
            chat_id=message.chat.id,
            text="**✘Kids Not Allowed To Do This↯**"
        )

    now = datetime.utcnow()
    daily_users = user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(days=1)}})
    weekly_users = user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(weeks=1)}})
    monthly_users = user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(days=30)}})
    yearly_users = user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(days=365)}})
    
    total_users = user_activity_collection.count_documents({"is_group": False})
    total_groups = user_activity_collection.count_documents({"is_group": True})

    stats_text = (
        "**💥 Bot's Full Database Info 💥**\n"
        "**✘━━━━━━━━━━━✘**\n"
        "**✨ Registered Users Activity: ✨**\n"
        f"- 💫 Daily Active: {daily_users} 🔥\n"
        f"- 🌟 Weekly Active: {weekly_users} ⚡\n"
        f"- ❄️ Monthly Active: {monthly_users} 🌈\n"
        f"- 👀 Annual Active: {yearly_users} 🎯\n"
        "**✘━━━━━━━━━━━✘**\n"
        "**✘ Total Metrics: ✘**\n"
        f"- 👥 Total Users: {total_users} 💫\n"
        f"- 🌐 Total Groups: {total_groups} 🌟\n"
        f"- ↯ Database Size: {total_users + total_groups} ✨\n"
    )

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💥 Bot Updates 💥", url=UPDATE_CHANNEL_URL)]])
    return await client.send_message(
        chat_id=message.chat.id,
        text=stats_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

async def group_added_handler(client: Client, message: Message):
    """Handle event when bot is added to a group."""
    for new_member in message.new_chat_members:
        if new_member.is_self:
            chat_id = message.chat.id
            update_user_activity(chat_id, is_group=True)
            return await client.send_message(
                chat_id=chat_id,
                text=(
                    "**💥 Thank You For Adding Me To This Group! 💫**\n"
                    "**✘ ━━━━━━━━━━━━━━━━━━ ✘**\n"
                    "**✨ I'm here to assist with various tasks and enhance your group experience.\n"
                    "↯ Feel free to explore my features and let me know if you need help! 🌟**\n"
                    "**✘ ━━━━━━━━━━━━━━━━━━ ✘**"
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("➕ Add Me 💥", url="https://t.me/ItsSmartToolBot?startgroup=new&admin=post_messages+delete_messages+edit_messages+pin_messages+change_info+invite_users+promote_members"),
                        InlineKeyboardButton("My Dev 💫", user_id=DEVELOPER_USER_ID)
                    ]
                ])
            )
    return None  # Explicit None for non-self member additions, as this won't be awaited

async def activity_handler(client: Client, message: Message):
    """Track user activity for all messages."""
    if message.from_user:
        update_user_activity(message.from_user.id)
    return None  # Explicit None, as this handler is not awaited

def setup_admin_handler(app: Client):
    """Set up command and event handlers for the bot."""
    app.add_handler(
        MessageHandler(
            broadcast_handler,
            (filters.command(["broadcast", "b", "send", "s"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
        ),
        group=1
    )
    
    app.add_handler(
        MessageHandler(
            stats_handler,
            (filters.command(["stats", "report", "status"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
        ),
        group=1
    )
    
    app.add_handler(
        MessageHandler(
            activity_handler,
            filters.all
        ),
        group=2
    )

    app.add_handler(
        MessageHandler(
            group_added_handler,
            filters.group & filters.new_chat_members
        ),
        group=1
    )
