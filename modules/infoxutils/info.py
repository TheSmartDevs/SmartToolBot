# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode, ChatType, UserStatus
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied, ChannelInvalid
from config import COMMAND_PREFIX
from utils import LOGGER, get_dc_locations  # Use LOGGER from utils
from core import banned_users  # Check if user is banned

# Use the imported LOGGER
logger = LOGGER

# Function to calculate account age accurately
def calculate_account_age(creation_date):
    today = datetime.now()
    delta = relativedelta(today, creation_date)
    years = delta.years
    months = delta.months
    days = delta.days
    return f"{years} years, {months} months, {days} days"

# Function to estimate account creation date based on user ID
def estimate_account_creation_date(user_id):
    # Known reference points for user IDs and their creation dates
    reference_points = [
        (100000000, datetime(2013, 8, 1)),  # Telegram's launch date
        (1273841502, datetime(2020, 8, 13)),  # Example reference point
        (1500000000, datetime(2021, 5, 1)),  # Another reference point
        (2000000000, datetime(2022, 12, 1)),  # Another reference point
    ]
    
    # Find the closest reference point
    closest_point = min(reference_points, key=lambda x: abs(x[0] - user_id))
    closest_user_id, closest_date = closest_point
    
    # Calculate the difference in user IDs
    id_difference = user_id - closest_user_id
    
    # Estimate the creation date based on the difference
    # Assuming 20,000,000 user IDs are created per day (adjusted for estimation)
    days_difference = id_difference / 20000000
    creation_date = closest_date + timedelta(days=days_difference)
    
    return creation_date

