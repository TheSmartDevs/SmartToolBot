from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from core import banned_users
from utils import notify_admin, LOGGER
import aiohttp
import time

# Temporary pagination session storage
pagination_sessions = {}

def setup_cpn_handler(app: Client):
    @app.on_message(filters.command(["cpn"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def cpn_handler(client: Client, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        LOGGER.info(f"[CPN] Command received from user: {user_id}")

        if await banned_users.find_one({"user_id": user_id}):
            LOGGER.info(f"[CPN] Blocked banned user: {user_id}")
            await client.send_message(chat_id, "**✘ Sorry, You're Banned From Using Me ↯**", parse_mode=ParseMode.MARKDOWN)
            return

        args = message.text.split()
        if len(args) < 2:
            LOGGER.warning(f"[CPN] Missing site name from user: {user_id}")
            await client.send_message(chat_id, "**❌ Missing store name! Try like this: /cpn amazon**", parse_mode=ParseMode.MARKDOWN)
            return

        sitename = args[1].strip().lower()
        sitename_with_com = f"{sitename}.com"
        LOGGER.info(f"[CPN] Processing site: {sitename_with_com} for user: {user_id}")

        loading = await client.send_message(chat_id, f"**🔍 Searching Coupon For {sitename}**", parse_mode=ParseMode.MARKDOWN)

        try:
            LOGGER.info(f"[CPN] Sending API request for {sitename_with_com}")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://smartcoupon.vercel.app/cpn?site={sitename_with_com}") as resp:
                    if resp.status != 200:
                        raise Exception(f"API Error: Status {resp.status}")
                    data = await resp.json()
                    LOGGER.info(f"[CPN] API response received for {sitename_with_com}")

        except Exception as e:
            LOGGER.error(f"[CPN] API connection error for {sitename_with_com}: {e}")
            await notify_admin(client, "/cpn", e, message)
            await loading.edit("**❌ Site unreachable or error occurred. Try again later.**", parse_mode=ParseMode.MARKDOWN)
            return

        if "results" not in data or not data["results"]:
            LOGGER.warning(f"[CPN] No results found for {sitename_with_com}")
            await loading.edit("**❌ No promo code found. Store name is incorrect?**", parse_mode=ParseMode.MARKDOWN)
            return

        coupons = data["results"]
        pages = [coupons[i:i + 5] for i in range(0, len(coupons), 5)]
        session_id = f"{chat_id}_{message.id}"
        pagination_sessions[session_id] = {
            "coupons": coupons,
            "current_page": 0,
            "timestamp": time.time(),
            "sitename": sitename
        }

        LOGGER.info(f"[CPN] Parsed {len(coupons)} coupons for {sitename}")

        async def format_page(page_idx):
            start_index = page_idx * 5
            text = f"**Successfully Found {len(coupons)} Coupons For {sitename.upper()} ✅**\n\n"
            for i, item in enumerate(pages[page_idx], start=start_index + 1):
                title = item.get("title", "No title available")
                code = item.get("code", "No code available")
                text += f"**{i}.**\n**⊗ Title:** {title}\n**⊗ Coupon Code:** `{code}`\n\n"
            return text.strip()

        buttons = []
        if len(pages) > 1:
            buttons.append([InlineKeyboardButton("➡️ Next", callback_data=f"cpn_next_{session_id}")])

        try:
            await loading.edit(
                await format_page(0),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            LOGGER.warning(f"[CPN] Failed to apply reply markup: {e}")
            await loading.edit(await format_page(0), parse_mode=ParseMode.MARKDOWN)

        LOGGER.info(f"[CPN] First page sent to user {user_id}")

    @app.on_callback_query(filters.regex("^cpn_(next|prev)_(.+)$"))
    async def handle_pagination(client: Client, callback_query):
        action, session_id = callback_query.data.split("_", 2)[1:]
        user_id = callback_query.from_user.id
        LOGGER.info(f"[CPN] Pagination '{action}' triggered by user: {user_id}")

        session = pagination_sessions.get(session_id)
        if not session or time.time() - session["timestamp"] > 20:
            LOGGER.warning(f"[CPN] Session expired for user: {user_id}")
            await callback_query.answer("❌ Session Expired. Try Again.", show_alert=True)
            if session_id in pagination_sessions:
                del pagination_sessions[session_id]
            return

        try:
            coupons = session["coupons"]
            sitename = session["sitename"]
            pages = [coupons[i:i + 5] for i in range(0, len(coupons), 5)]
            page = session["current_page"]

            if action == "next" and page < len(pages) - 1:
                session["current_page"] += 1
            elif action == "prev" and page > 0:
                session["current_page"] -= 1

            page = session["current_page"]
            session["timestamp"] = time.time()

            async def format_page(page_idx):
                start_index = page_idx * 5
                text = f"**Successfully Found {len(coupons)} Coupons For {sitename.upper()} ✅**\n\n"
                for i, item in enumerate(pages[page_idx], start=start_index + 1):
                    title = item.get("title", "No title available")
                    code = item.get("code", "No code available")
                    text += f"**{i}.**\n**⊗ Title:** {title}\n**⊗ Coupon Code:** `{code}`\n\n"
                return text.strip()

            buttons = []
            if page > 0:
                buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"cpn_prev_{session_id}"))
            if page < len(pages) - 1:
                buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"cpn_next_{session_id}"))

            try:
                await callback_query.message.edit_text(
                    await format_page(page),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([buttons] if buttons else None)
                )
            except Exception as e:
                LOGGER.warning(f"[CPN] Failed to edit with reply markup: {e}")
                await callback_query.message.edit_text(
                    await format_page(page),
                    parse_mode=ParseMode.MARKDOWN
                )

            await callback_query.answer()

        except Exception as e:
            LOGGER.error(f"[CPN] Pagination error for user {user_id}: {e}")
            await notify_admin(client, "/cpn-pagination", e, callback_query.message)
            await callback_query.answer("❌ Something went wrong!", show_alert=True)
