import os
import time
import logging
from collections import Counter
from pyrogram import Client, filters, handlers
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from config import COMMAND_PREFIX, MAX_TXT_SIZE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Command to display top bins from a file
async def handle_topbin_command(client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.document or not message.reply_to_message.document.file_name.endswith('.txt'):
        await client.send_message(message.chat.id, "<b>Reply to a text file containing credit cards to check top bins❌</b>", parse_mode=ParseMode.HTML)
        logging.warning("No valid text file provided for checking top bins.")
        return

    file_size_mb = message.reply_to_message.document.file_size / (1024 * 1024)
    if file_size_mb > MAX_TXT_SIZE:
        await client.send_message(message.chat.id, "<b>File size exceeds the 15MB limit❌</b>", parse_mode=ParseMode.HTML)
        logging.warning("File size exceeds the 15MB limit.")
        return

    temp_msg = await client.send_message(message.chat.id, "<b>Finding Top Bins...</b>", parse_mode=ParseMode.HTML)
    start_time = time.time()
    file_path = await message.reply_to_message.download()
    logging.info(f"Downloaded file to {file_path}")
    with open(file_path, 'r') as file:
        content = file.readlines()

    bin_counter = Counter([line.strip()[:6] for line in content if len(line.strip()) >= 6])
    top_bins = bin_counter.most_common(20)
    end_time = time.time()
    time_taken = end_time - start_time

    if not top_bins:
        await temp_msg.delete()
        await client.send_message(message.chat.id, "<b>❌ No BIN data found in the file.</b>", parse_mode=ParseMode.HTML)
        logging.info("No BIN data found in the file.")
        os.remove(file_path)
        return

    if message.from_user:
        user_full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        user_profile_url = f"https://t.me/{message.from_user.username}" if message.from_user.username else None
        user_link = f'<a href="{user_profile_url}">{user_full_name}</a>' if user_profile_url else user_full_name
    else:
        group_name = message.chat.title or "this group"
        group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "this group"
        user_link = f'<a href="{group_url}">{group_name}</a>'

    response_message = (
        f"<b>Here are the top 20 bins:</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
    )
    for i, (bin, count) in enumerate(top_bins, 1):
        response_message += f"{i:02d}. BIN: <code>{bin}</code> - Count: <code>{count}</code>\n"

    response_message += (
        f"\n<b>Checked By:</b> {user_link}\n"
        f"<b>Time taken to validate:</b> <code>{time_taken:.2f} seconds</code>\n"
        f"<b>📝 Extra Info:</b> <code>Use responsibly</code>\n"
        f"<b>🔍 Verified:</b> <code>Yes</code>"
    )

    await temp_msg.delete()
    await client.send_message(message.chat.id, response_message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    logging.info("Top bins sent to the chat.")
    os.remove(file_path)
    logging.info(f"Temporary file {file_path} removed.")

# Setup handler for topbin command
def setup_topbin_handler(app: Client):
    app.add_handler(handlers.MessageHandler(handle_topbin_command, filters.command(["topbin"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)))