def setup_info_handler(app):
    @app.on_message(filters.command(["info", "id"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def handle_info_command(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘ Sorry You're Banned From Using Me ↯**")
            return

        logger.info("Received /info or /id command")
        try:
            # Get DC locations data from imported function
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
                    
                    # Added verification and status
                    verified_status = "Yes" if getattr(user, 'is_verified', False) else "No"
                    
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
                        "✘《 **User Information** ↯ 》\n"
                        f"↯ **Full Name:** {user.first_name} {user.last_name or ''}\n"
                        f"↯ **User ID:** `{user.id}`\n"
                        f"↯ **Username:** @{user.username if user.username else 'None'}\n"
                        f"↯ **Chat Id:** `{chat.id}`\n"
                        f"↯ **Data Center:** {user.dc_id} ({dc_location})\n"
                        f"↯ **Premium User:** {premium_status}\n"
                        f"↯ **Verified:** {verified_status}\n"
                        f"↯ **Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else 'Clean'}\n"
                        f"↯ **Status:** {status}\n"
                        f"↯ **Account Created On:** {account_created_str}\n"
                        f"↯ **Account Age:** {account_age}"
                    )
                    buttons = [
                        [InlineKeyboardButton("✘ Android Link ↯", url=f"tg://openmessage?user_id={user.id}"), InlineKeyboardButton("✘ iOS Link ↯", url=f"tg://user?id={user.id}")],
                        [InlineKeyboardButton("✘ Permanent Link ↯", user_id=user.id)],
                    ]
                    await client.send_message(chat_id=message.chat.id, text=response, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
                    logger.info("User info fetched successfully with buttons")
                elif message.reply_to_message:
                    # Show info of the replied user or bot
                    logger.info("Fetching info of the replied user or bot")
                    user = message.reply_to_message.from_user
                    chat = message.chat
                    premium_status = "Yes" if user.is_premium else "No"
                    dc_location = DC_LOCATIONS.get(user.dc_id, "Unknown")
                    account_created = estimate_account_creation_date(user.id)
                    account_created_str = account_created.strftime("%B %d, %Y")
                    account_age = calculate_account_age(account_created)
                    
                    # Added verification and status
                    verified_status = "Yes" if getattr(user, 'is_verified', False) else "No"
                    
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
                        "✘《 **User Information** ↯ 》\n"
                        f"↯ **Full Name:** {user.first_name} {user.last_name or ''}\n"
                        f"↯ **User ID:** `{user.id}`\n"
                        f"↯ **Username:** @{user.username if user.username else 'None'}\n"
                        f"↯ **Chat Id:** `{chat.id}`\n"
                        f"↯ **Data Center:** {user.dc_id} ({dc_location})\n"
                        f"↯ **Premium User:** {premium_status}\n"
                        f"↯ **Verified:** {verified_status}\n"
                        f"↯ **Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else 'Clean'}\n"
                        f"↯ **Status:** {status}\n"
                        f"↯ **Account Created On:** {account_created_str}\n"
                        f"↯ **Account Age:** {account_age}"
                    )
                    if user.is_bot:
                        response = (
                            "✘《 **Bot Information** ↯ 》\n"
                            f"↯ **Bot Name:** {user.first_name} {user.last_name or ''}\n"
                            f"↯ **Bot ID:** `{user.id}`\n"
                            f"↯ **Username:** @{user.username if user.username else 'None'}\n"
                            f"↯ **Data Center:** {user.dc_id} ({dc_location})\n"
                            f"↯ **Premium User:** {premium_status}\n"
                            f"↯ **Verified:** {verified_status}\n"
                            f"↯ **Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else 'Clean'}\n"
                            f"↯ **Account Created On:** {account_created_str}\n"
                            f"↯ **Account Age:** {account_age}"
                        )
                    buttons = [
                        [InlineKeyboardButton("✘ Android Link ↯", url=f"tg://openmessage?user_id={user.id}"), InlineKeyboardButton("✘ iOS Link ↯", url=f"tg://user?id={user.id}")],
                        [InlineKeyboardButton("✘ Permanent Link ↯", user_id=user.id)],
                    ]
                    await client.send_message(chat_id=message.chat.id, text=response, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
                    logger.info("Replied user info fetched successfully")
                elif len(message.command) > 1:
                    # Extract username from the command
                    logger.info("Extracting username from the command")
                    username = message.command[1].strip('@').replace('https://', '').replace('http://', '').replace('t.me/', '').replace('/', '').replace(':', '')

                    try:
                        # First, attempt to get user or bot info
                        logger.info(f"Fetching info for user or bot: {username}")
                        user = await client.get_users(username)
                        premium_status = "Yes" if user.is_premium else "No"
                        dc_location = DC_LOCATIONS.get(user.dc_id, "Unknown")
                        account_created = estimate_account_creation_date(user.id)
                        account_created_str = account_created.strftime("%B %d, %Y")
                        account_age = calculate_account_age(account_created)
                        
                        # Added verification and status
                        verified_status = "Verified" if user.is_verified else "Not Verified"
                        
                        status = "⚪️ Unknown"
                        if user.status:
                            if user.status == UserStatus.ONLINE:
                                status = "Online"
                            elif user.status == UserStatus.OFFLINE:
                                status = "Offline"
                            elif user.status == UserStatus.RECENTLY:
                                status = "Online"
                            elif user.status == UserStatus.LAST_WEEK:
                                status = "Last seen within a week"
                            elif user.status == UserStatus.LAST_MONTH:
                                status = "Last seen within a month"
                        
                        response = (
                            "✘《 **User Information** ↯ 》\n"
                            f"✓ **Full Name:** {user.first_name} {user.last_name or ''}\n"
                            f"✓ **ID:** `{user.id}`\n"
                            f"✓ **Username:** @{user.username if user.username else 'None'}\n"
                            f"✓ **Context ID:** `{user.id}`\n"
                            f"✓ **Data Center:** {user.dc_id} ({dc_location})\n"
                            f"✓ **Premium:** {premium_status}\n"
                            f"✓ **Verification:** {verified_status}\n"
                            f"✓ **Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                            f"✓ **Status:** {status}\n"
                            f"✓ **Account Created On:** {account_created_str}\n"
                            f"✓ **Account Age:** {account_age}"
                        )
                        if user.is_bot:
                            response = (
                                "✘《 **Bot Information** ↯ 》\n"
                                f"✓ **Bot Name:** {user.first_name} {user.last_name or ''}\n"
                                f"✓ **Bot ID:** `{user.id}`\n"
                                f"✓ **Username:** @{user.username if user.username else 'None'}\n"
                                f"✓ **Data Center:** {user.dc_id} ({dc_location})\n"
                                f"✓ **Premium:** {premium_status}\n"
                                f"✓ **Verification:** {verified_status}\n"
                                f"✓ **Flags:** {'Scam' if getattr(user, 'is_scam', False) else 'Fake' if getattr(user, 'is_fake', False) else '✓ Clean'}\n"
                                f"✓ **Account Created On:** {account_created_str}\n"
                                f"✓ **Account Age:** {account_age}"
                            )
                        buttons = [
                            [InlineKeyboardButton("✘ Android Link ↯", url=f"tg://openmessage?user_id={user.id}"), InlineKeyboardButton("✘ iOS Link ↯", url=f"tg://user?id={user.id}")],
                            [InlineKeyboardButton("✘ Permanent Link ↯", user_id=user.id)],
                        ]
                        await client.send_message(chat_id=message.chat.id, text=response, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
                        logger.info("User/bot info fetched successfully with buttons")
                    except (PeerIdInvalid, UsernameNotOccupied, IndexError):
                        logger.info(f"Username '{username}' not found as a user/bot. Checking for chat...")
                        try:
                            chat = await client.get_chat(username)
                            dc_location = DC_LOCATIONS.get(chat.dc_id, "Unknown")
                            response = (
                                f"✘《 **Chat Information** ↯ 》\n"
                                f"✓ **{chat.title}**\n"
                                f"✓ **ID:** `{chat.id}`\n"
                                f"✓ **Type:** {'Supergroup' if chat.type == ChatType.SUPERGROUP else 'Group' if chat.type == ChatType.GROUP else 'Channel'}\n"
                                f"✓ **Member count:** {chat.members_count if chat.members_count else 'Unknown'}"
                            )
                            buttons = [
                                [InlineKeyboardButton("✘ Joining Link ↯", url=f"t.me/c/{str(chat.id).replace('-100', '')}/100"), InlineKeyboardButton("✘ Permanent Link ↯", url=f"t.me/c/{str(chat.id).replace('-100', '')}/100")],
                            ]
                            await client.send_message(chat_id=message.chat.id, text=response, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
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
            finally:
                if not (message.reply_to_message or len(message.command) > 1):  # Only delete progress message if it wasn't edited
                    await client.delete_messages(chat_id=message.chat.id, message_ids=progress_message.id)
                    logger.info("Progress message deleted")
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            await client.send_message(
                chat_id=message.chat.id,
                text="**Looks Like I Don't Have Control Over The User**",
                parse_mode=ParseMode.MARKDOWN
            )
