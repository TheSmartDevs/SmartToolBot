import asyncio
import os
import re
import shutil
import tempfile
import uuid
from PIL import Image
from pyrogram import Client, emoji, enums, filters
from pyrogram.errors import BadRequest, PeerIdInvalid, StickersetInvalid
from pyrogram.file_id import FileId
from pyrogram.raw.functions.messages import GetStickerSet, SendMedia
from pyrogram.raw.functions.stickers import AddStickerToSet, CreateStickerSet
from pyrogram.raw.types import DocumentAttributeFilename, InputDocument, InputMediaUploadedDocument, InputStickerSetItem, InputStickerSetShortName
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import BOT_TOKEN, COMMAND_PREFIX, BAN_REPLY
from utils import LOGGER
from core import banned_users

def get_emoji_regex():
    e_list = [getattr(emoji, e).encode("unicode-escape").decode("ASCII") for e in dir(emoji) if not e.startswith("_")]
    e_sort = sorted([x for x in e_list if not x.startswith("*")], reverse=True)
    pattern_ = f"({'|'.join(e_sort)})"
    return re.compile(pattern_)

EMOJI_PATTERN = get_emoji_regex()

async def resize_png_for_sticker(input_file: str, output_file: str):
    try:
        with Image.open(input_file) as im:
            width, height = im.size
            if width == 512 or height == 512:
                im.save(output_file, "PNG", optimize=True)
                return output_file
            if width > height:
                new_width = 512
                new_height = int((512 / width) * height)
            else:
                new_height = 512
                new_width = int((512 / height) * width)
            im = im.resize((new_width, new_height), Image.Resampling.LANCZOS)
            im.save(output_file, "PNG", optimize=True)
            return output_file
    except Exception as e:
        LOGGER.error(f"Error resizing PNG: {str(e)}")
        return None

async def process_video_sticker(input_file: str, output_file: str):
    try:
        command = [
            "ffmpeg", "-i", input_file,
            "-t", "3",
            "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2,fps=24",
            "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "150k",
            "-an", "-y",
            output_file
        ]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            LOGGER.error(f"FFmpeg error: {stderr.decode()}")
            return None
        if os.path.exists(output_file) and os.path.getsize(output_file) > 256 * 1024:
            LOGGER.warning("File size exceeds 256KB, re-encoding with lower quality")
            command[-3] = "-b:v"
            command[-2] = "100k"
            process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                LOGGER.error(f"FFmpeg error: {stderr.decode()}")
                return None
        return output_file
    except Exception as e:
        LOGGER.error(f"Error processing video: {str(e)}")
        return None

async def process_gif_to_webm(input_file: str, output_file: str):
    try:
        command = [
            "ffmpeg", "-i", input_file,
            "-t", "3",
            "-vf", "scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2,fps=24",
            "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "150k",
            "-an", "-y",
            output_file
        ]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            LOGGER.error(f"FFmpeg error: {stderr.decode()}")
            return None
        if os.path.exists(output_file) and os.path.getsize(output_file) > 256 * 1024:
            LOGGER.warning("File size exceeds 256KB, re-encoding with lower quality")
            command[-3] = "-b:v"
            command[-2] = "100k"
            process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                LOGGER.error(f"FFmpeg error: {stderr.decode()}")
                return None
        return output_file
    except Exception as e:
        LOGGER.error(f"Error processing GIF: {str(e)}")
        return None

