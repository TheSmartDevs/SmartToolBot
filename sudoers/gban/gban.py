#Copyright @ISmartCoder
#Updates Channel https://t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.errors import UserIdInvalid, UsernameInvalid, PeerIdInvalid
from config import OWNER_ID, COMMAND_PREFIX
from core import auth_admins, banned_users
from utils import LOGGER

def setup_gban_handler(app: Client):
    async def safe_send_message(client, chat_id, text):
        try:
            if chat_id and isinstance(chat_id, (int, str)):
                return await client.send_message(chat_id, text)
        except Exception as e:
            LOGGER.error(f"Failed to send message to {chat_id}: {e}")
        return None

    @app.on_message(filters.command(["gban"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gban_command(client, message):
        user_id = message.from_user.id
        try:
            auth_admins_data = await auth_admins.find({}, {"user_id": 1, "_id": 0}).to_list(None)
            AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        except Exception as e:
            LOGGER.error(f"Error fetching admins: {e}")
            return

        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            return

        if len(message.command) < 2 and not message.reply_to_message:
            await safe_send_message(client, message.chat.id, "**Please Provide A Valid User To Remove ❌**")
            return

        target_user = None
        target_identifier = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            target_identifier = target_user.id
        else:
            target_identifier = message.command[1]
            try:
                target_user = await client.get_users(int(target_identifier))
            except (ValueError, UserIdInvalid, PeerIdInvalid):
                try:
                    target_identifier = target_identifier.lstrip('@')
                    target_user = await client.get_users(target_identifier)
                except (UsernameInvalid, PeerIdInvalid) as e:
                    sent_message = await safe_send_message(client, message.chat.id, "**Removing User From Smart Tools**")
                    if sent_message:
                        await sent_message.edit("**Sorry Failed To Remove User From Bot ❌**")
                    LOGGER.error(f"Error resolving user {target_identifier}: {e}")
                    return

        if not target_user or not isinstance(target_user.id, int):
            sent_message = await safe_send_message(client, message.chat.id, "**Removing User From Smart Tools**")
            if sent_message:
                await sent_message.edit("**Sorry Failed To Remove User From Bot ❌**")
            LOGGER.error(f"Invalid target_user: {target_user}")
            return

        target_id = target_user.id
        target_name = target_user.first_name or str(target_id)
        profile_link = f"tg://user?id={target_id}"

        sent_message = await safe_send_message(client, message.chat.id, "**Removing User From Smart Tools**")

        try:
            if await banned_users.find_one({"user_id": target_id}):
                if sent_message:
                    await sent_message.edit("**Sorry Failed To Remove User From Bot ❌**")
                return
        except Exception as e:
            if sent_message:
                await sent_message.edit("**Sorry Failed To Remove User From Bot ❌**")
            LOGGER.error(f"Error checking ban status for {target_id}: {e}")
            return

        try:
            await banned_users.insert_one({"user_id": target_id, "username": target_name})
        except Exception as e:
            if sent_message:
                await sent_message.edit("**Sorry Failed To Remove User From Bot ❌**")
            LOGGER.error(f"Error banning user {target_id}: {e}")
            return

        await safe_send_message(client, target_id, "**Bad News, You're Banned From Using Me❌**")
        if sent_message:
            await sent_message.edit(f"**Successfully Removed [{target_name}]({profile_link}) From Smart Tools ✅**")
        
        for admin_id in [OWNER_ID] + AUTH_ADMIN_IDS:
            if admin_id != user_id and isinstance(admin_id, int):
                await safe_send_message(client, admin_id, f"**Successfully Removed [{target_name}]({profile_link}) From Smart Tools ✅**")

    @app.on_message(filters.command(["gunban"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def gunban_command(client, message):
        user_id = message.from_user.id
        try:
            auth_admins_data = await auth_admins.find({}, {"user_id": 1, "_id": 0}).to_list(None)
            AUTH_ADMIN_IDS = [admin["user_id"] for admin in auth_admins_data]
        except Exception as e:
            LOGGER.error(f"Error fetching admins: {e}")
            return

        if user_id != OWNER_ID and user_id not in AUTH_ADMIN_IDS:
            return

        if len(message.command) < 2 and not message.reply_to_message:
            await safe_send_message(client, message.chat.id, "**Please Provide A Valid User To Unban ❌**")
            return

        target_user = None
        target_identifier = None
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            target_identifier = target_user.id
        else:
            target_identifier = message.command[1]
            try:
                target_user = await client.get_users(int(target_identifier))
            except (ValueError, UserIdInvalid, PeerIdInvalid):
                try:
                    target_identifier = target_identifier.lstrip('@')
                    target_user = await client.get_users(target_identifier)
                except (UsernameInvalid, PeerIdInvalid) as e:
                    sent_message = await safe_send_message(client, message.chat.id, "**Unbanning User From Smart Tools**")
                    if sent_message:
                        await sent_message.edit("**Sorry Failed To Unban User From Bot ❌**")
                    LOGGER.error(f"Error resolving user {target_identifier}: {e}")
                    return

        if not target_user or not isinstance(target_user.id, int):
            sent_message = await safe_send_message(client, message.chat.id, "**Unbanning User From Smart Tools**")
            if sent_message:
                await sent_message.edit("**Sorry Failed To Unban User From Bot ❌**")
            LOGGER.error(f"Invalid target_user: {target_user}")
            return

        target_id = target_user.id
        target_name = target_user.first_name or str(target_id)
        profile_link = f"tg://user?id={target_id}"

        sent_message = await safe_send_message(client, message.chat.id, "**Unbanning User From Smart Tools**")

        try:
            if not await banned_users.find_one({"user_id": target_id}):
                if sent_message:
                    await sent_message.edit("**Sorry Failed To Unban User From Bot ❌**")
                return
        except Exception as e:
            if sent_message:
                await sent_message.edit("**Sorry Failed To Unban User From Bot ❌**")
            LOGGER.error(f"Error checking ban status for {target_id}: {e}")
            return

        try:
            await banned_users.delete_one({"user_id": target_id})
        except Exception as e:
            if sent_message:
                await sent_message.edit("**Sorry Failed To Unban User From Bot ❌**")
            LOGGER.error(f"Error unbanning user {target_id}: {e}")
            return

        await safe_send_message(client, target_id, "**Good News, You Can Now Use Me ✅**")
        if sent_message:
            await sent_message.edit(f"**Successfully Unbanned [{target_name}]({profile_link}) From Smart Tools ✅**")
        
        for admin_id in [OWNER_ID] + AUTH_ADMIN_IDS:
            if admin_id != user_id and isinstance(admin_id, int):
                await safe_send_message(client, admin_id, f"**Successfully Unbanned [{target_name}]({profile_link}) From Smart Tools ✅**")
