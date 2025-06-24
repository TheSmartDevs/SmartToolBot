# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.errors import UserIdInvalid, UsernameInvalid, PeerIdInvalid
from config import OWNER_ID, COMMAND_PREFIX
from core import auth_admins, banned_users
from utils import LOGGER

def setup_gban_handler(app: Client):
    async def safe_send_message(client, chat_id, text):
        try:
            if chat_id and isinstance(chat_id, (int, str)):
                await client.send_message(chat_id, text)
        except Exception as e:
            LOGGER.error(f"Failed to send message to {chat_id}: {e}")

    @app.on_message(filters.command(["gban"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gban_command(client, message):
        user_id = message.from_user.id
        try:
            auth_admins_data = await auth_admins.find({}, {"user_id": 1, "_id": 0}).to_list(None)
            AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        except Exception as e:
            await safe_send_message(client, message.chat.id, "**✘Error: Failed to fetch admin data↯**")
            LOGGER.error(f"Error fetching admins: {e}")
            return

        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            await safe_send_message(client, message.chat.id, "**✘Kids Not Allowed To Do This↯**")
            LOGGER.info(f"Unauthorized gban attempt by user {user_id}")
            return

        # Check if a user is specified
        if len(message.command) < 2 and not message.reply_to_message:
            await safe_send_message(client, message.chat.id, "**✘Please Specify User To Ban Forever↯**")
            return

        # Get target user
        target_user = None
        target_identifier = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            target_identifier = target_user.id
        else:
            target_identifier = message.command[1]
            try:
                # Try to resolve as user ID first
                target_user = await client.get_users(int(target_identifier))
            except (ValueError, UserIdInvalid, PeerIdInvalid):
                try:
                    # If not a valid user ID, try as username
                    target_identifier = target_identifier.lstrip('@')
                    target_user = await client.get_users(target_identifier)
                except (UsernameInvalid, PeerIdInvalid) as e:
                    await safe_send_message(client, message.chat.id, "**✘Error: Invalid User ID/Username↯**")
                    LOGGER.error(f"Error resolving user {target_identifier}: {e}")
                    return

        if not target_user or not isinstance(target_user.id, int):
            await safe_send_message(client, message.chat.id, "**✘Error: Invalid target user↯**")
            LOGGER.error(f"Invalid target_user: {target_user}")
            return

        target_id = target_user.id
        target_name = target_user.username or target_user.first_name or str(target_id)

        # Check if user is already banned
        try:
            if await banned_users.find_one({"user_id": target_id}):
                await safe_send_message(client, message.chat.id, f"**✘User {target_name} is already banned↯**")
                return
        except Exception as e:
            await safe_send_message(client, message.chat.id, "**✘Error: Failed to check ban status↯**")
            LOGGER.error(f"Error checking ban status for {target_id}: {e}")
            return

        # Ban the user
        try:
            await banned_users.insert_one({"user_id": target_id, "username": target_name})
        except Exception as e:
            await safe_send_message(client, message.chat.id, "**✘Error: Failed to ban user↯**")
            LOGGER.error(f"Error banning user {target_id}: {e}")
            return

        # Notify the banned user
        await safe_send_message(client, target_id, "**✘Bro You're Banned Forever↯**")

        # Notify owner and admins
        await safe_send_message(client, message.chat.id, f"**✘Successfully Banned {target_name}↯**")
        for admin_id in [OWNER_ID] + AUTH_ADMIN_IDS:
            if admin_id != user_id and isinstance(admin_id, int):
                await safe_send_message(client, admin_id, f"**✘Successfully Banned {target_name}↯**")

    @app.on_message(filters.command(["gunban"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gunban_command(client, message):
        user_id = message.from_user.id
        try:
            auth_admins_data = await auth_admins.find({}, {"user_id": 1, "_id": 0}).to_list(None)
            AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        except Exception as e:
            await safe_send_message(client, message.chat.id, "**✘Error: Failed to fetch admin data↯**")
            LOGGER.error(f"Error fetching admins: {e}")
            return

        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            await safe_send_message(client, message.chat.id, "**✘Kids Not Allowed To Do This↯**")
            LOGGER.info(f"Unauthorized gunban attempt by user {user_id}")
            return

        # Check if a user is specified
        if len(message.command) < 2 and not message.reply_to_message:
            await safe_send_message(client, message.chat.id, "**✘Please Specify User To UnBan ↯**")
            return

        # Get target user
        target_user = None
        target_identifier = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            target_identifier = target_user.id
        else:
            target_identifier = message.command[1]
            try:
                # Try to resolve as user ID first
                target_user = await client.get_users(int(target_identifier))
            except (ValueError, UserIdInvalid, PeerIdInvalid):
                try:
                    # If not a valid user ID, try as username
                    target_identifier = target_identifier.lstrip('@')
                    target_user = await client.get_users(target_identifier)
                except (UsernameInvalid, PeerIdInvalid) as e:
                    await safe_send_message(client, message.chat.id, "**✘Error: Invalid User ID/Username↯**")
                    LOGGER.error(f"Error resolving user {target_identifier}: {e}")
                    return

        if not target_user or not isinstance(target_user.id, int):
            await safe_send_message(client, message.chat.id, "**✘Error: Invalid target user↯**")
            LOGGER.error(f"Invalid target_user: {target_user}")
            return

        target_id = target_user.id
        target_name = target_user.username or target_user.first_name or str(target_id)

        # Check if user is banned
        try:
            if not await banned_users.find_one({"user_id": target_id}):
                await safe_send_message(client, message.chat.id, f"**✘User {target_name} is not banned↯**")
                return
        except Exception as e:
            await safe_send_message(client, message.chat.id, "**✘Error: Failed to check ban status↯**")
            LOGGER.error(f"Error checking ban status for {target_id}: {e}")
            return

        # Unban the user
        try:
            await banned_users.delete_one({"user_id": target_id})
        except Exception as e:
            await safe_send_message(client, message.chat.id, "**✘Error: Failed to unban user↯**")
            LOGGER.error(f"Error unbanning user {target_id}: {e}")
            return

        # Notify the unbanned user
        await safe_send_message(client, target_id, "**✘Bro You're Unbanned↯**")

        # Notify owner and admins
        await safe_send_message(client, message.chat.id, f"**✘Successfully Unbanned {target_name}↯**")
        for admin_id in [OWNER_ID] + AUTH_ADMIN_IDS:
            if admin_id != user_id and isinstance(admin_id, int):
                await safe_send_message(client, admin_id, f"**✘Successfully Unbanned {target_name}↯**")
