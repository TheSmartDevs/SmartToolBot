# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# Note This Script Based On https://github.com/abirxdhack/Mail-Scrapper
import re
import os
import aiofiles
import asyncio
from urllib.parse import urlparse
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from user import user
from pyrogram.errors import (
    UserAlreadyParticipant,
    InviteHashExpired,
    InviteHashInvalid,
    PeerIdInvalid,
    InviteRequestSent
)
from config import COMMAND_PREFIX, MAIL_SCR_LIMIT, SUDO_MAILSCR_LIMIT, OWNER_ID
from utils import LOGGER
from core import banned_users  # Check if user is banned

def filter_messages(message):
    LOGGER.info("Filtering message for email and password combinations")
    if message is None:
        LOGGER.warning("Message is None, returning empty list")
        return []

    pattern = r'(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b:\S+)'
    matches = re.findall(pattern, message)
    LOGGER.info(f"Found {len(matches)} matches in message")
    return matches

async def collect_channel_data(channel_identifier, amount):
    LOGGER.info(f"Collecting data from channel: {channel_identifier} with limit: {amount}")
    messages = []
    async for message in user.search_messages(channel_identifier, limit=amount):
        matches = filter_messages(message.text)
        if matches:
            messages.extend(matches)
            LOGGER.info(f"Collected {len(matches)} email-password combos from message")

        if len(messages) >= amount:
            LOGGER.info(f"Reached limit of {amount} messages, stopping collection")
            break

    unique_messages = list(set(messages))
    duplicates_removed = len(messages) - len(unique_messages)
    LOGGER.info(f"Total messages: {len(messages)}, Unique messages: {len(unique_messages)}, Duplicates removed: {duplicates_removed}")

    if not unique_messages:
        LOGGER.warning("No email and password combinations found")
        return [], 0, "<b>❌ No Email and Password Combinations were found</b>"

    return unique_messages[:amount], duplicates_removed, None

async def join_private_chat(client, invite_link):
    LOGGER.info(f"Attempting to join private chat: {invite_link}")
    try:
        await client.join_chat(invite_link)
        LOGGER.info(f"Successfully joined chat via invite link: {invite_link}")
        return True
    except UserAlreadyParticipant:
        LOGGER.info(f"Already a participant in the chat: {invite_link}")
        return True
    except InviteRequestSent:
        LOGGER.info(f"Join request sent to the chat: {invite_link}")
        return False
    except (InviteHashExpired, InviteHashInvalid) as e:
        LOGGER.error(f"Failed to join chat {invite_link}: {e}")
        return False

async def send_join_request(client, invite_link, message):
    LOGGER.info(f"Sending join request to chat: {invite_link}")
    try:
        await client.join_chat(invite_link)
        LOGGER.info(f"Join request sent successfully to chat: {invite_link}")
        await message.edit_text("<b>Hey Bro I Have Sent Join Request✅</b>", parse_mode=ParseMode.HTML)
        return True
    except PeerIdInvalid as e:
        LOGGER.error(f"Failed to send join request to chat {invite_link}: {e}")
        await message.edit_text("<b>Hey Bro Incorrect Invite Link ❌</b>", parse_mode=ParseMode.HTML)
        return False
    except InviteRequestSent:
        LOGGER.info(f"Join request sent to the chat: {invite_link}")
        await message.edit_text("<b>Hey Bro I Have Sent Join Request✅</b>", parse_mode=ParseMode.HTML)
        return False

def get_user_info(message):
    LOGGER.info("Retrieving user information")
    if message.from_user:
        user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        user_info = f"tg://user?id={message.from_user.id}"
        LOGGER.info(f"User info: {user_full_name}, {user_info}")
    else:
        user_full_name = message.chat.title or "this group"
        user_info = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
        LOGGER.info(f"Group info: {user_full_name}, {user_info}")
    return user_info, user_full_name

