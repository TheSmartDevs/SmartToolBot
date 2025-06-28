#Copyright @ISmartCoder
#Updates Channel: https://t.me/TheSmartDev
import re
import os
from pyrogram import Client, filters, handlers
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import COMMAND_PREFIX, MAX_TXT_SIZE, UPDATE_CHANNEL_URL
from utils import notify_admin, LOGGER
from core import banned_users

def filter_bin(content, bin_number):
    filtered_lines = [line for line in content if line.startswith(bin_number)]
    return filtered_lines

def remove_bin(content, bin_number):
    filtered_lines = [line for line in content if not line.startswith(bin_number)]
    return filtered_lines

async def process_file(file_path, bin_number, command):
    with open(file_path, 'r') as file:
        content = file.readlines()
    if command in ['/adbin', '.adbin']:
        return filter_bin(content, bin_number)
    elif command in ['/rmbin', '.rmbin']:
        return remove_bin(content, bin_number)

async def handle_bin_commands(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if user_id and await banned_users.find_one({"user_id": user_id}):
        await client.send_message(
            message.chat.id,
            "**✘Sorry You're Banned From Using Me↯**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        return

    temp_msg = None
    try:
        args = message.text.split()
        if len(args) != 2:
            await client.send_message(
                message.chat.id,
                "**⚠️ Please provide a valid BIN number❌**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            return

        command = args[0]
        bin_number = args[1]
        if not re.match(r'^\d{6}$', bin_number):
            await client.send_message(
                message.chat.id,
                "**⚠️ BIN number must be 6 digits❌**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            return

        if not message.reply_to_message:
            await client.send_message(
                message.chat.id,
                "**⚠️ Please provide a valid .txt file by replying to it.❌**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            return

        if not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
            await client.send_message(
                message.chat.id,
                "**⚠️ Please provide a valid .txt file by replying to it.❌**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            return

        file_size_mb = message.reply_to_message.document.file_size / (1024 * 1024)
        if file_size_mb > MAX_TXT_SIZE:
            await client.send_message(
                message.chat.id,
                "**⚠️ File size exceeds the 15MB limit❌**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            return

        processing_text = "**Adding Bins.....**" if command in ['/adbin', '.adbin'] else "**Removing Bins.....**"
        temp_msg = await client.send_message(
            message.chat.id,
            processing_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )

        file_path = await message.reply_to_message.download()
        processed_cards = await process_file(file_path, bin_number, command)
        
        if not processed_cards:
            await client.send_message(
                message.chat.id,
                f"**❌ No credit card details found with BIN {bin_number}.**",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            os.remove(file_path)
            if temp_msg:
                await temp_msg.delete()
            return

        action = "Add" if command in ['/adbin', '.adbin'] else "Remove"
        actioner = "Adder" if command in ['/adbin', '.adbin'] else "Remover"
        file_label = "Added" if command in ['/adbin', '.adbin'] else "Removed"

        if len(processed_cards) <= 10:
            formatted_cards = "\n".join(f"`{line.strip()}`" for line in processed_cards)
            response_message = (
                f"**Smart Bin {action} → Successful  ✅**\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"{formatted_cards}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"**Smart Bin {actioner} → Activated  ✅**"
            )
            await client.send_message(
                message.chat.id,
                response_message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
        else:
            file_name = f"Bin {file_label} Txt.txt"
            with open(file_name, "w") as file:
                file.write("".join(processed_cards))

            total_amount = len(processed_cards)
            total_size = f"{os.path.getsize(file_name) / 1024:.2f} KB"
            total_lines = len(processed_cards)
            caption = (
                f"**Smart Bin {action} → Successful  ✅**\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"**⊗ Total Amount:** {total_amount}\n"
                f"**⊗ Total Size:** {total_size}\n"
                f"**⊗ Target Bin:** {bin_number}\n"
                f"**⊗ Total Lines:** {total_lines}\n"
                f"**━━━━━━━━━━━━━━━━━**\n"
                f"**Smart Bin {actioner} → Activated  ✅**"
            )

            await client.send_document(
                chat_id=message.chat.id, document=file_name,
                caption=caption, parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
                )
            )
            os.remove(file_name)

        os.remove(file_path)
        if temp_msg:
            await temp_msg.delete()

    except Exception as e:
        LOGGER.error(f"Error processing file for {args[0] if 'args' in locals() and args else '/adbin'}: {str(e)}")
        await client.send_message(
            message.chat.id,
            "**❌ Error processing file**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join For Updates", url=UPDATE_CHANNEL_URL)]]
            )
        )
        await notify_admin(client, args[0] if 'args' in locals() and args else "/adbin", e, message)
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if temp_msg:
            await temp_msg.delete()

def setup_binf_handlers(app: Client):
    app.add_handler(
        handlers.MessageHandler(
            handle_bin_commands,
            filters.command(["adbin", "rmbin"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        )
    )
