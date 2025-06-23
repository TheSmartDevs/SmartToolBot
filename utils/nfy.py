import traceback
from datetime import datetime
from typing import Optional, Union
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode
from config import OWNER_ID, DEVELOPER_USER_ID, LOG_CHANNEL_ID
from .logging_setup import LOGGER
from app import app

TRACEBACK_DATA = {}

async def check_channel_membership(client: Client, user_id: int) -> tuple[bool, str, Optional[int]]:
    try:
        # Use LOG_CHANNEL_ID directly - works with both private and public channels
        from config import LOG_CHANNEL_ID
        
        # Validate LOG_CHANNEL_ID format
        if not isinstance(LOG_CHANNEL_ID, int):
            try:
                channel_id = int(LOG_CHANNEL_ID)
            except (ValueError, TypeError):
                return False, f"Invalid LOG_CHANNEL_ID format: {LOG_CHANNEL_ID}. Must be a valid integer.", None
        else:
            channel_id = LOG_CHANNEL_ID
        
        # Check if bot is member of the channel
        member = await client.get_chat_member(channel_id, user_id)
        
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True, "", channel_id
        else:
            return False, f"User {user_id} is not a member of the channel", channel_id
            
    except Exception as e:
        # Handle common errors gracefully
        error_msg = str(e).lower()
        if "user not found" in error_msg:
            return False, f"User {user_id} not found in channel", None
        elif "chat not found" in error_msg:
            return False, f"Channel {LOG_CHANNEL_ID} not found or bot is not a member", None
        elif "peer_id_invalid" in error_msg:
            return False, f"Invalid channel ID: {LOG_CHANNEL_ID}", None
        elif "forbidden" in error_msg:
            return False, f"Bot doesn't have permission to check membership in channel {LOG_CHANNEL_ID}", None
        else:
            return False, f"Failed to check membership: {str(e)}", None

