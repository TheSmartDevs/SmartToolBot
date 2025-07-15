import traceback
from datetime import datetime
from typing import Optional, Union
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode
from config import OWNER_ID, DEVELOPER_USER_ID, LOG_CHANNEL_ID, UPDATE_CHANNEL_URL
from .logging_setup import LOGGER
from app import app

TRACEBACK_DATA = {}

async def check_channel_membership(client: Client, user_id: int) -> tuple[bool, str, Optional[int]]:
    try:
        if not LOG_CHANNEL_ID:
            return False, "LOG_CHANNEL_ID is not configured", None
        
        channel_id = LOG_CHANNEL_ID
        
        if isinstance(channel_id, str):
            if channel_id.startswith('@'):
                pass
            else:
                try:
                    channel_id = int(channel_id)
                except (ValueError, TypeError):
                    return False, f"Invalid LOG_CHANNEL_ID format: {LOG_CHANNEL_ID}. Must be a valid integer or username.", None
        
        if isinstance(channel_id, int):
            if channel_id > 0:
                channel_id = -channel_id
            
            if not str(abs(channel_id)).startswith('100'):
                channel_id = int(f"-100{abs(channel_id)}")
        
        member = await client.get_chat_member(channel_id, user_id)
        
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True, "", channel_id
        else:
            return False, f"User {user_id} is not a member of the channel", channel_id
            
    except Exception as e:
        error_msg = str(e).lower()
        if "user not found" in error_msg:
            return False, f"User {user_id} not found in channel", None
        elif "chat not found" in error_msg or "channel_invalid" in error_msg:
            return False, f"Channel {LOG_CHANNEL_ID} not found or invalid", None
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
        if message and message.from_user:
            user = message.from_user
            full_name = f"{user.first_name} {user.last_name or ''}".strip()
            user_info = {'id': user.id, 'mention': f"<a href='tg://user?id={user.id}'>{full_name}</a>", 'username': f"@{user.username}" if user.username else "N/A", 'full_name': full_name}
            chat_id_user = getattr(message.chat, 'id', "N/A")
        
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
        formatted_time = now.strftime('%H:%M:%S')
        error_id = f"{int(now.timestamp() * 1000000)}"
        TRACEBACK_DATA[error_id] = {
            'error_type': error_type,
            'error_level': error_level,
            'traceback_text': traceback_text,
            'full_timestamp': full_timestamp,
            'command': command,
            'error_message': error_message,
            'user_info': user_info,
            'chat_id': chat_id_user,
            'formatted_date': formatted_date,
            'formatted_time': formatted_time
        }
        
        error_report = (
            "<b>🚨 New Bug Discovered in Smart Tools</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"- <b>Command</b>: {command}\n"
            f"- <b>User's Name</b>: {user_info['full_name']}\n"
            f"- <b>User's ID</b>: <code>{user_info['id']}</code>\n"
            f"- <b>Time</b>: {formatted_time}\n"
            f"- <b>Date</b>: {formatted_date}\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>🧭 Tap below to buttons investigate.</b>"
        )
        
        keyboard_buttons = []
        if user_info['id'] != "N/A":
            keyboard_buttons.append([
                InlineKeyboardButton("👤 View Profile", user_id=user_info['id']),
                InlineKeyboardButton("🛠 Dev", user_id=DEVELOPER_USER_ID)
            ])
        keyboard_buttons.append([InlineKeyboardButton("📄 View Traceback", callback_data=f"viewtrcbc{error_id}$")])
        
        await client.send_message(
            chat_id=OWNER_ID,
            text=error_report,
            reply_markup=InlineKeyboardMarkup(keyboard_buttons),
            disable_web_page_preview=True,
            disable_notification=(error_level == "WARNING"),
            parse_mode=ParseMode.HTML
        )
        
        if is_member and channel_id:
            minimal_report = (
                "<b>🚨 New Bug Discovered in Smart Tools</b>\n"
                "<b>━━━━━━━━━━━━━━━━━━</b>\n"
                f"- <b>Command</b>: {command}\n"
                f"- <b>User's Name</b>: {user_info['full_name']}\n"
                f"- <b>User's ID</b>: <code>{user_info['id']}</code>\n"
                f"- <b>Time</b>: {formatted_time}\n"
                f"- <b>Date</b>: {formatted_date}\n"
                "<b>━━━━━━━━━━━━━━━━━━</b>\n"
                "<b>🧭 Tap below to buttons investigate.</b>"
            )
            await client.send_message(
                chat_id=channel_id,
                text=minimal_report,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Updates Channel", url=UPDATE_CHANNEL_URL)]]),
                disable_web_page_preview=True,
                disable_notification=(error_level == "WARNING"),
                parse_mode=ParseMode.HTML
            )
        
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
        
        traceback_message = (
            "<b>🚨 Sure Here Is The Full Issue</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"- <b>Command</b>: {data['command']}\n"
            f"- <b>Error Type</b>: {data['error_type']}\n"
            f"- <b>Issue</b>: {issue_escaped}\n"
            f"- <b>Traceback</b>: <blockquote expandable=True>{traceback_escaped}</blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>🧭 Tap below to button Back To Main.</b>"
        )
        
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back To Main", callback_data=f"backtosummary{error_id}$")]])
        await callback_query.edit_message_text(
            text=traceback_message,
            reply_markup=back_button,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
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
            "<b>🚨 New Bug Discovered in Smart Tools</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"- <b>Command</b>: {data['command']}\n"
            f"- <b>User's Name</b>: {data['user_info']['full_name']}\n"
            f"- <b>User's ID</b>: <code>{data['user_info']['id']}</code>\n"
            f"- <b>Time</b>: {data['formatted_time']}\n"
            f"- <b>Date</b>: {data['formatted_date']}\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>🧭 Tap below to buttons investigate.</b>"
        )
        
        keyboard_buttons = []
        if data['user_info']['id'] != "N/A":
            keyboard_buttons.append([
                InlineKeyboardButton("👤 View Profile", user_id=data['user_info']['id']),
                InlineKeyboardButton("🛠 Dev", user_id=DEVELOPER_USER_ID)
            ])
        keyboard_buttons.append([InlineKeyboardButton("📄 View Traceback", callback_data=f"viewtrcbc{error_id}$")])
        
        await callback_query.edit_message_text(
            text=error_report,
            reply_markup=InlineKeyboardMarkup(keyboard_buttons),
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
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
