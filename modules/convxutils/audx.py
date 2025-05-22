#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from pydub import AudioSegment
from config import COMMAND_PREFIX

# --- Command Handler ---
async def handle_voice_command(client: Client, message: Message):
    if not message.reply_to_message:
        await client.send_message(
            chat_id=message.chat.id,
            text="**Please reply to an audio message.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    reply = message.reply_to_message

    # Check valid audio
    if not (reply.audio or reply.voice or reply.document):
        await client.send_message(
            chat_id=message.chat.id,
            text="**⚠️ Please reply to a valid audio file.**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Get file extension (for document/audio)
    file_extension = ""
    if reply.audio and reply.audio.file_name:
        file_extension = reply.audio.file_name.split('.')[-1].lower()
    elif reply.document and reply.document.file_name:
        file_extension = reply.document.file_name.split('.')[-1].lower()

    valid_audio_extensions = ['mp3', 'wav', 'ogg', 'm4a']
    if file_extension and file_extension not in valid_audio_extensions:
        await client.send_message(
            chat_id=message.chat.id,
            text="**⚠️ Please reply to a valid audio file**",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Processing message
    processing_message = await client.send_message(
        chat_id=message.chat.id,
        text="**Converting Mp3 To Voice Message✨..**",
        parse_mode=ParseMode.MARKDOWN
    )

    input_path = f"downloads/input.{file_extension if file_extension else 'ogg'}"
    output_path = "downloads/output.ogg"
    os.makedirs("downloads", exist_ok=True)

    try:
        # Download the file directly using Pyrogram's download
        await reply.download(input_path)

        # Convert to Telegram-compatible voice message
        await convert_audio(input_path, output_path)

        # Delete processing message before sending final voice message
        await processing_message.delete()

        # Send the final voice message (direct send, no reply)
        await client.send_voice(
            chat_id=message.chat.id,
            voice=output_path,
            caption=""
        )

    except Exception as e:
        await processing_message.edit_text(
            f"**Sorry Failed To Convert✨**",
            parse_mode=ParseMode.MARKDOWN
        )

    finally:
        # Clean up downloaded and processed files
        await cleanup_files(input_path, output_path)


async def convert_audio(input_path, output_path):
    """Convert the audio file to OGG OPUS format (Telegram voice message format)."""
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="ogg", codec="libopus")


async def cleanup_files(*files):
    """Remove files after processing."""
    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"Failed to remove {file}: {e}")


def setup_voice_handler(app: Client):
    """Register the /voice command handler."""
    app.add_handler(MessageHandler(
        handle_voice_command,
        filters.command(["voice"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
    ))