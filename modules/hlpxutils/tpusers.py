from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from utils import notify_admin, LOGGER
from core import banned_users, user_activity_collection

def setup_tp_handler(app: Client):
    @app.on_message(filters.command(["topusers"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def topusers_handler(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY)
            return
        
        loading_msg = await client.send_message(message.chat.id, "**Fetching Top Users Of SmartTool ⚙️...**", parse_mode=ParseMode.MARKDOWN)
        
        try:
            page = 1
            users_per_page = 9
            now = datetime.utcnow()
            daily_users = await user_activity_collection.find({"is_group": False, "last_activity": {"$gte": now - timedelta(days=1)}}).to_list(None)
            total_users = len(daily_users)
            total_pages = (total_users + users_per_page - 1) // users_per_page
            start_index = (page - 1) * users_per_page
            end_index = start_index + users_per_page
            paginated_users = daily_users[start_index:end_index]
            
            top_users_text = (
                f"**🏆 Top Users (All-time) — page {page}/{total_pages if total_pages > 0 else 1}:**\n"
                f"**━━━━━━━━━━━━━━━**\n"
            )
            for i, user in enumerate(paginated_users, start=start_index + 1):
                user_id_data = user['user_id']
                try:
                    telegram_user = await client.get_users(user_id_data)
                    full_name = f"{telegram_user.first_name} {telegram_user.last_name}" if telegram_user.last_name else telegram_user.first_name
                except Exception as e:
                    LOGGER.error(f"Failed to fetch user {user_id_data}: {e}")
                    full_name = f"User_{user_id_data}"
                rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
                top_users_text += f"**{rank_emoji} {i}.** [{full_name}](tg://user?id={user_id_data})\n** - User Id :** `{user_id_data}`\n\n"
            
            buttons = []
            nav_buttons = []
            
            if page == 1 and total_pages > 1:
                nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"nxttpusers_{page+1}"))
                buttons.append(nav_buttons)
            elif page > 1 and page < total_pages:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prvtpusers_{page-1}"))
                nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"nxttpusers_{page+1}"))
                buttons.append(nav_buttons)
            elif page == total_pages and page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prvtpusers_{page-1}"))
                buttons.append(nav_buttons)
            
            if buttons:
                top_users_buttons = InlineKeyboardMarkup(buttons)
            else:
                top_users_buttons = None
            
            await loading_msg.edit_text(top_users_text, parse_mode=ParseMode.MARKDOWN, reply_markup=top_users_buttons)
        
        except Exception as e:
            LOGGER.error(f"Failed to fetch top users: {e}")
            await loading_msg.edit_text("**Sorry Failed To Load Database**", parse_mode=ParseMode.MARKDOWN)
    
    @app.on_callback_query(filters.regex(r"^(nxttpusers|prvtpusers)_"))
    async def topusers_callback(client: Client, callback_query: CallbackQuery):
        call = callback_query
        user_id = call.from_user.id if call.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await call.answer(BAN_REPLY, show_alert=True)
            return
        
        try:
            if call.data.startswith("nxttpusers_"):
                page = int(call.data.split("_")[1])
            elif call.data.startswith("prvtpusers_"):
                page = int(call.data.split("_")[1])
            
            users_per_page = 9
            now = datetime.utcnow()
            daily_users = await user_activity_collection.find({"is_group": False, "last_activity": {"$gte": now - timedelta(days=1)}}).to_list(None)
            total_users = len(daily_users)
            total_pages = (total_users + users_per_page - 1) // users_per_page
            start_index = (page - 1) * users_per_page
            end_index = start_index + users_per_page
            paginated_users = daily_users[start_index:end_index]
            
            top_users_text = (
                f"**🏆 Top Users (All-time) — page {page}/{total_pages if total_pages > 0 else 1}:**\n"
                f"**━━━━━━━━━━━━━━━**\n"
            )
            for i, user in enumerate(paginated_users, start=start_index + 1):
                user_id_data = user['user_id']
                try:
                    telegram_user = await client.get_users(user_id_data)
                    full_name = f"{telegram_user.first_name} {telegram_user.last_name}" if telegram_user.last_name else telegram_user.first_name
                except Exception as e:
                    LOGGER.error(f"Failed to fetch user {user_id_data}: {e}")
                    full_name = f"User_{user_id_data}"
                rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
                top_users_text += f"**{rank_emoji} {i}.** [{full_name}](tg://user?id={user_id_data})\n** - User Id :** `{user_id_data}`\n\n"
            
            buttons = []
            nav_buttons = []
            
            if page == 1 and total_pages > 1:
                nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"nxttpusers_{page+1}"))
                buttons.append(nav_buttons)
            elif page > 1 and page < total_pages:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prvtpusers_{page-1}"))
                nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"nxttpusers_{page+1}"))
                buttons.append(nav_buttons)
            elif page == total_pages and page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prvtpusers_{page-1}"))
                buttons.append(nav_buttons)
            
            if buttons:
                top_users_buttons = InlineKeyboardMarkup(buttons)
            else:
                top_users_buttons = None
            
            await call.message.edit_text(top_users_text, parse_mode=ParseMode.MARKDOWN, reply_markup=top_users_buttons)
        
        except Exception as e:
            LOGGER.error(f"Failed to handle top users callback: {e}")
            await call.answer("Failed to load data", show_alert=True)
