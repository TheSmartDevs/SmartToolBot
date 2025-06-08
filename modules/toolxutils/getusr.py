from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatType
from config import COMMAND_PREFIX
from core import banned_users
from utils import notify_admin
import aiohttp
import aiofiles
import json
import os

def setup_getusr_handler(app: Client):
    @app.on_message(filters.command(["getusers"], prefixes=COMMAND_PREFIX))
    async def usr_handler(client: Client, message):
        user_id = message.from_user.id

        if banned_users.find_one({"user_id": user_id}):
            await client.send_message(
                message.chat.id,
                "✘ Sorry, You're Banned From Using Me ↯",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await client.send_message(
                message.chat.id,
                "You Can Only Get Users In Private Chats",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        args = message.text.split()
        if len(args) < 2:
            await client.send_message(
                message.chat.id,
                "❌ Please Provide The Bot Token After The Command",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        bot_token = args[1]
        loading = await client.send_message(
            message.chat.id,
            "Fetching Peers.....",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.safone.co/tgusers?bot_token={bot_token}") as resp:
                    if resp.status != 200:
                        await client.edit_message_text(
                            message.chat.id,
                            loading.id,
                            "❌ Invalid Bot Token Provided",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        return
                    data = await resp.json()
        except Exception:
            await client.edit_message_text(
                message.chat.id,
                loading.id,
                "❌ Invalid Bot Token Provided",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        file_path = f"/tmp/users_{user_id}.json"
        try:
            async with aiofiles.open(file_path, mode='w') as f:
                await f.write(json.dumps(data, indent=4))

            bot_info = data.get("bot_info", {})
            stats = data.get("stats", {})

            caption = (
                "📌 Requested Users\n"
                "━━━━━━━━\n"
                f"👤 Username: ` {bot_info.get('username', 'N/A')} `\n"
                f"👥 Total Users: `{stats.get('total_users', 0)} `\n"
                "━━━━━━━━\n"
                "📂 File contains user & chat IDs."
            )

            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await client.edit_message_text(
                message.chat.id,
                loading.id,
                "❌ Invalid Bot Token Provided",
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            await loading.delete()
            if os.path.exists(file_path):
                os.remove(file_path)
