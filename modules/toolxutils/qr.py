#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message
import aiohttp  # Import aiohttp for asynchronous HTTP requests
import asyncio
import logging
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def fetch_qr_image(qr_url: str):
    # Create an asynchronous HTTP session to fetch the QR code image URL
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.teleservices.io/QR/?message={qr_url}&logo=https://abirthetech.serv00.net/abir.jpg&body=dot&eye=frame2&eyeBall=ball5&gradientColor1=%2300FF29&gradientColor2=%23000000&gradientType=gradient&gradientOnEyes=false&file=png",
                timeout=10
            ) as response:
                if response.status == 200:
                    return await response.json()  # Return the JSON response
                else:
                    raise Exception(f"Failed to fetch QR code: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error fetching QR code: {e}")
        raise

def setup_qr_handler(app):
    @app.on_message(filters.command(["qr"], prefixes=COMMAND_PREFIX) & (filters.group | filters.private))
    async def qr_dl(client: Client, message: Message):
        ID = message.from_user.id
        FIRST = message.from_user.first_name or 'N/A'
        LAST = message.from_user.last_name or ''
        qr_url = message.text[len('/qr '):].strip()

        # Check if QR URL is too short (less than 6 characters)
        if len(qr_url) < 6:
            await client.send_message(
                chat_id=message.chat.id,
                text='<b>Please provide a QR text!</b>',
                parse_mode="HTML"
            )
            return

        # Send an initial message to inform the user the process is happening
        mafia = await client.send_message(
            chat_id=message.chat.id,
            text="<b>Fetching QR link details...✨</b>",
            parse_mode="HTML"
        )

        try:
            # Fetch QR image details asynchronously
            qr_data = await fetch_qr_image(qr_url)
            qr_pic = qr_data["qrImageUrl"]
            ms = qr_data["message"]

            # Send the QR code image to the chat
            await client.send_photo(
                chat_id=message.chat.id,
                photo=qr_pic,
                caption=f'''
<strong><b>🔍 QR Details 📋</b>
<b>━━━━━━━━━━━━━━━━━━</b>
<b>• Message: </b><code>{ms}</code>
<b>• File Type: </b><code>PNG</code>

<b>↠ Requested By: </b><a href="tg://user?id={ID}">{FIRST} {LAST}</a></strong>
''',
                parse_mode="HTML"
            )
            # Delete the "Fetching" message
            await mafia.delete()

        except Exception as e:
            # Update with error message if something goes wrong
            error_msg = "<b>Qr Code Gen API Dead</b>"
            await mafia.edit(error_msg, parse_mode="HTML")
            logger.error(f"Error in qr_dl handler: {e}")
            # Notify admins of error
            await notify_admin(client, "/qr", e, message)
