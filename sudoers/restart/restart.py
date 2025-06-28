# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# Restart Plugin From https://github.com/abirxdhackz/RestartModule
import os
import shutil
import asyncio
import subprocess
import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, UPDATE_CHANNEL_URL, COMMAND_PREFIX
from core import auth_admins
from utils import LOGGER

async def get_auth_admins():
    """Retrieve all authorized admins from MongoDB."""
    try:
        admins = await auth_admins.find({}, {"user_id": 1, "_id": 0}).to_list(None)
        return {admin["user_id"] for admin in admins}
    except Exception as e:
        logger.error(f"Error fetching auth admins: {e}")
        return set()

async def is_admin(user_id):
    """Check if the user is an admin (OWNER_ID or auth_admins)."""
    if user_id == OWNER_ID:  # Use direct comparison for single integer OWNER_ID
        return True
    auth_admin_ids = await get_auth_admins()
    return user_id in auth_admin_ids

def check_session_permissions(session_file: str) -> bool:
    """Check if the session file is writable."""
    if not os.path.exists(session_file):
        logger.warning(f"Session file {session_file} does not exist")
        return True
    if not os.access(session_file, os.W_OK):
        logger.error(f"Session file {session_file} is not writable")
        try:
            os.chmod(session_file, 0o600)
            logger.info(f"Fixed permissions for {session_file}")
            return os.access(session_file, os.W_OK)
        except Exception as e:
            logger.error(f"Failed to fix permissions for {session_file}: {e}")
            return False
    return True

def setup_restart_handler(app: Client):
    """Set up handlers for restart and stop commands."""

    @app.on_message(filters.command(["restart", "reboot", "reload"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def restart(client: Client, message):
        """Handle /restart, /reboot, /reload commands to restart the bot."""
        user_id = message.from_user.id
        logger.info(f"Restart command from user {user_id}")
        response = await client.send_message(
            chat_id=message.chat.id,
            text="**Restarting Your Bot Sir Please Wait ....**",
            parse_mode=ParseMode.MARKDOWN
        )

        if not await is_admin(user_id):
            logger.info("User not admin, editing message with restricted text")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**✘Kids Not Allowed To Do This↯**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👨🏼‍💻 Developer", url="https://t.me/abirxdhackz"),
                        InlineKeyboardButton("🤖 Other Bots", url=UPDATE_CHANNEL_URL)
                    ],
                    [
                        InlineKeyboardButton("🔗 Source Code", url="https://github.com/abirxdhackz/RestartModule"),
                        InlineKeyboardButton("🔔 Update News", url=UPDATE_CHANNEL_URL)
                    ]
                ])
            )

        session_file = "SmartTools.session"
        if not check_session_permissions(session_file):
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Bot Restart Failed**",
                parse_mode=ParseMode.MARKDOWN
            )

        directories = ["downloads", "temp", "temp_media", "data", "repos"]
        deleted_dirs = []
        failed_dirs = []
        for directory in directories:
            try:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
                    deleted_dirs.append(directory)
                    logger.info(f"Deleted directory: {directory}")
            except Exception as e:
                failed_dirs.append(directory)
                logger.error(f"Failed to delete directory {directory}: {e}")

        log_file = "botlog.txt"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logger.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

        start_script = "start.sh"
        if not os.path.exists(start_script):
            logger.error("Start script not found")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Bot Restart Failed**",
                parse_mode=ParseMode.MARKDOWN
            )

        try:
            await asyncio.sleep(4)
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**Bot Successfully Restarted!💥**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to edit restart message: {e}")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Bot Restart Failed**",
                parse_mode=ParseMode.MARKDOWN
            )

        try:
            subprocess.run(["bash", start_script], check=True)
            os._exit(0)
        except Exception as e:
            logger.error(f"Failed to execute restart command: {e}")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Bot Restart Failed**",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_message(filters.command(["stop", "kill", "off"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stop(client: Client, message):
        """Handle /stop, /kill, /off commands to stop the bot."""
        user_id = message.from_user.id
        logger.info(f"Stop command from user {user_id}")
        response = await client.send_message(
            chat_id=message.chat.id,
            text="**Stopping Bot and Clearing Database...**",
            parse_mode=ParseMode.MARKDOWN
        )

        if not await is_admin(user_id):
            logger.info("User not admin, editing message with restricted text")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**✘Kids Not Allowed To Do This↯**",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👨🏼‍💻 Developer", url="https://t.me/abirxdhackz"),
                        InlineKeyboardButton("🤖 Other Bots", url=UPDATE_CHANNEL_URL)
                    ],
                    [
                        InlineKeyboardButton("🔗 Source Code", url="https://github.com/abirxdhackz/RestartModule"),
                        InlineKeyboardButton("🔔 Update News", url=UPDATE_CHANNEL_URL)
                    ]
                ])
            )

        directories = ["downloads", "temp", "temp_media", "data", "repos"]
        deleted_dirs = []
        failed_dirs = []
        for directory in directories:
            try:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
                    deleted_dirs.append(directory)
                    logger.info(f"Deleted directory: {directory}")
            except Exception as e:
                failed_dirs.append(directory)
                logger.error(f"Failed to delete directory {directory}: {e}")

        log_file = "botlog.txt"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logger.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

        try:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**Bot Stopped Successfully, All Database Cleared**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to edit stop message: {e}")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Failed To Stop **",
                parse_mode=ParseMode.MARKDOWN
            )

        try:
            subprocess.run(["pkill", "-f", "main.py"], check=True)
            os._exit(0)
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Failed To Stop **",
                parse_mode=ParseMode.MARKDOWN
            )