def setup_kang_handler(app: Client):
    @app.on_message(filters.command(["kang"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def kang(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=enums.ParseMode.MARKDOWN)
            return

        user = message.from_user
        packnum = 1
        packname = f"a{user.id}_by_{client.me.username}"
        max_stickers = 120
        temp_files = []

        temp_message = await client.send_message(chat_id=message.chat.id, text="<b>Kanging this Sticker...✨</b>")

        while packnum <= 100:
            try:
                stickerset = await client.invoke(GetStickerSet(stickerset=InputStickerSetShortName(short_name=packname), hash=0))
                if stickerset.set.count < max_stickers:
                    break
                packnum += 1
                packname = f"a{packnum}_{user.id}_by_{client.me.username}"
            except StickersetInvalid:
                break

        if not message.reply_to_message:
            await temp_message.edit_text("<b>Please reply to a sticker, image, or document to kang it!</b>")
            return

        reply = message.reply_to_message
        if reply.sticker:
            file_id = reply.sticker.file_id
        elif reply.photo:
            file_id = reply.photo.file_id
        elif reply.document:
            file_id = reply.document.file_id
        elif reply.animation:
            file_id = reply.animation.file_id
        else:
            await temp_message.edit_text("<b>Please reply to a valid sticker, image, GIF, or document!</b>")
            return

        sticker_format = "png"
        if reply.sticker:
            if reply.sticker.is_animated:
                sticker_format = "tgs"
            elif reply.sticker.is_video:
                sticker_format = "webm"
        elif reply.animation or (reply.document and reply.document.mime_type == "image/gif"):
            sticker_format = "gif"

        try:
            file_name = f"kangsticker_{uuid.uuid4().hex}"
            if sticker_format == "tgs":
                kang_file = await app.download_media(file_id, file_name=f"{file_name}.tgs")
            elif sticker_format == "webm":
                kang_file = await app.download_media(file_id, file_name=f"{file_name}.webm")
            elif sticker_format == "gif":
                kang_file = await app.download_media(file_id, file_name=f"{file_name}.gif")
            else:
                kang_file = await app.download_media(file_id, file_name=f"{file_name}.png")
            
            if not kang_file:
                await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                return
            
            temp_files.append(kang_file)

        except Exception as e:
            LOGGER.error(f"Download error: {str(e)}")
            await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
            return

        sticker_emoji = "🌟"
        if len(message.command) > 1:
            emoji_matches = "".join(set(EMOJI_PATTERN.findall("".join(message.command[1:]))))
            sticker_emoji = emoji_matches or sticker_emoji
        elif reply.sticker and reply.sticker.emoji:
            sticker_emoji = reply.sticker.emoji

        full_name = user.first_name
        if user.last_name:
            full_name += f" {user.last_name}"
        pack_title = f"{full_name}'s Pack"

        try:
            if sticker_format == "png":
                output_file = f"resized_{uuid.uuid4().hex}.png"
                processed_file = await resize_png_for_sticker(kang_file, output_file)
                if not processed_file:
                    await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                    return
                kang_file = processed_file
                temp_files.append(kang_file)
            
            elif sticker_format == "gif":
                output_file = f"compressed_{uuid.uuid4().hex}.webm"
                processed_file = await process_gif_to_webm(kang_file, output_file)
                if not processed_file:
                    await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                    return
                kang_file = output_file
                sticker_format = "webm"
                temp_files.append(kang_file)
            
            elif sticker_format == "webm":
                output_file = f"compressed_{uuid.uuid4().hex}.webm"
                processed_file = await process_video_sticker(kang_file, output_file)
                if not processed_file:
                    await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
                    return
                kang_file = output_file
                temp_files.append(kang_file)

            file = await client.save_file(kang_file)
            media = await client.invoke(
                SendMedia(
                    peer=(await client.resolve_peer(message.chat.id)),
                    media=InputMediaUploadedDocument(
                        file=file,
                        mime_type=client.guess_mime_type(kang_file),
                        attributes=[DocumentAttributeFilename(file_name=os.path.basename(kang_file))],
                    ),
                    message=f"#Sticker kang by UserID -> {user.id}",
                    random_id=client.rnd_id(),
                )
            )
            msg_ = media.updates[-1].message
            stkr_file = msg_.media.document

            try:
                await client.invoke(
                    AddStickerToSet(
                        stickerset=InputStickerSetShortName(short_name=packname),
                        sticker=InputStickerSetItem(
                            document=InputDocument(
                                id=stkr_file.id,
                                access_hash=stkr_file.access_hash,
                                file_reference=stkr_file.file_reference,
                            ),
                            emoji=sticker_emoji,
                        ),
                    )
                )
            except StickersetInvalid:
                await client.invoke(
                    CreateStickerSet(
                        user_id=await client.resolve_peer(user.id),
                        title=pack_title,
                        short_name=packname,
                        stickers=[
                            InputStickerSetItem(
                                document=InputDocument(
                                    id=stkr_file.id,
                                    access_hash=stkr_file.access_hash,
                                    file_reference=stkr_file.file_reference,
                                ),
                                emoji=sticker_emoji,
                            )
                        ],
                    )
                )

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("View Sticker Pack", url=f"t.me/addstickers/{packname}")]])
            await temp_message.edit_text(
                f"**Sticker Kanged Successful! ✅**\n**Sticker Emoji: {sticker_emoji}**\n**Sticker Pack Name: {pack_title}**",
                reply_markup=keyboard
            )

            await client.delete_messages(chat_id=message.chat.id, message_ids=msg_.id, revoke=True)

        except Exception as e:
            LOGGER.error(f"Error adding sticker: {str(e)}")
            await temp_message.edit_text("<b>❌ Failed To Kang The Sticker</b>")
        
        finally:
            for file in temp_files:
                try:
                    os.remove(file)
                except:
                    LOGGER.warning(f"Failed to remove temporary file: {file}")
