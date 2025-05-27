# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.errors import UserIdInvalid, UsernameInvalid, PeerIdInvalid
from config import OWNER_ID, COMMAND_PREFIX
from core import auth_admins, banned_users
from utils import LOGGER

def setup_gban_handler(app: Client):
    @app.on_message(filters.command(["gban"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gban_command(client, message):
        user_id = message.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]

        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            sent_message = await client.send_message(message.chat.id, "**✘Kids Not Allowed To Do This↯**")
            LOGGER.info(f"Unauthorized gban attempt by user {user_id}")
            return

        # Check if a user is specified
        if len(message.command) < 2 and not message.reply_to_message:
            sent_message = await client.send_message(message.chat.id, "**✘Please Specify User To Ban Forever↯**")
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
                    sent_message = await client.send_message(message.chat.id, "**✘Error: Invalid User ID/Username↯**")
                    LOGGER.error(f"Error resolving user {target_identifier}: {e}")
                    return

        target_id = target_user.id
        target_name = target_user.username or target_user.first_name or str(target_id)

        # Check if user is already banned
        if banned_users.find_one({"user_id": target_id}):
            sent_message = await client.send_message(message.chat.id, f"**✘User {target_name} is already banned↯**")
            return

        # Ban the user
        banned_users.insert_one({"user_id": target_id, "username": target_name})
        
        # Notify the banned user
        try:
            await client.send_message(target_id, "**✘Bro You're Banned Forever↯**")
        except Exception as e:
            LOGGER.error(f"Failed to notify banned user {target_id}: {e}")

        # Notify owner and admins
        sent_message = await client.send_message(message.chat.id, f"**✘Successfully Banned {target_name}↯**")
        for admin_id in [OWNER_ID] + AUTH_ADMIN_IDS:
            if admin_id != user_id:
                try:
                    await client.send_message(admin_id, f"**✘Successfully Banned {target_name}↯**")
                except Exception as e:
                    LOGGER.error(f"Failed to notify admin {admin_id}: {e}")

    @app.on_message(filters.command(["gunban"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gunban_command(client, message):
        user_id = message.from_user.id
        auth_admins_data = auth_admins.find({}, {"user_id": 1, "_id": 0})
        AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]

        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            sent_message = await client.send_message(message.chat.id, "**✘Kids Not Allowed To Do This↯**")
            LOGGER.info(f"Unauthorized gunban attempt by user {user_id}")
            return

        # Check if a user is specified
        if len(message.command) < 2 and not message.reply_to_message:
            sent_message = await client.send_message(message.chat.id, "**✘Please Specify User To UnBan ↯**")
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
                    sent_message = await client.send_message(message.chat.id, "**✘Error: Invalid User ID/Username↯**")
                    LOGGER.error(f"Error resolving user {target_identifier}: {e}")
                    return

        target_id = target_user.id
        target_name = target_user.username or target_user.first_name or str(target_id)

        # Check if user is banned
        if not banned_users.find_one({"user_id": target_id}):
            sent_message = await client.send_message(message.chat.id, f"**✘User {target_name} is not banned↯**")
            return

        # Unban the user
        banned_users.delete_one({"user_id": target_id})
        
        # Notify the unbanned user
        try:
            await client.send_message(target_id, "**✘Bro You're Unbanned↯**")
        except Exception as e:
            LOGGER.error(f"Failed to notify unbanned user {target_id}: {e}")

        # Notify owner and admins
        sent_message = await client.send_message(message.chat.id, f"**✘Successfully Unbanned {target_name}↯**")
        for admin_id in [OWNER_ID] + AUTH_ADMIN_IDS:
            if admin_id != user_id:
                try:
                    await client.send_message(admin_id, f"**✘Successfully Unbanned {target_name}↯**")
                except Exception as e:
                    LOGGER.error(f"Failed to notify admin {admin_id}: {e}")
