# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from pyrogram.errors import UserNotParticipant, BadRequest, UserAdminInvalid
from config import COMMAND_PREFIX
from utils import LOGGER

async def is_admin(app, user_id, chat_id):
    try:
        member = await app.get_chat_member(chat_id, user_id)
        LOGGER.info(f"User ID: {user_id}, Status: {member.status}")
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        LOGGER.error(f"Error fetching member status for user {user_id} in chat {chat_id}: {e}")
        return False

async def handle_error(client, message, error_msg="Bot lacks necessary permissions or an error occurred."):
    try:
        await client.send_message(message.chat.id, f"**❌ {error_msg}**", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        LOGGER.error(f"Error sending error message to chat {message.chat.id}: {e}")

# Dictionary to store group-channel bindings (unused in this script)
#group_channel_bindings = {}

def setup_ban_handlers(app):
    
    @app.on_message(filters.command(["kick"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_kick(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        # Check if the user is an admin
        if user_id and not await is_admin(app, user_id, chat_id):
            await message.reply_text("**✘ Kids Are Not Allowed To Do This  ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        # Check if the user is replying to a message or specifying a username
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user.id
            reason = " ".join(message.command[1:]) or "No reason"
        else:
            target_users = [word for word in message.command[1:] if word.startswith('@')]
            reason = " ".join([word for word in message.command[1:] if not word.startswith('@')]) or "No reason"
            if not target_users:
                await message.reply_text("**❌ Please specify the username or reply to a message.**", parse_mode=ParseMode.MARKDOWN)
                return

        try:
            if message.reply_to_message:
                # Kick the user by replying to their message
                await app.ban_chat_member(chat_id, target_user)  # Ban to kick
                await app.unban_chat_member(chat_id, target_user)  # Unban to allow rejoining
                user_info = await app.get_users(target_user)
                username = user_info.username or user_info.first_name
                await message.reply_text(
                    f"**{username} has been kicked for [{reason}].** ✅",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.info(f"Kicked user @{username} (ID: {target_user}) from chat {chat_id} for: {reason}")
            else:
                # Kick the user by username
                for target_user in target_users:
                    user_info = await app.get_users(target_user)
                    target_user_id = user_info.id
                    await app.ban_chat_member(chat_id, target_user_id)  # Ban to kick
                    await app.unban_chat_member(chat_id, target_user_id)  # Unban to allow rejoining
                    username = user_info.username or user_info.first_name
                    await message.reply_text(
                        f"**{username} has been kicked for [{reason}].** ✅",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    LOGGER.info(f"Kicked user @{username} (ID: {target_user_id}) from chat {chat_id} for: {reason}")
        except UserNotParticipant:
            await handle_error(client, message, "User is not a member of this group.")
        except UserAdminInvalid:
            await handle_error(client, message, "Cannot kick an admin or the bot itself.")
        except BadRequest as e:
            await handle_error(client, message, f"Failed to kick user: {str(e)}")
        except Exception as e:
            LOGGER.error(f"Error kicking user in chat {chat_id}: {e}")
            await handle_error(client, message)
    
    @app.on_message(filters.command(["del"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_delete(client, message: Message):
        # Check if the user is replying to a message
        if not message.reply_to_message:
            await message.reply_text("**❌ Please reply to a message to delete it.**", parse_mode=ParseMode.MARKDOWN)
            return

        # Check if the user is an admin
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(app, user_id, chat_id):
            await message.reply_text("**✘ Kids Are Not Allowed To Do This  ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            # Delete the replied-to message
            await client.delete_messages(chat_id, message.reply_to_message.id)
            # Notify the user
            await message.reply_text("**✅ Message deleted successfully.**", parse_mode=ParseMode.MARKDOWN)
            LOGGER.info(f"Deleted message {message.reply_to_message.id} in chat {chat_id} by user {user_id}")
        except BadRequest as e:
            LOGGER.error(f"Error deleting message in chat {chat_id}: {e}")
            await handle_error(client, message, f"Failed to delete message: {str(e)}")
        except Exception as e:
            LOGGER.error(f"Error deleting message in chat {chat_id}: {e}")
            await handle_error(client, message)
    
    @app.on_message(filters.command(["ban", "fuck"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_ban(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(app, user_id, chat_id):
            await client.send_message(message.chat.id, "**✘ Kids Are Not Allowed To Do This  ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user.id
            reason = " ".join(message.command[1:]) or "No reason"
        else:
            target_users = [word for word in message.command[1:] if word.startswith('@')]
            reason = " ".join([word for word in message.command[1:] if not word.startswith('@')]) or "No reason"
            if not target_users:
                await client.send_message(message.chat.id, "**❌ Please specify the username or Reply To A User**", parse_mode=ParseMode.MARKDOWN)
                return

        try:
            if message.reply_to_message:
                await app.ban_chat_member(chat_id, target_user)
                user_info = await app.get_users(target_user)
                username = user_info.username or user_info.first_name
                await client.send_message(
                    message.chat.id,
                    f"**{username} has been banned for [{reason}].** ✅",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Unban", callback_data=f"unban:{target_user}")]]
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.info(f"Banned user @{username} (ID: {target_user}) from chat {chat_id} for: {reason}")
            else:
                for target_user in target_users:
                    user_info = await app.get_users(target_user)
                    target_user_id = user_info.id
                    await app.ban_chat_member(chat_id, target_user_id)
                    username = user_info.username or user_info.first_name
                    await client.send_message(
                        message.chat.id,
                        f"**{username} has been banned for [{reason}].** ✅",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Unban", callback_data=f"unban:{target_user_id}")]]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    LOGGER.info(f"Banned user @{username} (ID: {target_user_id}) from chat {chat_id} for: {reason}")
        except UserNotParticipant:
            await handle_error(client, message, "User is not a member of this group.")
        except UserAdminInvalid:
            await handle_error(client, message, "Cannot ban an admin or the bot itself.")
        except BadRequest as e:
            await handle_error(client, message, f"Failed to ban user: {str(e)}")
        except Exception as e:
            LOGGER.error(f"Error banning user in chat {chat_id}: {e}")
            await handle_error(client, message)

    @app.on_message(filters.command(["unban", "unfuck"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_unban(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(app, user_id, chat_id):
            await client.send_message(message.chat.id, "**✘ Kids Are Not Allowed To Do This  ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user.id
        else:
            target_users = [word for word in message.command[1:] if word.startswith('@')]
            if not target_users:
                await client.send_message(message.chat.id, "**❌ Please specify the username or Reply To A User**", parse_mode=ParseMode.MARKDOWN)
                return

        try:
            if message.reply_to_message:
                await app.unban_chat_member(chat_id, target_user)
                user_info = await app.get_users(target_user)
                username = user_info.username or user_info.first_name
                await client.send_message(message.chat.id, f"**{username} has been unbanned.** ✅", parse_mode=ParseMode.MARKDOWN)
                LOGGER.info(f"Unbanned user @{username} (ID: {target_user}) in chat {chat_id}")
            else:
                for target_user in target_users:
                    user_info = await app.get_users(target_user)
                    target_user_id = user_info.id
                    await app.unban_chat_member(chat_id, target_user_id)
                    username = user_info.username or user_info.first_name
                    await client.send_message(message.chat.id, f"**{username} has been unbanned.** ✅", parse_mode=ParseMode.MARKDOWN)
                    LOGGER.info(f"Unbanned user @{username} (ID: {target_user_id}) in chat {chat_id}")
        except UserNotParticipant:
            await handle_error(client, message, "User is not banned or not a member of this group.")
        except BadRequest as e:
            await handle_error(client, message, f"Failed to unban user: {str(e)}")
        except Exception as e:
            LOGGER.error(f"Error unbanning user in chat {chat_id}: {e}")
            await handle_error(client, message)

    @app.on_callback_query(filters.regex(r"^unban:(.*)"))
    async def callback_unban(client, callback_query):
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id if callback_query.from_user else None
        target_user = callback_query.data.split(":")[1]

        if user_id and not await is_admin(app, user_id, chat_id):
            await callback_query.answer("**✘ Kids Are Not Allowed To Do This  ↯**", show_alert=True)
            return

        try:
            await app.unban_chat_member(chat_id, target_user)
            user_info = await app.get_users(target_user)
            username = user_info.username or user_info.first_name
            await callback_query.message.edit_text(f"**{username} has been unbanned.** ✅", parse_mode=ParseMode.MARKDOWN)
            await callback_query.answer("User has been unbanned.")
            LOGGER.info(f"Unbanned user @{username} (ID: {target_user}) in chat {chat_id} via callback")
        except UserNotParticipant:
            await callback_query.answer("User is not banned or not a member.")
        except BadRequest as e:
            await callback_query.answer(f"Failed to unban user: {str(e)}", show_alert=True)
        except Exception as e:
            LOGGER.error(f"Error unbanning user via callback in chat {chat_id}: {e}")
            await callback_query.answer("Failed to unban user.", show_alert=True)

    @app.on_message(filters.command(["mute"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_mute(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(app, user_id, chat_id):
            await client.send_message(message.chat.id, "**✘ Kids Are Not Allowed To Do This  ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user.id
            reason = " ".join(message.command[1:]) or "No reason"
        else:
            target_users = [word for word in message.command[1:] if word.startswith('@')]
            reason = " ".join([word for word in message.command[1:] if not word.startswith('@')]) or "No reason"
            if not target_users:
                await client.send_message(message.chat.id, "**❌ Please specify the username or Reply To A User**", parse_mode=ParseMode.MARKDOWN)
                return

        try:
            if message.reply_to_message:
                await app.restrict_chat_member(chat_id, target_user, permissions=ChatPermissions(can_send_messages=False))
                user_info = await app.get_users(target_user)
                username = user_info.username or user_info.first_name
                await client.send_message(
                    message.chat.id,
                    f"**{username} has been muted for [{reason}].** ✅",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Unmute", callback_data=f"unmute:{target_user}")]]
                    ),
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.info(f"Muted user @{username} (ID: {target_user}) in chat {chat_id} for: {reason}")
            else:
                for target_user in target_users:
                    user_info = await app.get_users(target_user)
                    target_user_id = user_info.id
                    await app.restrict_chat_member(chat_id, target_user_id, permissions=ChatPermissions(can_send_messages=False))
                    username = user_info.username or user_info.first_name
                    await client.send_message(
                        message.chat.id,
                        f"**{username} has been muted for [{reason}].** ✅",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("Unmute", callback_data=f"unmute:{target_user_id}")]]
                        ),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    LOGGER.info(f"Muted user @{username} (ID: {target_user_id}) in chat {chat_id} for: {reason}")
        except UserNotParticipant:
            await handle_error(client, message, "User is not a member of this group.")
        except UserAdminInvalid:
            await handle_error(client, message, "Cannot mute an admin or the bot itself.")
        except BadRequest as e:
            await handle_error(client, message, f"Failed to mute user: {str(e)}")
        except Exception as e:
            LOGGER.error(f"Error muting user in chat {chat_id}: {e}")
            await handle_error(client, message)

    @app.on_message(filters.command(["unmute"], prefixes=COMMAND_PREFIX) & filters.group)
    async def handle_unmute(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None

        if user_id and not await is_admin(app, user_id, chat_id):
            await client.send_message(message.chat.id, "**✘ Kids Are Not Allowed To Do This  ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        if message.reply_to_message:
            target_user = message.reply_to_message.from_user.id
        else:
            target_users = [word for word in message.command[1:] if word.startswith('@')]
            if not target_users:
                await client.send_message(message.chat.id, "**❌ Please specify the username or Reply To A User**", parse_mode=ParseMode.MARKDOWN)
                return

        try:
            if message.reply_to_message:
                await app.restrict_chat_member(
                    chat_id, 
                    target_user, 
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
                user_info = await app.get_users(target_user)
                username = user_info.username or user_info.first_name
                await client.send_message(message.chat.id, f"**{username} has been unmuted.** ✅", parse_mode=ParseMode.MARKDOWN)
                LOGGER.info(f"Unmuted user @{username} (ID: {target_user}) in chat {chat_id}")
            else:
                for target_user in target_users:
                    user_info = await app.get_users(target_user)
                    target_user_id = user_info.id
                    await app.restrict_chat_member(
                        chat_id, 
                        target_user_id, 
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_polls=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True
                        )
                    )
                    username = user_info.username or user_info.first_name
                    await client.send_message(message.chat.id, f"**{username} has been unmuted.** ✅", parse_mode=ParseMode.MARKDOWN)
                    LOGGER.info(f"Unmuted user @{username} (ID: {target_user_id}) in chat {chat_id}")
        except UserNotParticipant:
            await handle_error(client, message, "User is not a member of this group.")
        except BadRequest as e:
            await handle_error(client, message, f"Failed to unmute user: {str(e)}")
        except Exception as e:
            LOGGER.error(f"Error unmuting user in chat {chat_id}: {e}")
            await handle_error(client, message)

    @app.on_callback_query(filters.regex(r"^unmute:(.*)"))
    async def callback_unmute(client, callback_query):
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id if callback_query.from_user else None
        target_user = callback_query.data.split(":")[1]

        if user_id and not await is_admin(app, user_id, chat_id):
            await callback_query.answer("**✘ Kids Are Not Allowed To Do This  ↯**", show_alert=True)
            return

        try:
            await app.restrict_chat_member(
                chat_id, 
                target_user, 
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True
                )
            )
            user_info = await app.get_users(target_user)
            username = user_info.username or user_info.first_name
            await callback_query.message.edit_text(f"**{username} has been unmuted.** ✅", parse_mode=ParseMode.MARKDOWN)
            await callback_query.answer("User has been unmuted.")
            LOGGER.info(f"Unmuted user @{username} (ID: {target_user}) in chat {chat_id} via callback")
        except UserNotParticipant:
            await callback_query.answer("User is not a member of this group.")
        except BadRequest as e:
            await callback_query.answer(f"Failed to unmute user: {str(e)}", show_alert=True)
        except Exception as e:
            LOGGER.error(f"Error unmuting user via callback in chat {chat_id}: {e}")
            await callback_query.answer("Failed to unmute user.", show_alert=True)
