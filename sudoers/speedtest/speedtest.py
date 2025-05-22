# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import asyncio
import subprocess
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import OWNER_IDS, COMMAND_PREFIX, UPDATE_CHANNEL_URL

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to convert speed to human-readable format
def speed_convert(size: float, is_mbps: bool = False) -> str:
    """Convert speed to human-readable format (bps or Mbps)."""
    if is_mbps:
        return f"{size:.2f} Mbps"
    power = 2**10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}bps"

# Helper function to convert bytes to human-readable file size
def get_readable_file_size(size_in_bytes: int) -> str:
    """Convert bytes to human-readable file size (B, KB, MB, etc.)."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size_in_bytes >= power:
        size_in_bytes /= power
        n += 1
    return f"{size_in_bytes:.2f} {power_labels[n]}"

# Function to perform speed test
def run_speedtest():
    """Run speedtest-cli and return JSON result."""
    try:
        result = subprocess.run(
            ["speedtest-cli", "--secure", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data
    except subprocess.CalledProcessError as e:
        logger.error(f"Speedtest failed: {e.stderr}")
        return {"error": f"Speedtest failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse speedtest JSON: {e}")
        return {"error": "Invalid speedtest output format"}
    except Exception as e:
        logger.error(f"Unexpected error during speedtest: {e}")
        return {"error": str(e)}

# Async function to handle speed test logic
async def run_speedtest_task(client: Client, chat_id: int, status_message: Message):
    """Run speed test in background and send results."""
    logger.info(f"Running speedtest for chat {chat_id}")
    with ThreadPoolExecutor() as pool:
        try:
            result = await asyncio.get_running_loop().run_in_executor(pool, run_speedtest)
        except Exception as e:
            logger.error(f"Error running speedtest: {e}")
            return await status_message.edit_text(
                "<b>✘ Speed Test Failed: Server Error ↯</b>",
                parse_mode=ParseMode.HTML
            )

    if "error" in result:
        return await status_message.edit_text(
            f"<b>✘ Speed Test Failed: {result['error']} ↯</b>",
            parse_mode=ParseMode.HTML
        )

    # Format the results with a stylized design
    response_text = (
        "<b>✘《 💥 SPEEDTEST RESULTS ↯ 》</b>\n"
        f"↯ <b>Upload Speed:</b> <code>{speed_convert(result['upload'])}</code>\n"
        f"↯ <b>Download Speed:</b> <code>{speed_convert(result['download'])}</code>\n"
        f"↯ <b>Ping:</b> <code>{result['ping']:.2f} ms</code>\n"
        f"↯ <b>Timestamp:</b> <code>{result['timestamp']}</code>\n"
        f"↯ <b>Data Sent:</b> <code>{get_readable_file_size(int(result['bytes_sent']))}</code>\n"
        f"↯ <b>Data Received:</b> <code>{get_readable_file_size(int(result['bytes_received']))}</code>\n"
        "<b>✘《 🌐 SERVER INFO ↯ 》</b>\n"
        f"↯ <b>Name:</b> <code>{result['server']['name']}</code>\n"
        f"↯ <b>Country:</b> <code>{result['server']['country']}, {result['server']['cc']}</code>\n"
        f"↯ <b>Sponsor:</b> <code>{result['server']['sponsor']}</code>\n"
        f"↯ <b>Latency:</b> <code>{result['server']['latency']:.2f} ms</code>\n"
        f"↯ <b>Latitude:</b> <code>{result['server']['lat']}</code>\n"
        f"↯ <b>Longitude:</b> <code>{result['server']['lon']}</code>\n"
        "<b>✘《 👾 CLIENT INFO ↯ 》</b>\n"
        f"↯ <b>IP Address:</b> <code>{result['client']['ip']}</code>\n"
        f"↯ <b>Latitude:</b> <code>{result['client']['lat']}</code>\n"
        f"↯ <b>Longitude:</b> <code>{result['client']['lon']}</code>\n"
        f"↯ <b>Country:</b> <code>{result['client']['country']}</code>\n"
        f"↯ <b>ISP:</b> <code>{result['client']['isp']}</code>\n"
        f"↯ <b>ISP Rating:</b> <code>{result['client'].get('isprating', 'N/A')}</code>\n"
        "<b>✘ Powered by @TheSmartDev ↯</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Update News", url=UPDATE_CHANNEL_URL)]
    ])

    await status_message.delete()
    return await client.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

# Handler for speed test command
async def speedtest_handler(client: Client, message: Message):
    """Handle /speedtest command to initiate a server speed test."""
    user_id = message.from_user.id
    logger.info(f"Speedtest command from user {user_id}")
    if user_id not in OWNER_IDS:
        logger.info("User not admin, sending restricted message")
        return await client.send_message(
            chat_id=message.chat.id,
            text="<b>✘Kids Not Allowed To Do This↯</b>",
            parse_mode=ParseMode.HTML
        )

    status_message = await client.send_message(
        chat_id=message.chat.id,
        text="<b>✘ Running Speedtest On Your Server ↯</b>",
        parse_mode=ParseMode.HTML
    )

    # Schedule the speed test task
    asyncio.create_task(run_speedtest_task(client, message.chat.id, status_message))
    return status_message

# Setup function to add the speed test handler
def setup_speed_handler(app: Client):
    """Set up the speed test handler for the bot."""
    logger.info("Setting up speedtest handler")
    app.add_handler(MessageHandler(
        speedtest_handler,
        filters.command("speedtest", prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
    ))

