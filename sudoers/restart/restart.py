# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# RESTART PLUGINS METHOD FROM https://github.com/abirxdhackz/RestartModule
import os
import shutil
import asyncio
import logging
import subprocess
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_IDS, UPDATE_CHANNEL_URL, COMMAND_PREFIX

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_session_permissions(session_file: str) -> bool:
    """Check if the session file is writable."""
    if not os.path.exists(session_file):
        logger.warning(f"Session file {session_file} does not exist")
        return True  # File doesn’t exist yet, so no permission issue
    if not os.access(session_file, os.W_OK):
        logger.error(f"Session file {session_file} is not writable")
        try:
            os.chmod(session_file, 0o600)  # Attempt to fix permissions
            logger.info(f"Fixed permissions for {session_file}")
            return os.access(session_file, os.W_OK)
        except Exception as e:
            logger.error(f"Failed to fix permissions for {session_file}: {e}")
            return False
    return True

def setup_restart_handler(app: Client):
    """Set up handlers for restart and stop commands."""
    logger.info("Setting up restart and stop handlers")

    @app.on_message(filters.command(["restart", "reboot", "reload"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def restart(client: Client, message):
        """Handle /restart, /reboot, /reload commands to restart the bot."""
        user_id = message.from_user.id
        logger.info(f"Restart command from user {user_id}")
        if user_id not in OWNER_IDS:
            logger.info("User not admin, sending restricted message")
            return await client.send_message(
                chat_id=message.chat.id,
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

        # Check session file permissions
        session_file = "SmartTools.session"
        if not check_session_permissions(session_file):
            return await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Bot Restart Error**",
                parse_mode=ParseMode.MARKDOWN
            )

        response = await client.send_message(
            chat_id=message.chat.id,
            text="**Restarting Your Bot Sir Please Wait ....**",
            parse_mode=ParseMode.MARKDOWN
        )

        # Clear directories
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

        # Delete the botlog.txt file if it exists
        log_file = "botlog.txt"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logger.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

        # Check if start.sh exists
        start_script = "start.sh"
        if not os.path.exists(start_script):
            logger.error("Start script not found")
            return await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**❌ Bot Restart Error**",
                parse_mode=ParseMode.MARKDOWN
            )

        try:
            # Wait for 4 seconds before editing the message
            await asyncio.sleep(4)
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**Bot Successfully Restarted!💥**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to edit restart message: {e}")
            return await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Bot Restart Error**",
                parse_mode=ParseMode.MARKDOWN
            )

        # Perform restart using subprocess
        try:
            subprocess.run(["bash", start_script], check=True)
            os._exit(0)  # Exit the current process after launching start.sh
        except Exception as e:
            logger.error(f"Failed to execute restart command: {e}")
            return await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Bot Restart Error**",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_message(filters.command(["stop", "kill", "off"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stop(client: Client, message):
        """Handle /stop, /kill, /off commands to stop the bot."""
        user_id = message.from_user.id
        logger.info(f"Stop command from user {user_id}")
        if user_id not in OWNER_IDS:
            logger.info("User not admin, sending restricted message")
            return await client.send_message(
                chat_id=message.chat.id,
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

        response = await client.send_message(
            chat_id=message.chat.id,
            text="**Stopping Bot and Clearing Database...**",
            parse_mode=ParseMode.MARKDOWN
        )

        # Clear directories
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

        # Delete the botlog.txt file
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
            return await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Failed To Stop Bot**",
                parse_mode=ParseMode.MARKDOWN
            )

        # Stop the bot process
        try:
            subprocess.run(["pkill", "-f", "main.py"], check=True)
            os._exit(0)  # Ensure process exits
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            return await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Failed To Stop Bot**",
                parse_mode=ParseMode.MARKDOWN
            )
