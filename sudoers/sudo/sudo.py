import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.handlers import (
    MessageHandler,
    ChatMemberUpdatedHandler
)
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    ChatMemberUpdated,
    ChatType
)
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    ChatWriteForbidden,
    UserIsBlocked,
    InputUserDeactivated,
    FloodWait,
    PeerIdInvalid
)
from config import (
    OWNER_ID,
    UPDATE_CHANNEL_URL,
    COMMAND_PREFIX,
    DEVELOPER_USER_ID
)
from core.database import auth_admins, user_activity_collection
from utils.logger import LOGGER

async def update_user_activity(user_id: int, is_group: bool = False) -> None:
    """Update user or group activity in the database."""
    try:
        now = datetime.utcnow()
        update_data = {
            "$set": {
                "last_activity": now,
                "is_group": bool(is_group)
            },
            "$inc": {"activity_count": 1}
        }
        result = await user_activity_collection.update_one(
            {"user_id": user_id}, update_data, upsert=True
        )
        LOGGER.debug(f"Updated activity for user_id {user_id}, is_group={is_group}, result: {result.modified_count} modified, {result.upserted_id} upserted")
    except Exception as e:
        LOGGER.error(f"Error updating user activity for user_id {user_id}: {str(e)}")

async def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    try:
        auth_admins_data = await auth_admins.find({}, {"user_id": 1, "_id": 0}).to_list(None)
        return user_id == OWNER_ID or user_id in [admin["user_id"] for admin in auth_admins_data]
    except Exception as e:
        LOGGER.error(f"Error checking admin status for user_id {user_id}: {str(e)}")
        return False

