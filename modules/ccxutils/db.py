#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from core import banned_users

# Define the BIN databases for each country
bin_databases = {
    "Bangladesh": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "BD Bin Database\n\n"
        "BIN: `400462`\n**Bank:** PUBALI BANK, LTD.\n**Country:** BD\n\n"
        "BIN: `400465`\n**Bank:** PUBALI BANK, LTD.\n**Country:** BD\n\n"
        "BIN: `400468`\n**Bank:** PUBALI BANK, LTD.\n**Country:** BD\n\n"
        "BIN: `400469`\n**Bank:** PUBALI BANK, LTD.\n**Country:** BD\n\n"
        "BIN: `400470`\n**Bank:** PUBALI BANK, LTD.\n**Country:** BD",
        "https://telegra.ph/Smart-Tool-01-17"
    ),
    "Algeria": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Algeria Bin Database\n\n"
        "BIN: `400622`\n**Bank:** BANQUE EXTERIEURE D'ALGERIE\n**Country:** DZ\n\n"
        "BIN: `400946`\n**Bank:** SOCIETE GENERALE ALGERIE\n**Country:** DZ\n\n"
        "BIN: `405060`\n**Bank:** SOCIETE GENERALE ALGERIE\n**Country:** DZ\n\n"
        "BIN: `417203`\n**Bank:** CREDIT POPULAIRE D'ALGERIE\n**Country:** DZ\n\n"
        "BIN: `417217`\n**Bank:** CREDIT POPULAIRE D'ALGERIE\n**Country:** DZ\n\n"
        "BIN: `417231`\n**Bank:** CREDIT POPULAIRE D'ALGERIE\n**Country:** DZ",
        "https://telegra.ph/Smart-Tool-01-17-2"
    ),
    "India": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "India Bin Database\n\n"
        "BIN: `400016`\n**Bank:** STATE BANK OF INDIA\n**Country:** IN\n\n"
        "BIN: `400017`\n**Bank:** STATE BANK OF INDIA\n**Country:** IN\n\n"
        "BIN: `400018`\n**Bank:** STATE BANK OF INDIA\n**Country:** IN\n\n"
        "BIN: `400019`\n**Bank:** STATE BANK OF INDIA\n**Country:** IN\n\n"
        "BIN: `400032`\n**Bank:** STATE BANK OF INDIA\n**Country:** IN",
        "https://telegra.ph/Smart-Tool-01-17-3"
    ),
    "China": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "China Bin Database\n\n"
        "BIN: `400201`\n**Bank:** YUANTA COMMERCIAL BANK CO., LTD.\n**Country:** TW\n\n"
        "BIN: `400211`\n**Bank:** YUANTA COMMERCIAL BANK CO., LTD.\n**Country:** TW\n\n"
        "BIN: `400212`\n**Bank:** CITIBANK, N.A.\n**Country:** CN\n\n"
        "BIN: `400221`\n**Bank:** BANK OF CHINA\n**Country:** CN\n\n"
        "BIN: `400292`\n**Bank:** BANK OF CHINA\n**Country:** CN\n\n"
        "BIN: `400353`\n**Bank:** MEGA INTERNATIONAL COMMERCIAL BANK CO., LTD.\n**Country:** TW",
        "https://telegra.ph/Smart-Tool-01-17-4"
    ),
    "Brazil": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Brazil Bin Database\n\n"
        "BIN: `400102`\n**Bank:** BANCO DO BRASIL, S.A.\n**Country:** BR\n\n"
        "BIN: `400106`\n**Bank:** BANCO DO BRASIL, S.A.\n**Country:** BR\n\n"
        "BIN: `400107`\n**Bank:** BANCO DO BRASIL, S.A.\n**Country:** BR\n\n"
        "BIN: `400130`\n**Bank:** BANCO DO BRASIL, S.A.\n**Country:** BR\n\n"
        "BIN: `400136`\n**Bank:** BANCO DO BRASIL, S.A.\n**Country:** BR",
        "https://telegra.ph/Smart-Tool-01-17-5"
    ),
    "Argentina": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Argentina Bin Database\n\n"
        "BIN: `400103`\n**Bank:** VISA ARGENTINA, S.A.\n**Country:** AR\n\n"
        "BIN: `400104`\n**Bank:** VISA ARGENTINA, S.A.\n**Country:** AR\n\n"
        "BIN: `400276`\n**Bank:** VISA ARGENTINA, S.A.\n**Country:** AR\n\n"
        "BIN: `400440`\n**Bank:** CAJA POPULAR DE AHORROS DE LA PROVINCIA DE TUCUMAN\n**Country:** AR\n\n"
        "BIN: `400448`\n**Bank:** CITIBANK\n**Country:** AR",
        "https://telegra.ph/Smart-Tool-01-17-6"
    ),
    "Japan": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Japan Bin Database\n\n"
        "BIN: `400142`\n**Bank:** SONY BANK, INC.\n**Country:** JP\n\n"
        "BIN: `400673`\n**Bank:** MUFG BANK, LTD\n**Country:** JP\n\n"
        "BIN: `401924`\n**Bank:** VANDLE CARD\n**Country:** JP\n\n"
        "BIN: `402854`\n**Bank:** CITI CARDS JAPAN, INC.\n**Country:** JP\n\n"
        "BIN: `405283`\n**Bank:** INTERPAYMENT SERVICES, LTD.\n**Country:** JP",
        "https://telegra.ph/Smart-Tool-01-17-7"
    ),
    "Mexico": (
        "Smart Tool ⚙️ - Bin database 📋\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Mexico Bin Database\n\n"
        "BIN: `400443`\n**Bank:** BANCO INBURSA S.A. INSTITUCION DE BANCA MULTIPLE GRUPO FINANCIERO INBURSA\n**Country:** MX\n\n"
        "BIN: `400523`\n**Bank:** BANCO AUTOFIN MEXICO, S.A.\n**Country:** MX\n\n"
        "BIN: `400819`\n**Bank:** BANCOPPEL S.A. INSTITUCION DE BANCA MULTIPLE\n**Country:** MX\n\n"
        "BIN: `400829`\n**Bank:** BANCA MIFEL, S.A.\n**Country:** MX\n\n"
        "BIN: `400994`\n**Bank:** BANCO NACIONAL DE MEXICO, S.A.\n**Country:** MX",
        "https://telegra.ph/Smart-Tool-01-17-8"
    ),
}

# List of accepted countries
accepted_countries = ["Bangladesh", "India", "Algeria", "China", "Brazil", "Brasil", "Argentina", "Japan", "Mexico"]

def setup_db_handlers(app: Client):
    @app.on_message(filters.command(["bindb"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def bindb_handler(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘ Sorry You're Banned From Using Me ↯**")
            return

        user_input = message.text.split(maxsplit=1)
        if len(user_input) == 1:
            await client.send_message(message.chat.id, "**Please provide a full country name for bin database ❌**")
            return

        country = user_input[1].capitalize()
        if country not in accepted_countries:
            await client.send_message(message.chat.id, "**Please provide a valid country name ❌**")
            return

        fetching_message = await client.send_message(message.chat.id, f"**Fetching Bins Database For Your Country Name**")

        # Simulate fetching delay
        await asyncio.sleep(2)

        await fetching_message.delete()

        # Handle the case where "Brasil" is used instead of "Brazil"
        if country == "Brasil":
            country = "Brazil"

        bin_data, url = bin_databases[country]
        button = InlineKeyboardButton("Full Output", url=url)
        reply_markup = InlineKeyboardMarkup([[button]])

        await client.send_message(message.chat.id, f"**{bin_data}**", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
