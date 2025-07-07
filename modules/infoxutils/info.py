# Copyright @ISmartCoder
# Updates Channel t.me/TheSmartDev

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode, ChatType, UserStatus
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied, ChannelInvalid
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, get_dc_locations
from core import banned_users

logger = LOGGER

def calculate_account_age(creation_date):
    today = datetime.now()
    delta = relativedelta(today, creation_date)
    years = delta.years
    months = delta.months
    days = delta.days
    return f"{years} years, {months} months, {days} days"

def estimate_account_creation_date(user_id):
    reference_points = [
        (100000000, datetime(2013, 8, 1)),
        (1273841502, datetime(2020, 8, 13)),
        (1500000000, datetime(2021, 5, 1)),
        (2000000000, datetime(2022, 12, 1)),
    ]
    
    closest_point = min(reference_points, key=lambda x: abs(x[0] - user_id))
    closest_user_id, closest_date = closest_point
    
    id_difference = user_id - closest_user_id
    days_difference = id_difference / 20000000
    creation_date = closest_date + timedelta(days=days_difference)
    
    return creation_date

def setup_info_handler(app):
    @app.on_message(filters.command(["info", "id"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_info_command(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            return

        logger.info("Received /info or /id command")
        try:
            DC_LOCATIONS = get_dc_locations()
            
            progress_message = await client.send_message(message.chat.id, "**✨ Smart Tools Fetching Info From Database 💥**")
            try:
                if not message.command or (len(message.command) == 1 and not message.reply_to_message):
                    logger.info("Fetching current user info")
                    user = message.from_user
                    chat = message.chat
                    premium_status = "Yes" if user.is_premium else "No"
                    dc_location = DC_LOCATIONS.get(user.dc_id, "Unknown")
                    account_created = estimate_account_creation_date(user.id)
                    account_created_str = account_created.strftime("%B %d, %Y")
                    account_age = calculate_account_age(account_created)
                    
                    verified_status = "Verified" if getattr(user, 'is_verified', False) else "Not Verified"
                    
                    status = "⚪️ Unknown"
                    if user.status:
                        if user.status == UserStatus.ONLINE:
                            status = "Online"
                        elif user.status == UserStatus.OFFLINE:
                            status = "Offline"
                        elif user.status == UserStatus.RECENTLY:
                            status = "Recently online"
                        elif user.status == UserStatus.LAST_WEEK:
                            status = "Last seen within week"
                        elif user.status == UserStatus.LAST_MONTH:
                            status = "Last seen within month"
                    
                    chat_id_display = chat.id if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else user.id
                    response = (
                        "**Smart User Info Extract Completed ✅**\n"
                        "**━━━━━━━━━━━━━━━━━**\n"
                        f"**⊗ Full Name:** {user.first_name} {user.last_name or ''}\n"
                        f"**⊗ UserID:** `{user.id}`\n"
                        f"**⊗ Username:** @{user.username if user.username else 'None'}\n"
                        f"**⊗ ChatID:** `{chat_id_display}`\n"
                        f"**⊗ Data Center:** {user.dc_id} ({dc_location})\n"
                        f"**⊗ Premium:** {premium_status}\n"
                        f"**⊗ Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                        f"**⊗ Verification:** {verified_status}\n"
                        f"**⊗ Status:** {status}\n"
                        f"**⊗ Account Created On:** {account_created_str}\n"
                        f"**⊗ Account Age:** {account_age}\n"
                        "**━━━━━━━━━━━━━━━━━**\n"
                        "**Use Below Buttons For Profile View ✅**"
                    )
                    buttons = [
                        [InlineKeyboardButton("Android Link", url=f"tg://openmessage?user_id={user.id}"), InlineKeyboardButton("IOS Link", url=f"tg://user?id={user.id}")],
                        [InlineKeyboardButton("Permanent Link", user_id=user.id)],
                    ]
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=progress_message.id,
                        text=response,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    logger.info("User info fetched successfully with buttons")
                elif message.reply_to_message:
                    logger.info("Fetching info of the replied user or bot")
                    user = message.reply_to_message.from_user
                    chat = message.chat
                    premium_status = "Yes" if user.is_premium else "No"
                    dc_location = DC_LOCATIONS.get(user.dc_id, "Unknown")
                    account_created = estimate_account_creation_date(user.id)
                    account_created_str = account_created.strftime("%B %d, %Y")
                    account_age = calculate_account_age(account_created)
                    
                    verified_status = "Verified" if getattr(user, 'is_verified', False) else "Not Verified"
                    
                    status = "⚪️ Unknown"
                    if user.status:
                        if user.status == UserStatus.ONLINE:
                            status = "Online"
                        elif user.status == UserStatus.OFFLINE:
                            status = "Offline"
                        elif user.status == UserStatus.RECENTLY:
                            status = "Recently online"
                        elif user.status == UserStatus.LAST_WEEK:
                            status = "Last seen within week"
                        elif user.status == UserStatus.LAST_MONTH:
                            status = "Last seen within month"
                    
                    chat_id_display = chat.id if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else user.id
                    response = (
                        "**Smart User Info Extract Completed ✅**\n"
                        "**━━━━━━━━━━━━━━━━━**\n"
                        f"**⊗ Full Name:** {user.first_name} {user.last_name or ''}\n"
                        f"**⊗ UserID:** `{user.id}`\n"
                        f"**⊗ Username:** @{user.username if user.username else 'None'}\n"
                        f"**⊗ ChatID:** `{chat_id_display}`\n"
                        f"**⊗ Data Center:** {user.dc_id} ({dc_location})\n"
                        f"**⊗ Premium:** {premium_status}\n"
                        f"**⊗ Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                        f"**⊗ Verification:** {verified_status}\n"
                        f"**⊗ Status:** {status}\n"
                        f"**⊗ Account Created On:** {account_created_str}\n"
                        f"**⊗ Account Age:** {account_age}\n"
                        "**━━━━━━━━━━━━━━━━━**\n"
                        "**Use Below Buttons For Profile View ✅**"
                    )
                    if user.is_bot:
                        response = (
                            "**Smart Bot Info Extract Completed ✅**\n"
                            "**━━━━━━━━━━━━━━━━━**\n"
                            f"**⊗ Bot Name:** {user.first_name} {user.last_name or ''}\n"
                            f"**⊗ BotID:** `{user.id}`\n"
                            f"**⊗ Username:** @{user.username if user.username else 'None'}\n"
                            f"**⊗ ChatID:** `{chat_id_display}`\n"
                            f"**⊗ Data Center:** {user.dc_id} ({dc_location})\n"
                            f"**⊗ Premium:** {premium_status}\n"
                            f"**⊗ Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                            f"**⊗ Verification:** {verified_status}\n"
                            f"**⊗ Status:** {status}\n"
                            "**━━━━━━━━━━━━━━━━━**\n"
                            "**Use Below Buttons For Profile View ✅**"
                        )
                    buttons = [
                        [InlineKeyboardButton("Android Link", url=f"tg://openmessage?user_id={user.id}"), InlineKeyboardButton("IOS Link", url=f"tg://user?id={user.id}")],
                        [InlineKeyboardButton("Permanent Link", user_id=user.id)],
                    ]
                    await client.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=progress_message.id,
                        text=response,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    logger.info("Replied user info fetched successfully")
                elif len(message.command) > 1:
                    logger.info("Extracting username from the command")
                    username = message.command[1].strip('@').replace('https://', '').replace('http://', '').replace('t.me/', '').replace('/', '').replace(':', '')

                    try:
                        logger.info(f"Fetching info for user or bot: {username}")
                        user = await client.get_users(username)
                        premium_status = "Yes" if user.is_premium else "No"
                        dc_location = DC_LOCATIONS.get(user.dc_id, "Unknown")
                        account_created = estimate_account_creation_date(user.id)
                        account_created_str = account_created.strftime("%B %d, %Y")
                        account_age = calculate_account_age(account_created)
                        
                        verified_status = "Verified" if user.is_verified else "Not Verified"
                        
                        status = "⚪️ Unknown"
                        if user.status:
                            if user.status == UserStatus.ONLINE:
                                status = "Online"
                            elif user.status == UserStatus.OFFLINE:
                                status = "Offline"
                            elif user.status == UserStatus.RECENTLY:
                                status = "Recently online"
                            elif user.status == UserStatus.LAST_WEEK:
                                status = "Last seen within week"
                            elif user.status == UserStatus.LAST_MONTH:
                                status = "Last seen within month"
                        
                        response = (
                            "**Smart User Info Extract Completed ✅**\n"
                            "**━━━━━━━━━━━━━━━━━**\n"
                            f"**⊗ Full Name:** {user.first_name} {user.last_name or ''}\n"
                            f"**⊗ UserID:** `{user.id}`\n"
                            f"**⊗ Username:** @{user.username if user.username else 'None'}\n"
                            f"**⊗ ChatID:** `{user.id}`\n"
                            f"**⊗ Data Center:** {user.dc_id} ({dc_location})\n"
                            f"**⊗ Premium:** {premium_status}\n"
                            f"**⊗ Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                            f"**⊗ Verification:** {verified_status}\n"
                            f"**⊗ Status:** {status}\n"
                            f"**⊗ Account Created On:** {account_created_str}\n"
                            f"**⊗ Account Age:** {account_age}\n"
                            "**━━━━━━━━━━━━━━━━━**\n"
                            "**Use Below Buttons For Profile View ✅**"
                        )
                        if user.is_bot:
                            response = (
                                "**Smart Bot Info Extract Completed ✅**\n"
                                "**━━━━━━━━━━━━━━━━━**\n"
                                f"**⊗ Bot Name:** {user.first_name} {user.last_name or ''}\n"
                                f"**⊗ BotID:** `{user.id}`\n"
                                f"**⊗ Username:** @{user.username if user.username else 'None'}\n"
                                f"**⊗ ChatID:** `{user.id}`\n"
                                f"**⊗ Data Center:** {user.dc_id} ({dc_location})\n"
                                f"**⊗ Premium:** {premium_status}\n"
                                f"**⊗ Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                                f"**⊗ Verification:** {verified_status}\n"
                                f"**⊗ Status:** {status}\n"
                                "**━━━━━━━━━━━━━━━━━**\n"
                                "**Use Below Buttons For Profile View ✅**"
                            )
                        buttons = [
                            [InlineKeyboardButton("Android Link", url=f"tg://openmessage?user_id={user.id}"), InlineKeyboardButton("IOS Link", url=f"tg://user?id={user.id}")],
                            [InlineKeyboardButton("Permanent Link", user_id=user.id)],
                        ]
                        await client.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=progress_message.id,
                            text=response,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup(buttons)
                        )
                        logger.info("User/bot info fetched successfully with buttons")
                    except (PeerIdInvalid, UsernameNotOccupied, IndexError):
                        logger.info(f"Username '{username}' not found as a user/bot. Checking for chat...")
                        try:
                            chat = await client.get_chat(username)
                            dc_location = DC_LOCATIONS.get(chat.dc_id, "Unknown")
                            chat_type = "Channel" if chat.type == ChatType.CHANNEL else "Supergroup" if chat.type == ChatType.SUPERGROUP else "Group"
                            response = (
                                f"**Smart {chat_type} Info Extract Completed ✅**\n"
                                "**━━━━━━━━━━━━━━━━━**\n"
                                f"**⊗ Name:** {chat.title}\n"
                                f"**⊗ ChatID:** `{chat.id}`\n"
                                f"**⊗ Type:** {chat_type}\n"
                                f"**⊗ Total Members:** {chat.members_count if chat.members_count else 'Unknown'}\n"
                                "**━━━━━━━━━━━━━━━━━**\n"
                                "**Use Below Buttons For Visiting Chat ✅**"
                            )
                            buttons = [
                                [InlineKeyboardButton(f"Join This {chat_type}", url=f"t.me/c/{str(chat.id).replace('-100', '')}/100"), InlineKeyboardButton("Permanent Link", url=f"t.me/c/{str(chat.id).replace('-100', '')}/100")],
                            ]
                            await client.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=progress_message.id,
                                text=response,
                                parse_mode=ParseMode.MARKDOWN,
                                reply_markup=InlineKeyboardMarkup(buttons)
                            )
                            logger.info("Chat info fetched successfully with buttons")
                        except (ChannelInvalid, PeerIdInvalid):
                            error_message = (
                                "**Looks Like I Don't Have Control Over The Channel**"
                                if chat.type == ChatType.CHANNEL
                                else "**Looks Like I Don't Have Control Over The Group**"
                            )
                            await client.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=progress_message.id,
                                text=error_message,
                                parse_mode=ParseMode.MARKDOWN
                            )
                            logger.error(f"Permission error: {error_message}")
                        except Exception as e:
                            logger.error(f"Error fetching chat info: {str(e)}")
                            await client.edit_message_text(
                                chat_id=message.chat.id,
                                message_id=progress_message.id,
                                text="**Looks Like I Don't Have Control Over The Group**",
                                parse_mode=ParseMode.MARKDOWN
                            )
                    except Exception as e:
                        logger.error(f"Error fetching user or bot info: {str(e)}")
                        await client.edit_message_text(
                            chat_id=message.chat.id,
                            message_id=progress_message.id,
                            text="**Looks Like I Don't Have Control Over The User**",
                            parse_mode=ParseMode.MARKDOWN
                        )
            except Exception as e:
                logger.error(f"Unhandled exception: {str(e)}")
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=progress_message.id,
                    text="**Looks Like I Don't Have Control Over The User**",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            await client.send_message(
                chat_id=message.chat.id,
                text="**Looks Like I Don't Have Control Over The User**",
                parse_mode=ParseMode.MARKDOWN
            )