async def broadcast_handler(client: Client, message: Message) -> None:
    """Handle broadcast and send commands."""
    if not message.from_user or not message.chat:
        LOGGER.error("Invalid user or chat information for broadcast command")
        return

    user_id = message.from_user.id
    if not await is_admin(user_id):
        LOGGER.info(f"Unauthorized broadcast attempt by user_id {user_id}")
        await client.send_message(message.chat.id, "**✘ Sorry You're Not Authorized Bro!**", parse_mode=ParseMode.MARKDOWN)
        return

    is_broadcast = message.command[0].lower() in ["broadcast", "b"]
    LOGGER.info(f"{'Broadcast' if is_broadcast else 'Send'} initiated by user_id {user_id}")

    if message.reply_to_message and (
        message.reply_to_message.text or message.reply_to_message.photo or
        message.reply_to_message.video or message.reply_to_message.audio or
        message.reply_to_message.document
    ):
        await process_broadcast(client, message.reply_to_message, is_broadcast, message.chat.id)
    elif is_broadcast and len(message.command) > 1:
        await process_broadcast(client, " ".join(message.command[1:]), is_broadcast, message.chat.id)
    else:
        action = "broadcast" if is_broadcast else "send"
        await client.send_message(
            message.chat.id, f"**Please send a message to {action}.**", parse_mode=ParseMode.MARKDOWN
        )
        async def callback(client: Client, msg: Message):
            if msg.from_user and msg.from_user.id == user_id and msg.chat.id == message.chat.id:
                if not (msg.text or msg.photo or msg.video or msg.audio or msg.document):
                    await client.send_message(
                        msg.chat.id, "**✘ Send a valid text, photo, video, audio, or document!**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                await process_broadcast(client, msg, is_broadcast, msg.chat.id)
                client.remove_handler(handler, group=2)
        handler = MessageHandler(callback, filters.user(user_id) & filters.chat(message.chat.id))
        client.add_handler(handler, group=2)

async def process_broadcast(client: Client, content, is_broadcast: bool = True, chat_id: int = None) -> None:
    """Process the broadcast or forward operation."""
    try:
        if isinstance(content, str):
            broadcast_text = content
            broadcast_msg = None
        elif isinstance(content, Message):
            broadcast_text = None
            broadcast_msg = content
        else:
            raise ValueError("Invalid content type")

        LOGGER.info(f"Processing {'broadcast' if is_broadcast else 'forward'}")
        processing_msg = await client.send_message(
            chat_id, f"**💫 {'Broadcasting' if is_broadcast else 'Sending'} In Progress...**",
            parse_mode=ParseMode.MARKDOWN
        )

        bot_info = await client.get_me()
        bot_id = bot_info.id

        cutoff_date = datetime.utcnow() - timedelta(days=90)
        await user_activity_collection.delete_many({"last_activity": {"$lt": cutoff_date}})
        LOGGER.info("Cleaned up old entries from user_activity_collection")

        chats = await user_activity_collection.find({}, {"user_id": 1, "is_group": 1}).to_list(None)
        user_ids = [chat["user_id"] for chat in chats if not chat.get("is_group", False) and chat["user_id"] != bot_id]
        group_ids = [chat["user_id"] for chat in chats if chat.get("is_group", False) and chat["user_id"] != bot_id]
        LOGGER.info(f"Found {len(user_ids)} users and {len(group_ids)} groups to broadcast to")

        successful_users, blocked_users, successful_groups, failed_groups = 0, 0, 0, 0
        start_time = datetime.now()
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Updates Channel", url=UPDATE_CHANNEL_URL)]])

        all_chat_ids = user_ids + group_ids
        LOGGER.debug(f"Starting broadcast to {len(all_chat_ids)} chats")

        async def send_to_chat(target_chat_id: int) -> tuple:
            try:
                if broadcast_text:
                    sent_msg = await client.send_message(target_chat_id, broadcast_text, reply_markup=keyboard)
                    if target_chat_id in group_ids:
                        chat = await client.get_chat(target_chat_id)
                        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                            await client.pin_chat_message(target_chat_id, sent_msg.id)
                elif broadcast_msg:
                    if is_broadcast:
                        if not (broadcast_msg.text or broadcast_msg.photo or broadcast_msg.video or
                                broadcast_msg.audio or broadcast_msg.document):
                            raise ValueError("Unsupported message type")
                        sent_msg = await client.copy_message(
                            target_chat_id, broadcast_msg.chat.id, broadcast_msg.id, reply_markup=keyboard
                        )
                        if target_chat_id in group_ids:
                            chat = await client.get_chat(target_chat_id)
                            if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                                await client.pin_chat_message(target_chat_id, sent_msg.id)
                    else:
                        await client.forward_messages(target_chat_id, broadcast_msg.chat.id, broadcast_msg.id)
                if target_chat_id in user_ids:
                    return ("user", "success")
                else:
                    return ("group", "success")
            except FloodWait as e:
                LOGGER.warning(f"FloodWait for chat_id {target_chat_id}: Waiting {e.value}s")
                await asyncio.sleep(e.value)
                return await send_to_chat(target_chat_id)
            except UserIsBlocked:
                LOGGER.error(f"User blocked the bot: chat_id {target_chat_id}")
                if target_chat_id in user_ids:
                    return ("user", "blocked")
                else:
                    return ("group", "failed")
            except (InputUserDeactivated, ChatWriteForbidden, PeerIdInvalid) as e:
                LOGGER.error(f"Failed to send to chat_id {target_chat_id}: {str(e)}")
                if target_chat_id in user_ids:
                    return ("user", "blocked")
                else:
                    return ("group", "failed")
            except Exception as e:
                LOGGER.error(f"Error sending to chat_id {target_chat_id}: {str(e)}")
                if target_chat_id in user_ids:
                    return ("user", "blocked")
                else:
                    return ("group", "failed")

        results = await asyncio.gather(*[send_to_chat(chat_id) for chat_id in all_chat_ids], return_exceptions=True)

        for result in results:
            if isinstance(result, tuple):
                chat_type, status = result
                if chat_type == "user":
                    if status == "success":
                        successful_users += 1
                    elif status == "blocked":
                        blocked_users += 1
                elif chat_type == "group":
                    if status == "success":
                        successful_groups += 1
                    elif status == "failed":
                        failed_groups += 1

        time_diff = (datetime.now() - start_time).seconds
        await processing_msg.delete()

        summary_msg = await client.send_message(
            chat_id,
            f"**Successfully {'Broadcast' if is_broadcast else 'Forward'} Complete in {time_diff} seconds ✅**\n\n"
            f"**To Users:** `{successful_users}`\n"
            f"**Blocked:** `{blocked_users}`\n"
            f"**To Groups:** `{successful_groups}`\n"
            f"**Failed Groups:** `{failed_groups}`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        chat = await client.get_chat(chat_id)
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await client.pin_chat_message(chat_id, summary_msg.id)

        LOGGER.info(f"{'Broadcast' if is_broadcast else 'Forward'} completed: {successful_users} users, {successful_groups} groups, "
                    f"{blocked_users} blocked users, {failed_groups} failed groups")
    except Exception as e:
        LOGGER.error(f"Error in {'broadcast' if is_broadcast else 'forward'}: {str(e)}")
        await client.send_message(chat_id, "**✘ Error Processing Request!**", parse_mode=ParseMode.MARKDOWN)

async def stats_handler(client: Client, message: Message) -> None:
    """Handle stats command."""
    if not message.from_user or not message.chat:
        LOGGER.error("Invalid user or chat for stats command")
        return

    user_id = message.from_user.id
    if not await is_admin(user_id):
        LOGGER.info(f"Unauthorized stats attempt by user_id {user_id}")
        await client.send_message(message.chat.id, "**✘ Unauthorized Access!**", parse_mode=ParseMode.MARKDOWN)
        return

    LOGGER.info(f"Stats command by user_id {user_id}")
    try:
        now = datetime.utcnow()
        daily_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gte": now - timedelta(days=1)}})
        weekly_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gte": now - timedelta(weeks=1)}})
        monthly_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gte": now - timedelta(days=30)}})
        yearly_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gte": now - timedelta(days=365)}})
        total_users = await user_activity_collection.count_documents({"is_group": False})
        total_groups = await user_activity_collection.count_documents({"is_group": True})

        stats_text = (
            f"**Smart Bot Status ⇾ Report ✅**\n"
            f"**━━━━━━━━━━━━━━━━**\n"
            f"**Users & Groups Engagements:**\n"
            f"**1 Day:** {daily_users} users were active\n"
            f"**1 Week:** {weekly_users} users were active\n"
            f"**1 Month:** {monthly_users} users were active\n"
            f"**1 Year:** {yearly_users} users were active\n"
            f"**Total Connected Groups:** {total_groups}\n"
            f"**━━━━━━━━━━━━━━━━**\n"
            f"**Total Smart Tools Users:** {total_users} ✅"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Updates Channel", url=UPDATE_CHANNEL_URL)]])
        await client.send_message(
            message.chat.id, stats_text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
        LOGGER.info("Stats command completed")
    except Exception as e:
        LOGGER.error(f"Error in stats: {str(e)}")
        await client.send_message(message.chat.id, "**✘ Error Fetching Stats!**", parse_mode=ParseMode.MARKDOWN)

async def group_added_handler(client: Client, message: Message) -> None:
    """Handle bot being added to a group."""
    try:
        if not message.new_chat_members or not message.chat:
            return
        for member in message.new_chat_members:
            if member.is_self:
                chat_id = message.chat.id
                await update_user_activity(chat_id, is_group=True)
                await client.send_message(
                    chat_id,
                    "**Thank you for adding me to this group!**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_to_message_id=message.id
                )
                LOGGER.info(f"Bot added to group {chat_id}")
    except Exception as e:
        LOGGER.error(f"Error in group_added_handler for chat_id {message.chat.id}: {str(e)}")

async def group_removed_handler(client: Client, member_update: ChatMemberUpdated) -> None:
    """Handle bot being removed or banned from a group."""
    try:
        if (member_update.old_chat_member and member_update.old_chat_member.status in ["member", "administrator"] and
            member_update.new_chat_member and member_update.new_chat_member.status in ["banned", "left"] and
            member_update.new_chat_member.user.is_self):
            chat_id = member_update.chat.id
            await user_activity_collection.delete_one({"user_id": chat_id, "is_group": True})
            LOGGER.info(f"Bot removed/banned from group {chat_id}, removed from database")
    except Exception as e:
        LOGGER.error(f"Error in group_removed_handler for chat_id {member_update.chat.id}: {str(e)}")

async def update_user_activity_handler(client: Client, message: Message) -> None:
    """Update user activity for private chats and groups."""
    try:
        if message.from_user:
            is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
            await update_user_activity(message.from_user.id, is_group=False)  # Track individual user
            if is_group and message.chat:
                await update_user_activity(message.chat.id, is_group=True)  # Track group
    except Exception as e:
        LOGGER.error(f"Error in update_user_activity_handler for message_id {message.id}: {str(e)}")

async def start_handler(client: Client, message: Message) -> None:
    """Handle /start command to ensure user activity is recorded."""
    try:
        if message.from_user and message.chat:
            is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
            await update_user_activity(message.from_user.id, is_group=False)
            if is_group:
                await update_user_activity(message.chat.id, is_group=True)
            await client.send_message(
                message.chat.id,
                "**Welcome to Smart Bot!** Use /help to see available commands.",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.info(f"Start command by user_id {message.from_user.id} in chat_id {message.chat.id}")
    except Exception as e:
        LOGGER.error(f"Error in start_handler for chat_id {message.chat.id}: {str(e)}")

def setup_admin_handler(app: Client) -> None:
    """Set up all admin and activity handlers."""
    prefixes = COMMAND_PREFIX + [""]
    app.add_handler(
        MessageHandler(
            broadcast_handler,
            (filters.command(["broadcast", "b", "send", "s"], prefixes=prefixes) & (filters.private | filters.group))
        ),
        group=2
    )
    app.add_handler(
        MessageHandler(
            stats_handler,
            (filters.command(["stats", "report", "status"], prefixes=prefixes) & (filters.private | filters.group))
        ),
        group=2
    )
    app.add_handler(
        MessageHandler(
            start_handler,
            (filters.command(["start"], prefixes=prefixes) & (filters.private | filters.group))
        ),
        group=2
    )
    app.add_handler(
        MessageHandler(
            update_user_activity_handler,
            filters.all & (filters.private | filters.group)
        ),
        group=3
    )
    app.add_handler(
        MessageHandler(
            group_added_handler,
            filters.group & filters.new_chat_members
        ),
        group=2
    )
    app.add_handler(
        ChatMemberUpdatedHandler(
            group_removed_handler,
            filters.group
        ),
        group=2
    )
