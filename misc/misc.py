# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import time
import subprocess
from datetime import datetime, timedelta
import psutil
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import UPDATE_CHANNEL_URL
from core import user_activity_collection
from utils import (
    LOGGER,
    responses,
    main_menu_keyboard,
    second_menu_keyboard,
    third_menu_keyboard,
    timeof_fmt,
    DONATION_OPTIONS_TEXT,
    get_donation_buttons,
    generate_invoice,
    handle_donate_callback
)

async def handle_callback_query(client, callback_query):
    call = callback_query
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if call.data == "stats":
        now = datetime.utcnow()
        daily_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(days=1)}})
        weekly_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(weeks=1)}})
        monthly_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(days=30)}})
        yearly_users = await user_activity_collection.count_documents({"is_group": False, "last_activity": {"$gt": now - timedelta(days=365)}})
        total_users = await user_activity_collection.count_documents({"is_group": False})
        total_groups = await user_activity_collection.count_documents({"is_group": True})

        stats_text = (
            f"**Smart Bot Status ⇾ Report ✅**\n"
            f"**━━━━━━━━━━━━━━━━**\n"
            f"**Users & Groups Engagements:**\n"
            f"**1 Day:** {daily_users} users were active\n"
            f"**1 Week:** {weekly_users} users were active\n"
            f"**1 Month:** {monthly_users} users were active\n"
            f"**1 Year:** {yearly_users} users were active\n"
            f"**Total Connected Groups:** {total_groups}\n"
            f"**━━━━━━━━━━━━━━━━**\n"
            f"**Total Smart Tools Users :** {total_users} ✅"
        )

        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="about_me")]])
        await call.message.edit_text(stats_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button)
        return

    if call.data == "server":
        ping_output = subprocess.getoutput("ping -c 1 google.com")
        ping = ping_output.split("time=")[1].split()[0] if "time=" in ping_output else "N/A"
        disk = psutil.disk_usage('/')
        total_disk = disk.total / (2**30)
        used_disk = disk.used / (2**30)
        free_disk = disk.free / (2**30)
        mem = psutil.virtual_memory()
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime = timeof_fmt(uptime_seconds)
        swap = psutil.swap_memory()
        total_mem = mem.total / (2**30)
        used_mem = mem.used / (2**30)
        available_mem = mem.available / (2**30)

        server_status_text = (
            f"**Smart Bot Status ⇾ Report ✅**\n"
            f"**━━━━━━━━━━━━━**\n"
            f"**Server Connection:**\n"
            f"**- Ping:** {ping} ms\n"
            f"**- Bot Status:** Online\n"
            f"**- Server Uptime:** {uptime}\n"
            f"**━━━━━━━━━━━━━**\n"
            f"**Server Storage:**\n"
            f"**- Total:** {total_disk:.2f} GB\n"
            f"**- Used:** {used_disk:.2f} GB\n"
            f"**- Available:** {free_disk:.2f} GB\n"
            f"**━━━━━━━━━━━━━**\n"
            f"**Memory Usage:**\n"
            f"**- Total:** {total_mem:.2f} GB\n"
            f"**- Used:** {used_mem:.2f} GB\n"
            f"**- Available:** {available_mem:.2f} GB\n"
            f"**━━━━━━━━━━━━━**\n"
            f"**Server Stats Check Successful ✅**"
        )

        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="about_me")]])
        await call.message.edit_text(server_status_text, parse_mode=ParseMode.MARKDOWN, reply_markup=back_button)
        return

    if call.data in responses:
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="about_me")]]) if call.data == "server" else (
            InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Status", callback_data="stats"),
                 InlineKeyboardButton("💾 Server", callback_data="server"),
                 InlineKeyboardButton("⭐️ Donate", callback_data="donate")],
                [InlineKeyboardButton("⬅️ Back", callback_data="start_message")]
            ]) if call.data == "about_me" else (
                InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data="main_menu")]]) if call.data in ["ai_tools", "credit_cards", "crypto", "converter", "decoders", "downloaders", "domain_check", "education_utils", "rembg", "github"] else (
                    InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data="second_menu")]]) if call.data in ["info", "mail_tools", "network_tools", "random_address", "string_session", "stripe_keys", "sticker", "time_date", "text_split", "translate"] else (
                        InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data="third_menu")]]) if call.data in ["tempmail", "text_ocr", "bot_users_export", "web_capture", "yt_tools"] else (
                            InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]])
                        )
                    )
                )
            )
        )

        await call.message.edit_text(
            responses[call.data][0],
            parse_mode=responses[call.data][1]['parse_mode'],
            disable_web_page_preview=responses[call.data][1]['disable_web_page_preview'],
            reply_markup=back_button
        )
    elif call.data.startswith("donate_") or call.data.startswith("increment_donate_") or call.data.startswith("decrement_donate_") or call.data == "donate":
        await handle_donate_callback(client, call)
    elif call.data == "main_menu":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard)
    elif call.data == "next_1":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=second_menu_keyboard)
    elif call.data == "next_2":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=third_menu_keyboard)
    elif call.data == "previous_1":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=main_menu_keyboard)
    elif call.data == "previous_2":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=second_menu_keyboard)
    elif call.data == "close":
        await call.message.delete()
    elif call.data == "start_message":
        full_name = f"{call.from_user.first_name} {call.from_user.last_name}" if call.from_user.last_name else call.from_user.first_name
        start_message = (
            f"<b>Hi {full_name}! Welcome To This Bot</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>Smart Tool ⚙️ </b>: The ultimate toolkit on Telegram, offering education, AI, downloaders, temp mail, credit card tool, and more. Simplify your tasks with ease!\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>Don't Forget To <a href='{UPDATE_CHANNEL_URL}'>Join Here</a> For Updates!</b>"
        )
        await call.message.edit_text(
            start_message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Main Menu", callback_data="main_menu")],
                [InlineKeyboardButton("ℹ️ About Me", callback_data="about_me"),
                 InlineKeyboardButton("📄 Policy & Terms", callback_data="policy_terms")]
            ]),
            disable_web_page_preview=True
        )
    elif call.data == "policy_terms":
        policy_terms_text = (
            "<b>📜 Policy & Terms Menu</b>\n\n"
            "At <b>Smart Tool ⚙️</b>, we prioritize your privacy and security. To ensure a seamless and safe experience, we encourage you to review our <b>Privacy Policy</b> and <b>Terms & Conditions</b>.\n\n"
            "🔹 <b>Privacy Policy</b>: Learn how we collect, use, and protect your personal data.\n"
            "🔹 <b>Terms & Conditions</b>: Understand the rules and guidelines for using our services.\n\n"
            "<b>💡 Choose an option below to proceed:</b>"
        )
        policy_terms_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Privacy Policy", callback_data="privacy_policy"),
             InlineKeyboardButton("Terms & Conditions", callback_data="terms_conditions")],
            [InlineKeyboardButton("⬅️ Back", callback_data="start_message")]
        ])
        await call.message.edit_text(policy_terms_text, parse_mode=ParseMode.HTML, reply_markup=policy_terms_button)
    elif call.data == "privacy_policy":
        privacy_policy_text = (
            "<b>📜 Privacy Policy for Smart Tool ⚙️</b>\n\n"
            "Welcome to <b>Smart Tool ⚙️</b> Bot. By using our services, you agree to this privacy policy.\n\n"
            "1. <b>Personal Information</b>:\n"
            "   - Personal Information: User ID and username for personalization.\n"
            "   - <b>Usage Data</b>: Information on how you use the app to improve our services.\n\n"
            "2. Usage of Information:\n"
            "   - <b>Service Enhancement</b>: To provide and improve <b>Smart Tool ⚙️</b>\n"
            "   - <b>Communication</b>: Updates and new features.\n"
            "   - <b>Security</b>: To prevent unauthorized access.\n"
            "   - <b>Advertisements</b>: Display of promotions.\n\n"
            "3. Data Security:\n"
            "   - These tools do not store any data, ensuring your privacy.\n"
            "   - We use strong security measures, although no system is 100% secure.\n\n"
            "Thank you for using <b>Smart Tool ⚙️</b>. We prioritize your privacy and security."
        )
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="policy_terms")]])
        await call.message.edit_text(privacy_policy_text, parse_mode=ParseMode.HTML, reply_markup=back_button)
    elif call.data == "terms_conditions":
        terms_conditions_text = (
            "<b>📜 Terms & Conditions for Smart Tool ⚙️</b>\n\n"
            "Welcome to <b>Smart Tool ⚙️</b>. By using our services, you accept these <b>Terms & Conditions</b>.\n\n"
            "<b>1. Usage Guidelines</b>\n"
            "   - Eligibility: Must be 13 years of age or older.\n\n"
            "<b>2. Prohibited</b>\n"
            "   - Illegal and unauthorized uses are strictly forbidden.\n"
            "   - Spamming and abusing are not allowed in this Bot\n\n"
            "<b>3. Tools and Usage</b>\n"
            "   - For testing/development purposes only, not for illegal use.\n"
            "   - We <b>do not support</b> misuse for fraud or policy violations.\n"
            "   - Automated requests may lead to service limitations or suspension.\n"
            "   - We are not responsible for any account-related issues.\n\n"
            "<b>4. User Responsibility</b>\n"
            "   - You are responsible for all activities performed using the bot.\n"
            "   - Ensure that your activities comply with platform policies.\n\n"
            "<b>5. Disclaimer of Warranties</b>\n"
            "   - We do not guarantee uninterrupted service, accuracy, or reliability.\n"
            "   - We are not responsible for any consequences arising from your use of the bot.\n\n"
            "<b>6. Termination</b>\n"
            "   - Access may be terminated for any violations without prior notice.\n\n"
            "<b>7. Contact Information</b>\n"
            "   - Contact My Dev for any inquiries or concerns. <a href='tg://user?id=7303810912'>Abir Arafat Chawdhury👨‍💻</a> \n\n"
            "Thank you for using <b>Smart Tool ⚙️</b>. We prioritize your safety, security, and best user experience. 🚀"
        )
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="policy_terms")]])
        await call.message.edit_text(terms_conditions_text, parse_mode=ParseMode.HTML, reply_markup=back_button)
    elif call.data == "second_menu":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=second_menu_keyboard)
    elif call.data == "third_menu":
        await call.message.edit_text("<b>Here are the Smart-Tool Options: 👇</b>", parse_mode=ParseMode.HTML, reply_markup=third_menu_keyboard)
