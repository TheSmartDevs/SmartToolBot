# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import aiohttp
import asyncio
import base64
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType, ChatAction
from pyrogram.raw.functions.users import GetFullUser
from PIL import Image
from config import COMMAND_PREFIX, PROFILE_ERROR_URL
from utils import LOGGER  # Import LOGGER from utils
from core import banned_users  # Check if user is banned
import json

# Use the imported LOGGER
logger = LOGGER

# Semaphore to limit concurrent tasks
MAX_CONCURRENT_TASKS = 5
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def download_default_avatar(client, url, session):
    async with semaphore:
        if "t.me/" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                chat_username = parts[3]
                message_id = int(parts[4])
                try:
                    message = await client.get_messages(chat_username, message_id)
                    if message and message.photo:
                        return await client.download_media(message.photo.file_id)
                    return None
                except Exception as e:
                    logger.error(f"Failed to get message from Telegram: {e}")
                    return None
            return None
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    temp_file = f"default_avatar_{os.urandom(4).hex()}.jpg"
                    content = await response.read()
                    with open(temp_file, 'wb') as f:
                        f.write(content)
                    return temp_file
                return None
        except Exception as e:
            logger.error(f"Error downloading default avatar: {e}")
            return None

async def upload_to_imgbb(image_path, session):
    try:
        async with semaphore:
            with open(image_path, "rb") as file:
                image_data = base64.b64encode(await asyncio.to_thread(file.read)).decode('utf-8')
            api_key = "134919706cb1f04cb24f6069213fc1d9"  # Replace with your ImgBB API key
            upload_url = "https://api.imgbb.com/1/upload"
            payload = {"key": api_key, "image": image_data}
            async with session.post(upload_url, data=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        return result["data"]["url"]
                return None
    except Exception as e:
        logger.error(f"Failed to upload image to ImgBB: {e}")
        return None

async def convert_photo_to_sticker(photo_path):
    try:
        async with semaphore:
            with Image.open(photo_path) as img:
                img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                square_size = max(img.size)
                sticker = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
                offset = ((square_size - img.size[0]) // 2, (square_size - img.size[1]) // 2)
                sticker.paste(img, offset)
                sticker_path = f"sticker_{os.urandom(4).hex()}.webp"
                sticker.save(sticker_path, 'WEBP', quality=85)
                return sticker_path
    except Exception as e:
        logger.error(f"Failed to convert photo to sticker: {e}")
        return None

async def get_emoji_status(client, user_id):
    try:
        async with semaphore:
            try:
                input_user = await client.resolve_peer(user_id)
                full_user = await client.invoke(GetFullUser(id=input_user))
                if hasattr(full_user, 'full_user') and hasattr(full_user.full_user, 'emoji_status'):
                    emoji_status = full_user.full_user.emoji_status
                    if hasattr(emoji_status, 'document_id'):
                        return str(emoji_status.document_id)
                    custom_emoji_id = getattr(emoji_status, 'custom_emoji_id', None)
                    if custom_emoji_id:
                        return str(custom_emoji_id)
            except Exception:
                pass
            user = await client.get_users(user_id)
            if user and hasattr(user, 'emoji_status') and user.emoji_status:
                if hasattr(user.emoji_status, 'document_id'):
                    return str(user.emoji_status.document_id)
                if hasattr(user.emoji_status, 'custom_emoji_id'):
                    return str(user.emoji_status.custom_emoji_id)
            return None
    except Exception as e:
        logger.error(f"Failed to fetch emoji status for user {user_id}: {e}", exc_info=True)
        return None

async def extract_premium_emojis(message, offset_adjust=0):
    premium_emoji_entities = []
    if hasattr(message, 'entities') and message.entities:
        for entity in message.entities:
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                entity_data = {
                    "type": "custom_emoji",
                    "offset": entity.offset - offset_adjust,
                    "length": entity.length,
                    "document_id": str(entity.custom_emoji_id)
                }
                premium_emoji_entities.append(entity_data)
    if hasattr(message, 'caption_entities') and message.caption_entities:
        for entity in message.caption_entities:
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                entity_data = {
                    "type": "custom_emoji",
                    "offset": entity.offset - offset_adjust,
                    "length": entity.length,
                    "document_id": str(entity.custom_emoji_id)
                }
                premium_emoji_entities.append(entity_data)
    return premium_emoji_entities

async def extract_message_entities(message, skip_command_prefix=False, command_prefix_length=0):
    entities = []
    def process_entity(entity, is_caption=False):
        adjusted_offset = entity.offset - (command_prefix_length if skip_command_prefix else 0)
        if skip_command_prefix and entity.offset < command_prefix_length:
            return None
        entity_data = {"type": entity.type.name.lower(), "offset": adjusted_offset, "length": entity.length}
        if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
            entity_data["type"] = "custom_emoji"
            entity_data["document_id"] = str(entity.custom_emoji_id)
        for attr in ['url', 'user', 'language']:
            if hasattr(entity, attr) and getattr(entity, attr):
                attr_value = getattr(entity, attr)
                if attr == 'user' and hasattr(attr_value, 'id'):
                    entity_data[attr] = str(attr_value.id)
                else:
                    entity_data[attr] = attr_value
        return entity_data

    if hasattr(message, 'entities') and message.entities:
        for entity in message.entities:
            entity_data = process_entity(entity)
            if entity_data:
                entities.append(entity_data)
    if hasattr(message, 'caption_entities') and message.caption_entities:
        for entity in message.caption_entities:
            entity_data = process_entity(entity, is_caption=True)
            if entity_data:
                entities.append(entity_data)
    return entities

async def generate_quote(client: Client, message: Message, session):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
        command_parts = message.text.split()
        replied_message = message.reply_to_message
        text = None
        user = None
        user_id = None
        full_name = None
        avatar_file_path = None
        photo_path = None
        message_entities = []

        # Determine user and download avatar
        async with semaphore:
            # Case 1: Reply to a photo message with /q
            if replied_message and len(command_parts) == 1 and replied_message.photo:
                # If replying to own message
                if replied_message.from_user and replied_message.from_user.id == message.from_user.id:
                    user = message.from_user
                # If replying to someone else's message
                else:
                    user = replied_message.from_user
            # Case 2: Other cases (text-based or no reply)
            elif replied_message and len(command_parts) == 1:
                user = replied_message.from_user
            elif len(command_parts) > 1:
                user = message.from_user

            if user:
                full_name = user.first_name
                if user.last_name:
                    full_name += f" {user.last_name}"
                user_id = user.id
                if user.photo:
                    try:
                        avatar_file_path = await client.download_media(user.photo.big_file_id)
                    except Exception as e:
                        logger.error(f"Failed to download user photo: {e}")
                        avatar_file_path = None
            elif message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]:
                full_name = message.chat.title
                user_id = message.chat.id
                if message.chat.photo:
                    try:
                        avatar_file_path = await client.download_media(message.chat.photo.big_file_id)
                    except Exception as e:
                        logger.error(f"Failed to download chat photo: {e}")
                        avatar_file_path = None

            if avatar_file_path is None:
                avatar_file_path = await download_default_avatar(client, PROFILE_ERROR_URL, session)
                if avatar_file_path is None:
                    logger.error("Failed to download default avatar")
                    await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
                    return

            async with semaphore:
                with open(avatar_file_path, "rb") as file:
                    avatar_data = await asyncio.to_thread(file.read)
                avatar_base64 = base64.b64encode(avatar_data).decode()

            # Use user's font size preference only for group chats, default to "small" for private chats
            font_size = "small"
            if message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP] and user:
                try:
                    user_settings = await client.get_chat_member(message.chat.id, user_id)
                    font_size = getattr(user_settings, 'font_size', "small") if user_settings else "small"
                except ValueError:
                    font_size = "small"  # Fallback if get_chat_member fails

            emoji_status_id = await get_emoji_status(client, user_id)
            from_payload = {
                "id": str(user_id),
                "name": full_name,
                "photo": {"url": f"data:image/jpeg;base64,{avatar_base64}"},
                "fontSize": font_size
            }
            if emoji_status_id:
                from_payload["emoji_status"] = emoji_status_id

            # Handle photo-based sticker with caption
            if replied_message and len(command_parts) == 1 and replied_message.photo:
                try:
                    async with semaphore:
                        photo_path = await client.download_media(replied_message.photo.file_id)
                        if not photo_path:
                            logger.error("Failed to download replied photo")
                            await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
                            return

                    hosted_url = await upload_to_imgbb(photo_path, session)
                    if not hosted_url:
                        async with semaphore:
                            with open(photo_path, "rb") as file:
                                photo_data = await asyncio.to_thread(file.read)
                            photo_base64 = base64.b64encode(photo_data).decode()
                            hosted_url = f"data:image/jpeg;base64,{photo_base64}"

                    # Include caption in text if available
                    text = replied_message.caption if replied_message.caption else ""

                    json_data = {
                        "type": "quote",
                        "format": "webp",
                        "backgroundColor": "#000000",
                        "width": 512,
                        "height": 768,
                        "scale": 2,
                        "messages": [
                            {
                                "entities": [],
                                "avatar": True,
                                "from": from_payload,
                                "media": {"type": "photo", "url": hosted_url},
                                "text": text,
                                "textFontSize": font_size
                            }
                        ]
                    }
                    async with semaphore:
                        async with session.post('https://bot.lyo.su/quote/generate', json=json_data) as response:
                            if response.status != 200:
                                logger.error(f"Quotly API error: {response.status} - {await response.text()}")
                                raise Exception(f"API returned status code {response.status}")
                            response_json = await response.json()
                            if 'result' not in response_json or 'image' not in response_json['result']:
                                logger.error(f"Invalid response from API: {response_json}")
                                raise Exception("Invalid response from API")

                    async with semaphore:
                        buffer = base64.b64decode(response_json['result']['image'].encode('utf-8'))
                        file_path = 'Quotly.webp'
                        with open(file_path, 'wb') as f:
                            f.write(buffer)
                        # Ensure sticker attributes are properly set
                        try:
                            await client.send_sticker(
                                message.chat.id,
                                file_path,
                                emoji="😀"  # Default emoji if none is provided
                            )
                            logger.info("Sticker sent successfully")
                        except Exception as e:
                            logger.error(f"Failed to send sticker: {e}", exc_info=True)
                            raise
                except Exception as e:
                    logger.error(f"Error creating sticker from photo: {e}", exc_info=True)
                    await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
                finally:
                    async with semaphore:
                        if avatar_file_path and os.path.exists(avatar_file_path):
                            os.remove(avatar_file_path)
                        if photo_path and os.path.exists(photo_path):
                            os.remove(photo_path)
                        if os.path.exists('Quotly.webp'):
                            os.remove('Quotly.webp')
                return

            # Handle text-based sticker
            if replied_message and len(command_parts) == 1:
                if replied_message.text or replied_message.caption:
                    text = replied_message.text or replied_message.caption
                    message_entities = await extract_message_entities(replied_message)
                    premium_emojis = await extract_premium_emojis(replied_message)
                    if premium_emojis:
                        existing_offsets = [e['offset'] for e in message_entities if e.get("type") == "custom_emoji"]
                        for emoji in premium_emojis:
                            if emoji['offset'] not in existing_offsets:
                                message_entities.append(emoji)
                else:
                    await client.send_message(message.chat.id, "**Please send text, a sticker, or a photo to create your sticker.**", parse_mode=ParseMode.MARKDOWN)
                    return
            elif len(command_parts) > 1:
                text = " ".join(command_parts[1:])
                message_entities = await extract_message_entities(message, skip_command_prefix=True, command_prefix_length=len(command_parts[0]) + 1)
                premium_emojis = await extract_premium_emojis(message, offset_adjust=len(command_parts[0]) + 1)
                if premium_emojis:
                    existing_offsets = [e['offset'] for e in message_entities if e.get("type") == "custom_emoji"]
                    for emoji in premium_emojis:
                        if emoji['offset'] not in existing_offsets:
                            message_entities.append(emoji)
            else:
                await client.send_message(message.chat.id, "**Please send text, a sticker, or a photo to create your sticker.**", parse_mode=ParseMode.MARKDOWN)
                return

            if message_entities:
                for i, entity in enumerate(message_entities, 1):
                    if entity.get("type") == "custom_emoji" and "document_id" not in entity:
                        logger.error(f"Premium emoji {i} is missing document_id!")

            json_data = {
                "type": "quote",
                "format": "webp",
                "backgroundColor": "#000000",
                "width": 512,
                "height": 768,
                "scale": 2,
                "messages": [
                    {
                        "entities": message_entities,
                        "avatar": True,
                        "from": from_payload,
                        "text": text or "",
                        "textFontSize": font_size,
                        "replyMessage": {}
                    }
                ]
            }
            async with semaphore:
                async with session.post('https://bot.lyo.su/quote/generate', json=json_data) as response:
                    if response.status != 200:
                        logger.error(f"Quotly API error: {response.status} - {await response.text()}")
                        raise Exception(f"API returned status code {response.status}")
                    response_json = await response.json()
                    if 'result' not in response_json or 'image' not in response_json['result']:
                        logger.error(f"Invalid response from API: {response_json}")
                        raise Exception("Invalid response from API")

            async with semaphore:
                buffer = base64.b64decode(response_json['result']['image'].encode('utf-8'))
                file_path = 'Quotly.webp'
                with open(file_path, 'wb') as f:
                    f.write(buffer)
                # Ensure sticker attributes are properly set
                try:
                    await client.send_sticker(
                        message.chat.id,
                        file_path,
                        emoji="😀"  # Default emoji if none is provided
                    )
                    logger.info("Sticker sent successfully")
                except Exception as e:
                    logger.error(f"Failed to send sticker: {e}", exc_info=True)
                    raise
    except Exception as e:
        logger.error(f"Error generating quote: {e}", exc_info=True)
        await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
    finally:
        async with semaphore:
            if avatar_file_path and os.path.exists(avatar_file_path):
                os.remove(avatar_file_path)
            if photo_path and os.path.exists(photo_path):
                os.remove(photo_path)
            if os.path.exists('Quotly.webp'):
                os.remove('Quotly.webp')

def setup_q_handler(app: Client):
    """Set up the quote command handler with an asynchronous session."""
    @app.on_message(filters.command(["q", "qoute", "csticker"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def q_command(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**")
            return

        async with aiohttp.ClientSession() as session:
            try:
                await generate_quote(client, message, session)
            except Exception as e:
                logger.error(f"Unhandled exception in q_command: {e}", exc_info=True)
                await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)