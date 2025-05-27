# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import COMMAND_PREFIX, MAX_TXT_SIZE
from utils import LOGGER
from core import banned_users  # Add banned user check

def process_file(file_path, line_limit):
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    total_lines = len(lines)
    split_files = []
    file_index = 1
    
    for start in range(0, total_lines, line_limit):
        end = start + line_limit
        split_file_path = f"{file_path}_part_{file_index}.txt"
        with open(split_file_path, "w") as split_file:
            split_file.writelines(lines[start:end])
        split_files.append(split_file_path)
        file_index += 1
    
    return split_files

def setup_txt_handler(app: Client):
    executor = ThreadPoolExecutor(max_workers=4)
    
    @app.on_message(filters.command(["sptxt"], prefixes=COMMAND_PREFIX) & filters.private)
    async def split_text(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await message.reply_text("**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            return

        if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith(".txt"):
            await message.reply_text("⚠️ **Please Reply To A Txt File And Give Amount To Split**", parse_mode=ParseMode.MARKDOWN)
            return

        file_size_mb = message.reply_to_message.document.file_size / (1024 * 1024)
        if file_size_mb > MAX_TXT_SIZE:
            await message.reply_text("⚠️ **File size exceeds the 10MB limit❌**", parse_mode=ParseMode.MARKDOWN)
            return

        try:
            line_limit = int(message.command[1])
        except (IndexError, ValueError):
            await message.reply_text("⚠️ **Please Provide A Valid Line Limit**", parse_mode=ParseMode.MARKDOWN)
            return

        processing_msg = await message.reply_text("**Processing Text Split..✨**", parse_mode=ParseMode.MARKDOWN)

        # Download the file asynchronously
        file_path = await client.download_media(message.reply_to_message.document)

        # Process the file in a worker thread
        split_files = await app.loop.run_in_executor(executor, process_file, file_path, line_limit)

        # Delete the processing message before sending files
        await processing_msg.delete()

        # Send the split files to the user asynchronously
        for split_file in split_files:
            await client.send_document(message.chat.id, split_file)
            os.remove(split_file)

        # Remove the original file
        os.remove(file_path)

    @app.on_message(filters.command(["sptxt"], prefixes=COMMAND_PREFIX) & ~filters.private)
    async def notify_private_chat(client: Client, message: Message):
        await message.reply_text("**You only can Split text in private chat⚠️**", parse_mode=ParseMode.MARKDOWN)