async def notify_admin(client: Client, command: str, error: Union[Exception, str], message: Optional[Message] = None) -> None:
    try:
        is_member, error_msg, channel_id = await check_channel_membership(client, client.me.id)
        if not is_member:
            LOGGER.error(error_msg)
        user_info = {'id': "N/A", 'mention': "Unknown User", 'username': "N/A", 'full_name': "N/A"}
        chat_id_user = "N/A"
        message_content = "N/A"
        message_type = "N/A"
        if message:
            if message.from_user:
                user = message.from_user
                full_name = f"{user.first_name} {user.last_name or ''}".strip()
                user_info = {'id': user.id, 'mention': f"<a href='tg://user?id={user.id}'>{full_name}</a>", 'username': f"@{user.username}" if user.username else "N/A", 'full_name': full_name}
            chat_id_user = getattr(message.chat, 'id', "N/A")
            if message.text:
                message_content = message.text[:200]
                message_type = "Text"
            elif message.caption:
                message_content = message.caption[:200]
                message_type = "Caption"
            elif message.photo:
                message_type = "Photo"
            elif message.document:
                message_type = "Document"
            elif message.video:
                message_type = "Video"
            else:
                message_type = str(message.media) if message.media else "Unknown"
        if isinstance(error, str):
            error_type = "StringError"
            error_message = error
            traceback_text = "N/A"
            error_level = "WARNING"
        else:
            error_type = type(error).__name__
            error_message = str(error)
            traceback_text = "".join(traceback.format_exception(type(error), error, error.__traceback__)) if error.__traceback__ else "N/A"
            error_level = ("WARNING" if isinstance(error, (ValueError, UserWarning)) else "ERROR" if isinstance(error, RuntimeError) else "CRITICAL")
        now = datetime.now()
        full_timestamp = now.strftime('%d-%m-%Y %H:%M:%S %p')
        formatted_date = now.strftime('%d-%m-%Y')
        formatted_time = now.strftime('%H:%M:%S %p')
        error_id = f"{int(now.timestamp() * 1000000)}"
        TRACEBACK_DATA[error_id] = {'error_type': error_type, 'error_level': error_level, 'message_content': message_content, 'message_type': message_type, 'traceback_text': traceback_text, 'full_timestamp': full_timestamp, 'command': command, 'error_message': error_message, 'user_info': user_info, 'chat_id': chat_id_user, 'formatted_date': formatted_date, 'formatted_time': formatted_time}
        error_report = (
            "<b>🔍 New Bug Found In Smart Tools 📋</b>\n"
            "<b>━━━━━━━━━━━━━━━━</b>\n"
            f"<b>⊗ COMMAND:</b> <code>{command}</code>\n"
            f"<b>⊗ ISSUE:</b> <code>{error_message[:300]}</code>\n"
            f"<b>⊗ USER'S NAME:</b> <code>{user_info['full_name']}</code>\n"
            f"<b>⊗ USERID:</b> <code>{user_info['id']}</code>\n"
            f"<b>⊗ ChatID:</b> <code>{chat_id_user}</code>\n"
            f"<b>⊗ TIME:</b> <code>{formatted_time}</code>\n"
            f"<b>⊗ DATE:</b> <code>{formatted_date}</code>\n"
            "<b>━━━━━━━━━━━━━━━━</b>\n"
            "<b>🔍 Always Fix Bug & Keep Bot Pro 📋</b>"
        )
        keyboard_buttons = []
        if user_info['id'] != "N/A":
            keyboard_buttons.append([InlineKeyboardButton("User Profile", user_id=user_info['id']), InlineKeyboardButton("Developer", user_id=DEVELOPER_USER_ID)])
        keyboard_buttons.append([InlineKeyboardButton("View Full Traceback", callback_data=f"viewtrcbc{error_id}$")])
        await client.send_message(chat_id=OWNER_ID, text=error_report, reply_markup=InlineKeyboardMarkup(keyboard_buttons), disable_web_page_preview=True, disable_notification=(error_level == "WARNING"), parse_mode=ParseMode.HTML)
        if is_member and channel_id:
            minimal_report = (
                "<b>🔍 New Bug Found In Smart Tools 📋</b>\n"
                "<b>━━━━━━━━━━━━━━━━</b>\n"
                f"<b>⊗ COMMAND:</b> <code>{command}</code>\n"
                f"<b>⊗ ISSUE:</b> <code>{error_message[:300]}</code>\n"
                f"<b>⊗ USER'S NAME:</b> <code>{user_info['full_name']}</code>\n"
                f"<b>⊗ USERID:</b> <code>{user_info['id']}</code>\n"
                f"<b>⊗ ChatID:</b> <code>{chat_id_user}</code>\n"
                f"<b>⊗ TIME:</b> <code>{formatted_time}</code>\n"
                f"<b>⊗ DATE:</b> <code>{formatted_date}</code>\n"
                "<b>━━━━━━━━━━━━━━━━</b>\n"
                "<b>🔍 Always Fix Bug & Keep Bot Pro 📋</b>"
            )
            await client.send_message(chat_id=channel_id, text=minimal_report, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Updates Channel", url="https://t.me/TheSmartDev")]]), disable_web_page_preview=True, disable_notification=(error_level == "WARNING"), parse_mode=ParseMode.HTML)
        LOGGER.info(f"Admin notification sent for command: {command} with error_id: {error_id}")
    except Exception as e:
        LOGGER.error(f"Failed to send admin notification: {e}")
        LOGGER.error(traceback.format_exc())

@app.on_callback_query(filters.regex(r"^viewtrcbc.*\$$"))
async def handle_traceback_callback(client: Client, callback_query):
    try:
        LOGGER.info(f"Traceback callback triggered: {callback_query.data}")
        error_id = callback_query.data.replace("viewtrcbc", "").replace("$", "")
        LOGGER.info(f"Extracted error_id: {error_id}")
        if error_id not in TRACEBACK_DATA:
            LOGGER.warning(f"Traceback data not found for error_id: {error_id}")
            LOGGER.info(f"Available error_ids: {list(TRACEBACK_DATA.keys())}")
            await callback_query.answer("❌ Traceback data not found or expired!", show_alert=True)
            return
        data = TRACEBACK_DATA[error_id]
        LOGGER.info(f"Found traceback data for error_id: {error_id}")
        traceback_text = data['traceback_text']
        if len(traceback_text) > 2000:
            traceback_text = traceback_text[:2000] + "\n... (truncated)"
        traceback_escaped = traceback_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        issue_escaped = data['error_message'][:200].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        content_escaped = data['message_content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        traceback_message = (
            "<b>🔍 Full Traceback Error Here 📋</b>\n"
            "<b>━━━━━━━━━━━━━━━</b>\n"
            f"<b>⊗ Command:</b> <code>{data['command']}</code>\n"
            f"<b>⊗ Error Type:</b> <code>{data['error_type']}</code>\n"
            f"<b>⊗ Severity:</b> <code>{data['error_level']}</code>\n"
            f"<b>⊗ Issue:</b>\n<blockquote expandable=True>{issue_escaped}</blockquote>\n"
            f"<b>⊗ Content:</b>\n<blockquote expandable=True>{content_escaped}</blockquote>\n"
            f"<b>⊗ Content Type:</b> <code>{data['message_type']}</code>\n"
            f"<b>⊗ Time:</b> <code>{data['full_timestamp']}</code>\n"
            f"<b>⊗ Traceback:</b>\n<blockquote expandable=True>{traceback_escaped}</blockquote>"
            "<b>━━━━━━━━━━━━━━━</b>\n"
            "<b>🔍 Must Take Action Soon 📋</b>"
        )
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙Back", callback_data=f"backtosummary{error_id}$")]])
        await callback_query.edit_message_text(text=traceback_message, reply_markup=back_button, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        await callback_query.answer("Here Is The Full Traceback ✅")
        LOGGER.info(f"Traceback displayed successfully for error_id: {error_id}")
    except Exception as e:
        LOGGER.error(f"Error in traceback callback: {e}")
        LOGGER.error(traceback.format_exc())
        try:
            await callback_query.answer("Failed To Show Traceback ❌", show_alert=True)
        except:
            pass

@app.on_callback_query(filters.regex(r"^backtosummary.*\$$"))
async def handle_back_callback(client: Client, callback_query):
    try:
        LOGGER.info(f"Back to summary callback triggered: {callback_query.data}")
        error_id = callback_query.data.replace("backtosummary", "").replace("$", "")
        if error_id not in TRACEBACK_DATA:
            await callback_query.answer("Failed To Show Traceback ❌", show_alert=True)
            return
        data = TRACEBACK_DATA[error_id]
        error_report = (
            "<b>🔍 New Bug Found In Smart Tools 📋</b>\n"
            "<b>━━━━━━━━━━━━━━━━</b>\n"
            f"<b>⊗ COMMAND:</b> <code>{data['command']}</code>\n"
            f"<b>⊗ ISSUE:</b> <code>{data['error_message'][:300]}</code>\n"
            f"<b>⊗ USER'S NAME:</b> <code>{data['user_info']['full_name']}</code>\n"
            f"<b>⊗ USERID:</b> <code>{data['user_info']['id']}</code>\n"
            f"<b>⊗ ChatID:</b> <code>{data['chat_id']}</code>\n"
            f"<b>⊗ TIME:</b> <code>{data['formatted_time']}</code>\n"
            f"<b>⊗ DATE:</b> <code>{data['formatted_date']}</code>\n"
            "<b>━━━━━━━━━━━━━━━━</b>\n"
            "<b>🔍 Always Fix Bug & Keep Bot Pro 📋</b>"
        )
        keyboard_buttons = []
        if data['user_info']['id'] != "N/A":
            keyboard_buttons.append([InlineKeyboardButton("User Profile", user_id=data['user_info']['id']), InlineKeyboardButton("Developer", user_id=DEVELOPER_USER_ID)])
        keyboard_buttons.append([InlineKeyboardButton("View Full Traceback", callback_data=f"viewtrcbc{error_id}$")])
        await callback_query.edit_message_text(text=error_report, reply_markup=InlineKeyboardMarkup(keyboard_buttons), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        await callback_query.answer("Summary Loaded Successful ✅!")
        LOGGER.info(f"Back to summary successful for error_id: {error_id}")
    except Exception as e:
        LOGGER.error(f"Error in back callback: {e}")
        LOGGER.error(traceback.format_exc())
        try:
            await callback_query.answer("Error ❌ Loading Summary", show_alert=True)
        except:
            pass

def cleanup_old_traceback_data():
    try:
        current_time = datetime.now().timestamp() * 1000000
        keys_to_remove = []
        for key in TRACEBACK_DATA.keys():
            try:
                timestamp = float(key)
                if current_time - timestamp > 86400000000:
                    keys_to_remove.append(key)
            except:
                pass
        for key in keys_to_remove:
            del TRACEBACK_DATA[key]
        if keys_to_remove:
            LOGGER.info(f"Cleaned up {len(keys_to_remove)} old traceback entries")
    except Exception as e:
        LOGGER.error(f"Error in cleanup: {e}")

try:
    cleanup_old_traceback_data()
except:
    pass