def setup_mailscr_handler(app):
    @app.on_message(filters.command(["scrmail", "mailscr"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def collect_handler(client, message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        LOGGER.info(f"Received command: {message.text}")
        args = message.text.split()
        if len(args) < 3:
            LOGGER.warning("Insufficient arguments provided")
            await client.send_message(message.chat.id, "<b>❌ Please provide a channel with amount</b>", parse_mode=ParseMode.HTML)
            return

        # Extract channel identifier (username, invite link, or chat ID)
        channel_identifier = args[1]
        try:
            amount = int(args[2])
        except ValueError:
            LOGGER.warning("Invalid amount provided")
            await client.send_message(message.chat.id, "<b>❌ Amount must be a number</b>", parse_mode=ParseMode.HTML)
            return

        # Determine limit based on user ID
        user_id = message.from_user.id if message.from_user else None
        limit = SUDO_MAILSCR_LIMIT if user_id in OWNER_ID else MAIL_SCR_LIMIT
        LOGGER.info(f"User ID: {user_id}, Applying limit: {limit}")

        # Check if requested amount exceeds limit
        if amount > limit:
            LOGGER.warning(f"Requested amount {amount} exceeds limit {limit} for user {user_id}")
            await client.send_message(message.chat.id, f"<b>❌ Amount exceeds limit of {limit}</b>", parse_mode=ParseMode.HTML)
            return

        chat = None
        channel_name = ""

        progress_message = await client.send_message(message.chat.id, "<b>Checking Username...</b>", parse_mode=ParseMode.HTML)
        LOGGER.info(f"Sent progress message: Checking Username...")

        # Handle t.me/username format
        if channel_identifier.startswith(("t.me/", "https://t.me/", "http://t.me/")):
            LOGGER.info(f"Processing t.me link: {channel_identifier}")
            # Prepend https:// if no scheme is present
            if not channel_identifier.startswith(("http://", "https://")):
                channel_identifier = "https://" + channel_identifier
            parsed_url = urlparse(channel_identifier)
            # Extract username by removing 't.me/' from the path
            channel_username = parsed_url.path.lstrip("/").replace("t.me/", "", 1)
            if channel_username.startswith("+"):
                # Handle private channel invite link
                invite_link = channel_identifier
                LOGGER.info(f"Detected private channel invite link: {invite_link}")
                joined = await join_private_chat(user, invite_link)
                if not joined:
                    LOGGER.info(f"Join not completed, sending join request for: {invite_link}")
                    request_sent = await send_join_request(user, invite_link, progress_message)
                    if not request_sent:
                        return
                else:
                    chat = await user.get_chat(invite_link)
                    channel_name = chat.title
                    LOGGER.info(f"Joined private channel: {channel_name}")
                    channel_identifier = chat.id
            else:
                # Handle public channel
                channel_username = f"@{channel_username}" if not channel_username.startswith("@") else channel_username
                LOGGER.info(f"Processing public channel username: {channel_username}")
                try:
                    chat = await user.get_chat(channel_username)
                    channel_name = chat.title
                    channel_identifier = channel_username
                    LOGGER.info(f"Successfully fetched public channel: {channel_name}")
                except Exception as e:
                    LOGGER.error(f"Failed to fetch public channel {channel_username}: {e}")
                    await progress_message.edit_text(f"<b>Hey Bro Incorrect Username ❌</b>", parse_mode=ParseMode.HTML)
                    return
        # Handle private channel chat ID (numeric)
        elif channel_identifier.lstrip("-").isdigit():
            # Treat it as a chat ID
            chat_id = int(channel_identifier)
            LOGGER.info(f"Processing chat ID: {chat_id}")
            try:
                # Fetch the chat details
                chat = await user.get_chat(chat_id)
                channel_name = chat.title
                LOGGER.info(f"Successfully fetched private channel: {channel_name} (ID: {chat_id})")
            except Exception as e:
                LOGGER.error(f"Failed to fetch private channel {chat_id}: {e}")
                await progress_message.edit_text("<b>Hey Bro Incorrect ChatId ❌</b>", parse_mode=ParseMode.HTML)
                return
        else:
            # Handle public channels (username or @username)
            channel_username = channel_identifier
            if not channel_username.startswith("@"):
                channel_username = f"@{channel_username}"
            LOGGER.info(f"Processing public channel username: {channel_username}")
            try:
                chat = await user.get_chat(channel_username)
                channel_name = chat.title
                channel_identifier = channel_username
                LOGGER.info(f"Successfully fetched public channel: {channel_name}")
            except Exception as e:
                LOGGER.error(f"Failed to fetch channel {channel_username}: {e}")
                await progress_message.edit_text("<b>Hey Bro Incorrect Username ❌</b>", parse_mode=ParseMode.HTML)
                return

        await progress_message.edit_text("<b>Scraping In Progress</b>", parse_mode=ParseMode.HTML)
        LOGGER.info("Updated progress message: Scraping In Progress")

        messages, duplicates_removed, error_msg = await collect_channel_data(channel_identifier, amount)

        if error_msg:
            LOGGER.error(f"Error during data collection: {error_msg}")
            await progress_message.edit_text(error_msg, parse_mode=ParseMode.HTML)
            return

        if not messages:
            LOGGER.warning("No email-password combos found")
            await progress_message.edit_text("<b>Sorry Bro ❌ No Mail Pass Found</b>", parse_mode=ParseMode.HTML)
            return

        file_path = f'{channel_identifier}_combos.txt'
        LOGGER.info(f"Writing {len(messages)} combos to file: {file_path}")
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
            for combo in messages:
                try:
                    await file.write(f"{combo}\n")
                except UnicodeEncodeError:
                    LOGGER.warning(f"Skipped combo due to UnicodeEncodeError: {combo}")
                    continue

        user_info, user_full_name = get_user_info(message)
        output_message = (f"<b>Mail Scraped Successful ✅</b>\n"
                          f"<b>━━━━━━━━━━━━━━━━</b>\n"
                          f"<b>Source:</b> <code>{channel_name} 🌐</code>\n"
                          f"<b>Amount:</b> <code>{len(messages)} 📝</code>\n"
                          f"<b>Duplicates Removed:</b> <code>{duplicates_removed} 🗑️</code>\n"
                          f"<b>━━━━━━━━━━━━━━━━</b>\n"
                          f"<b>Scrapped By:</b> <a href='{user_info}'>{user_full_name}</a>")
        LOGGER.info(f"Sending document with caption: {output_message}")
        await client.send_document(message.chat.id, file_path, caption=output_message, parse_mode=ParseMode.HTML)

        LOGGER.info(f"Removing temporary file: {file_path}")
        os.remove(file_path)
        LOGGER.info("Deleting progress message")
        await progress_message.delete()
