# Copyright @ISmartCoder
# Updates Channel: https://t.me/TheSmartDev

import os
import asyncio
import base64
import binascii
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER, notify_admin
from core import banned_users

def setup_decoders_handler(app: Client):
    commands = {
        "b64en": lambda text: base64.b64encode(text.encode()).decode(),
        "b64de": lambda text: base64.b64decode(text).decode(),
        "b32en": lambda text: base64.b32encode(text.encode()).decode(),
        "b32de": lambda text: base64.b32decode(text).decode(),
        "binen": lambda text: ' '.join(format(ord(char), '08b') for char in text),
        "binde": lambda text: ''.join(chr(int(b, 2)) for b in text.split()),
        "hexen": lambda text: binascii.hexlify(text.encode()).decode(),
        "hexde": lambda text: binascii.unhexlify(text).decode(),
        "octen": lambda text: ' '.join(format(ord(char), '03o') for char in text),
        "octde": lambda text: ''.join(chr(int(o, 8)) for o in text.split()),
        "trev": lambda text: text[::-1],
        "tcap": lambda text: text.upper(),
        "tsm": lambda text: text.lower(),
        "wc": lambda text: (
            "<b>📊 Text Counter</b>\n\n"
            "<b>✅ Words:</b> <code>{}</code>\n"
            "<b>✅ Characters:</b> <code>{}</code>\n"
            "<b>✅ Sentences:</b> <code>{}</code>\n"
            "<b>✅ Paragraphs:</b> <code>{}</code>".format(
                len(text.split()),
                len(text),
                text.count('.') + text.count('!') + text.count('?'),
                text.count('\n') + 1
            )
        )
    }

    for command, func in commands.items():
        @app.on_message(filters.command([command], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
        async def handle_command(client, message, func=func, command=command):
            user_id = message.from_user.id if message.from_user else None
            if user_id and await banned_users.find_one({"user_id": user_id}):
                await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
                LOGGER.info(f"Banned user {user_id} attempted to use /{command}")
                return

            processing_msg = await client.send_message(message.chat.id, "<b>Processing Your Input...✨</b>", parse_mode=ParseMode.HTML)

            try:
                text = None

                if message.reply_to_message:
                    if message.reply_to_message.document:
                        file_path = await client.download_media(message.reply_to_message.document)
                        with open(file_path, "r", encoding="utf-8") as file:
                            text = file.read()
                        os.remove(file_path)
                    else:
                        text = message.reply_to_message.text
                else:
                    text = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else None

                if not text:
                    await client.send_message(message.chat.id, "<b>⚠️ Please provide text or reply to a message/file❌</b>", parse_mode=ParseMode.HTML)
                    await processing_msg.delete()
                    LOGGER.warning(f"No text provided for /{command} by user {user_id or 'unknown'} in chat {message.chat.id}")
                    return

                result = func(text)

                if message.from_user:
                    user_full_name = message.from_user.first_name + (" " + message.from_user.last_name if message.from_user.last_name else "")
                    user_profile_url = f"tg://user?id={message.from_user.id}"
                    user_mention = f"<a href='{user_profile_url}'>{user_full_name}</a>"
                else:
                    user_mention = "<a href='https://t.me/ItsSmartToolBot'>ItsSmartToolBot</a>"

                LOGGER.info(f"Processed /{command} for user {user_id or 'unknown'} in chat {message.chat.id}")

                if len(result) > 4096:
                    file_name = f"{command}_result.txt"
                    with open(file_name, "w", encoding="utf-8") as file:
                        file.write(result)

                    await client.send_document(
                        message.chat.id,
                        file_name,
                        caption=f"✨ <b>Here is your processed file!</b> ✨\n\n"
                                f"📂 <b>Command Used:</b> <code>{command}</code>\n"
                                f"📝 <b>Requested By:</b> {user_mention}\n"
                                f"📜 <b>Processed Successfully!</b> ✅",
                        parse_mode=ParseMode.HTML
                    )
                    os.remove(file_name)
                else:
                    await client.send_message(
                        message.chat.id,
                        f"<b>✅ {command} Result:</b>\n<code>{result}</code>" if command != "wc" else result,
                        parse_mode=ParseMode.HTML
                    )

            except Exception as e:
                LOGGER.error(f"Error processing /{command} for user {user_id or 'unknown'} in chat {message.chat.id}: {str(e)}")
                await notify_admin(client, f"/{command}", e, message)
                await client.send_message(
                    message.chat.id,
                    "<b>❌ Sorry Bro, Invalid Text Provided!</b>",
                    parse_mode=ParseMode.HTML
                )

            await processing_msg.delete()
