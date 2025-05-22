#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import requests
import base64
import os
import asyncio
import logging
import json
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType, ChatAction
from pyrogram.raw.functions.users import GetFullUser
from PIL import Image
from datetime import datetime
from config import COMMAND_PREFIX, PROFILE_ERROR_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ThreadPoolExecutor instance
executor = ThreadPoolExecutor(max_workers=5)  # Adjust At Your Own Needs

async def download_default_avatar(client, url):
    """Download default avatar from Telegram URL"""
    logger.info(f"Attempting to download default avatar from: {url}")
    
    # Check if it's a Telegram URL (t.me format)
    if "t.me/" in url:
        # Extract the chat and message ID
        parts = url.split("/")
        logger.info(f"URL parts: {parts}")
        
        if len(parts) >= 5:
            chat_username = parts[3]
            message_id = int(parts[4])
            logger.info(f"Parsed Telegram URL: chat={chat_username}, message_id={message_id}")
            
            try:
                # Get the message from Telegram
                logger.info(f"Fetching message from Telegram...")
                message = await client.get_messages(chat_username, message_id)
                
                if message and message.photo:
                    # Download the photo directly with a temporary name
                    logger.info(f"Photo found in message, downloading...")
                    temp_file = await client.download_media(message.photo.file_id)
                    logger.info(f"Downloaded to: {temp_file}")
                    return temp_file
                else:
                    logger.error(f"No photo found in message: {url}")
                    return None
            except Exception as e:
                logger.error(f"Failed to get message from Telegram: {e}")
                return None
        else:
            logger.error(f"Invalid Telegram URL format: {url}")
            return None
    else:
        # Regular URL, use requests
        try:
            logger.info(f"Downloading from regular URL...")
            response = requests.get(url)
            if response.status_code == 200:
                temp_file = f"default_avatar_{os.urandom(4).hex()}.jpg"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Downloaded to: {temp_file}")
                return temp_file
            else:
                logger.error(f"Failed to download from URL, status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading default avatar: {e}")
            return None

async def convert_photo_to_sticker(photo_path):
    """Convert a photo to WebP sticker format with optimized memory usage"""
    try:
        logger.info(f"Converting photo to sticker: {photo_path}")
        # Open the image
        img = Image.open(photo_path)
        
        # Resize to Telegram sticker size (512x512 max dimension) with lower quality
        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
        
        # Create new square image with transparent background
        square_size = max(img.size)
        sticker = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
        offset = ((square_size - img.size[0]) // 2, (square_size - img.size[1]) // 2)
        sticker.paste(img, offset)
        
        # Save as WebP with reduced quality to save memory
        sticker_path = f"sticker_{os.urandom(4).hex()}.webp"
        sticker.save(sticker_path, 'WEBP', quality=85)  # Reduced quality
        logger.info(f"Sticker created: {sticker_path}")
        return sticker_path
    except Exception as e:
        logger.error(f"Failed to convert photo to sticker: {e}")
        return None
    finally:
        # Close the image to free memory
        if 'img' in locals():
            img.close()
        if 'sticker' in locals():
            sticker.close()

async def get_emoji_status(client, user_id):
    """Fetch the emoji status ID using Pyrogram's raw API method which is more reliable"""
    try:
        logger.info(f"Fetching emoji status for user {user_id} via raw API")
        
        # Use the raw API to get user's full info including premium emoji status
        try:
            # First get the InputUser object
            input_user = await client.resolve_peer(user_id)
            # Use GetFullUser raw function to get complete user data
            full_user = await client.invoke(GetFullUser(id=input_user))
            
            # Check for emoji status in the full user data
            if hasattr(full_user, 'full_user') and hasattr(full_user.full_user, 'emoji_status'):
                emoji_status = full_user.full_user.emoji_status
                logger.info(f"Raw emoji_status object found: {emoji_status}")
                
                # Debug all attributes of the emoji_status object
                if hasattr(emoji_status, '__dict__'):
                    logger.info(f"Emoji status attributes: {emoji_status.__dict__}")
                
                # Extract the custom emoji ID - try document_id first
                if hasattr(emoji_status, 'document_id'):
                    emoji_id = emoji_status.document_id
                    logger.info(f"Found emoji document_id: {emoji_id}")
                    return str(emoji_id)  # Convert to string for API payload
                
                # Alternative property names to check
                custom_emoji_id = getattr(emoji_status, 'custom_emoji_id', None)
                if custom_emoji_id:
                    logger.info(f"Found custom_emoji_id: {custom_emoji_id}")
                    return str(custom_emoji_id)  # Ensure string format
                
                # Try to get ID by checking all attributes
                for attr_name in dir(emoji_status):
                    if 'id' in attr_name.lower() and not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(emoji_status, attr_name)
                            if isinstance(attr_value, (int, str)) and attr_value:
                                logger.info(f"Found emoji ID in attribute {attr_name}: {attr_value}")
                                return str(attr_value)  # Ensure string format
                        except:
                            pass
        except Exception as raw_error:
            logger.warning(f"Raw API method failed: {raw_error}. Trying alternative method.")
        
        # Fallback to standard method
        user = await client.get_users(user_id)
        if user and hasattr(user, 'emoji_status') and user.emoji_status:
            logger.info(f"Standard API emoji_status found: {user.emoji_status}")
            
            # Try different property names that might contain the emoji ID
            possible_id_attrs = ['document_id', 'custom_emoji_id', 'id']
            
            for attr in possible_id_attrs:
                if hasattr(user.emoji_status, attr):
                    emoji_id = getattr(user.emoji_status, attr)
                    if emoji_id:
                        logger.info(f"Found emoji ID via attribute '{attr}': {emoji_id}")
                        return str(emoji_id)  # Ensure string format
            
            # If we have emoji_status object but couldn't extract ID, debug its attributes
            logger.info(f"Emoji status available but ID not found. Available attributes: {dir(user.emoji_status)}")
            
            # Try to extract any ID by converting to dict if possible
            try:
                if hasattr(user.emoji_status, 'to_dict'):
                    emoji_dict = user.emoji_status.to_dict()
                    logger.info(f"Emoji status as dict: {emoji_dict}")
                    if 'document_id' in emoji_dict:
                        return str(emoji_dict['document_id'])  # Ensure string format
                    # Try to find any key that might be the ID
                    for key, value in emoji_dict.items():
                        if 'id' in key.lower() and isinstance(value, (int, str)):
                            logger.info(f"Using '{key}' as emoji ID: {value}")
                            return str(value)  # Ensure string format
                
                # Last resort: try to get any attribute with "id" in the name
                for attr_name in dir(user.emoji_status):
                    if 'id' in attr_name.lower() and not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(user.emoji_status, attr_name)
                            if isinstance(attr_value, (int, str)) and attr_value:
                                logger.info(f"Found emoji ID in attribute {attr_name}: {attr_value}")
                                return str(attr_value)  # Ensure string format
                        except:
                            pass
            except Exception as dict_err:
                logger.warning(f"Failed to process emoji_status: {dict_err}")
        
        logger.info(f"No emoji status found for user {user_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch emoji status for user {user_id}: {e}", exc_info=True)
        return None

async def extract_premium_emojis(message, offset_adjust=0):
    """Enhanced function to specifically extract premium emoji entities from a message"""
    premium_emoji_entities = []
    
    # Process message entities (for text messages)
    if hasattr(message, 'entities') and message.entities:
        for entity in message.entities:
            # Check if the entity is a custom emoji
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                # Create entity data with proper premium emoji handling
                entity_data = {
                    "type": "custom_emoji",
                    "offset": entity.offset - offset_adjust,  # Adjust offset if needed
                    "length": entity.length,
                    "document_id": str(entity.custom_emoji_id)  # Critical: ensure string format and use custom_emoji_id
                }
                
                # Debug the entity
                logger.info(f"Found premium emoji in text: ID={entity.custom_emoji_id}, offset={entity_data['offset']}, length={entity_data['length']}")
                
                # Try to extract additional emoji data if available (some Pyrogram versions use document_id)
                if hasattr(entity, 'document_id'):
                    entity_data["document_id"] = str(entity.document_id)
                    logger.info(f"Using document_id for premium emoji: {entity.document_id}")
                    
                premium_emoji_entities.append(entity_data)
    
    # Process caption entities (for media messages)
    if hasattr(message, 'caption_entities') and message.caption_entities:
        for entity in message.caption_entities:
            # Check if the entity is a custom emoji
            if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
                # Create entity data with proper premium emoji handling
                entity_data = {
                    "type": "custom_emoji",
                    "offset": entity.offset - offset_adjust,  # Adjust offset if needed
                    "length": entity.length,
                    "document_id": str(entity.custom_emoji_id)  # Critical: ensure string format and use custom_emoji_id
                }
                
                # Debug the entity
                logger.info(f"Found premium emoji in caption: ID={entity.custom_emoji_id}, offset={entity_data['offset']}, length={entity_data['length']}")
                
                # Try to extract additional emoji data if available
                if hasattr(entity, 'document_id'):
                    entity_data["document_id"] = str(entity.document_id)
                    logger.info(f"Using document_id for premium emoji: {entity.document_id}")
                    
                premium_emoji_entities.append(entity_data)
    
    # Log results
    if premium_emoji_entities:
        logger.info(f"Extracted {len(premium_emoji_entities)} premium emoji entities")
        for i, emoji in enumerate(premium_emoji_entities):
            logger.info(f"Premium emoji {i+1}: document_id={emoji.get('document_id')}, offset={emoji.get('offset')}, length={emoji.get('length')}")
    else:
        logger.info("No premium emoji entities found")
        
    return premium_emoji_entities

async def extract_message_entities(message, skip_command_prefix=False, command_prefix_length=0):
    """Extract all message entities with improved premium emoji handling"""
    entities = []
    
    # Function to properly process each entity
    def process_entity(entity, is_caption=False, offset_adjust=0):
        source_type = "caption" if is_caption else "text"
        
        # Calculate adjusted offset (for command messages)
        adjusted_offset = entity.offset - offset_adjust if offset_adjust > 0 else entity.offset
        
        # Skip entities that are part of the command prefix if requested
        if skip_command_prefix and entity.offset < command_prefix_length:
            logger.info(f"Skipping entity at offset {entity.offset} (part of command prefix)")
            return None
            
        # Create base entity data
        entity_data = {
            "type": entity.type.name.lower(),
            "offset": adjusted_offset,
            "length": entity.length
        }
        
        # Specifically handle custom emoji entities (premium emojis)
        if hasattr(entity, 'custom_emoji_id') and entity.custom_emoji_id:
            # For premium emojis, we need special handling
            entity_data["type"] = "custom_emoji"
            entity_data["document_id"] = str(entity.custom_emoji_id)
            logger.info(f"Found premium emoji in {source_type}: custom_emoji_id={entity.custom_emoji_id}, offset={adjusted_offset}, length={entity.length}")
            
            # Try to extract additional emoji data if available
            if hasattr(entity, 'document_id') and entity.document_id:
                entity_data["document_id"] = str(entity.document_id)
                logger.info(f"Using document_id for premium emoji: {entity.document_id}")
        
        # Handle other entity attributes
        for attr in ['url', 'user', 'language']:
            if hasattr(entity, attr) and getattr(entity, attr):
                attr_value = getattr(entity, attr)
                # Convert numeric IDs to strings if needed
                if attr == 'user' and hasattr(attr_value, 'id'):
                    entity_data[attr] = str(attr_value.id)
                else:
                    entity_data[attr] = attr_value
        
        return entity_data
    
    # Process text entities (standard messages)
    if hasattr(message, 'entities') and message.entities:
        for entity in message.entities:
            # Process all entities
            entity_data = process_entity(entity, 
                                         offset_adjust=command_prefix_length if skip_command_prefix else 0)
            if entity_data:  # Skip None results (filtered out command prefix)
                entities.append(entity_data)
    
    # Process caption entities (media messages)
    if hasattr(message, 'caption_entities') and message.caption_entities:
        for entity in message.caption_entities:
            entity_data = process_entity(entity, 
                                         is_caption=True,
                                         offset_adjust=command_prefix_length if skip_command_prefix else 0)
            if entity_data:  # Skip None results (filtered out command prefix)
                entities.append(entity_data)
    
    # Additional logging for premium emojis specifically
    premium_emojis = [e for e in entities if e.get("type") == "custom_emoji"]
    if premium_emojis:
        logger.info(f"Extracted {len(premium_emojis)} premium emoji entities")
        for i, emoji in enumerate(premium_emojis):
            logger.info(f"Premium emoji {i+1}: document_id={emoji.get('document_id')}, offset={emoji.get('offset')}, length={emoji.get('length')}")
    
    # Log all entities for debugging
    if entities:
        logger.info(f"Extracted {len(entities)} total entities")
        for i, entity in enumerate(entities):
            logger.info(f"Entity {i+1}: {entity}")
    else:
        logger.info("No message entities found")
        
    return entities

async def generate_quote(client: Client, message: Message):
    """Generate a quote sticker with error handling"""
    try:
        # Trigger 'choosing a sticker' animation
        await client.send_chat_action(message.chat.id, ChatAction.CHOOSE_STICKER)
        
        command_parts = message.text.split()
        
        # Determine source of text and user
        replied_message = message.reply_to_message
        
        # Initialize variables
        text = None
        user = None
        user_id = None
        full_name = None
        avatar_file_path = None
        message_entities = []
        
        # NEW CASE: Reply to a photo with just the command (/q) - Convert photo to sticker
        if replied_message and len(command_parts) == 1 and replied_message.photo:
            try:
                logger.info("Processing photo to sticker conversion")
                # Ensure chat action is visible with a small delay
                await asyncio.sleep(1)  # Brief delay to allow chat action to display
                # Download the photo
                photo_path = await client.download_media(replied_message.photo.file_id)
                if not photo_path:
                    logger.error("Failed to download photo")
                    await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
                    return
                
                # Convert photo to sticker
                sticker_path = await convert_photo_to_sticker(photo_path)
                if not sticker_path:
                    logger.error("Failed to convert photo to sticker")
                    await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
                    return
                
                # Send the sticker with explicit alt attribute
                await client.send_sticker(message.chat.id, sticker_path, emoji="")
                logger.info("Photo sticker sent successfully")
                
            except Exception as e:
                logger.error(f"Error converting photo to sticker: {e}")
                await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
            
            finally:
                # Clean up temporary files
                if 'photo_path' in locals() and photo_path and os.path.exists(photo_path):
                    os.remove(photo_path)
                    logger.info(f"Removed photo file: {photo_path}")
                if 'sticker_path' in locals() and sticker_path and os.path.exists(sticker_path):
                    os.remove(sticker_path)
                    logger.info(f"Removed sticker file: {sticker_path}")
            return
        
        # CASE 1: Reply to message with just the command (/q) - Use replied user's profile and text
        if replied_message and len(command_parts) == 1:
            if replied_message.text or replied_message.caption:
                # Use text or caption (for media messages)
                text = replied_message.text or replied_message.caption
                
                # Extract ALL entities from the replied message
                message_entities = await extract_message_entities(replied_message)
                
                # Double-check premium emojis specifically (critical part)
                premium_emojis = await extract_premium_emojis(replied_message)
                
                # If we found premium emojis but they weren't in the regular entities, add them
                if premium_emojis:
                    # First check if we need to add any new emojis
                    existing_premium_emoji_offsets = []
                    for entity in message_entities:
                        if entity.get("type") == "custom_emoji":
                            existing_premium_emoji_offsets.append(entity.get("offset"))
                    
                    # Add any premium emojis not already captured
                    for emoji in premium_emojis:
                        if emoji.get("offset") not in existing_premium_emoji_offsets:
                            logger.info(f"Adding missing premium emoji: {emoji}")
                            message_entities.append(emoji)
                
                # Important: Use the replied user's profile info
                user = replied_message.from_user
            else:
                await client.send_message(message.chat.id, "**Please send text, a sticker, or a photo to create your sticker.**", parse_mode=ParseMode.MARKDOWN)
                return
        
        # CASE 2: Command with text (/q some text) - Use command user's details
        elif len(command_parts) > 1:
            text = " ".join(command_parts[1:])
            user = message.from_user
            
            # Calculate command prefix length
            command_prefix_length = len(command_parts[0]) + 1  # +1 for the space after command
            
            # Extract ALL entities from the command message with command offset adjustment
            message_entities = await extract_message_entities(
                message, 
                skip_command_prefix=True,
                command_prefix_length=command_prefix_length
            )
            
            # Double-check premium emojis specifically using the dedicated function
            premium_emojis = await extract_premium_emojis(message, offset_adjust=command_prefix_length)
            
            # If we found premium emojis but they weren't in the regular entities, add them
            if premium_emojis:
                # First check if we need to add any new emojis
                existing_premium_emoji_offsets = []
                for entity in message_entities:
                    if entity.get("type") == "custom_emoji":
                        existing_premium_emoji_offsets.append(entity.get("offset"))
                
                # Add any premium emojis not already captured
                for emoji in premium_emojis:
                    if emoji.get("offset") not in existing_premium_emoji_offsets:
                        logger.info(f"Adding missing premium emoji: {emoji}")
                        message_entities.append(emoji)
        
        # CASE 3: Command with no text and no reply
        else:
            await client.send_message(message.chat.id, "**Please send text, a sticker, or a photo to create your sticker.**", parse_mode=ParseMode.MARKDOWN)
            return
        
        # Get user details
        if user:
            # Preserve user's original name format exactly as shown in Telegram
            full_name = user.first_name
            if user.last_name:
                full_name += f" {user.last_name}"
            user_id = user.id
            
            # Try to get user photo, if available
            if user.photo:
                try:
                    logger.info(f"Downloading user photo for user_id: {user_id}")
                    avatar_file_path = await client.download_media(user.photo.big_file_id)
                    logger.info(f"User photo downloaded to: {avatar_file_path}")
                except Exception as e:
                    logger.error(f"Failed to download user photo: {e}")
                    avatar_file_path = None
        else:
            # Fallback to chat: Fallback to chat details if somehow user is not available
            if message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]:
                full_name = message.chat.title
                user_id = message.chat.id
                if message.chat.photo:
                    try:
                        logger.info(f"Downloading chat photo for chat_id: {user_id}")
                        avatar_file_path = await client.download_media(message.chat.photo.big_file_id)
                        logger.info(f"Chat photo downloaded to: {avatar_file_path}")
                    except Exception as e:
                        logger.error(f"Failed to download chat photo: {e}")
                        avatar_file_path = None
        
        # If no profile photo, use default from config
        if avatar_file_path is None:
            logger.info(f"No profile photo found, using default from PROFILE_ERROR_URL: {PROFILE_ERROR_URL}")
            # Use the default profile image from config
            avatar_file_path = await download_default_avatar(client, PROFILE_ERROR_URL)
            
            if avatar_file_path is None:
                logger.error("Failed to download default avatar")
                await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
                return
        
        # Convert avatar to base64
        logger.info(f"Converting avatar to base64: {avatar_file_path}")
        with open(avatar_file_path, "rb") as file:
            avatar_data = file.read()
        avatar_base64 = base64.b64encode(avatar_data).decode()
        
        # Fetch emoji status ID using the improved method
        emoji_status_id = await get_emoji_status(client, user_id)
        
        # Prepare from_payload - preserve user's original name format
        from_payload = {
            "id": str(user_id),  # Ensure user_id is a string
            "name": full_name,
            "photo": {
                "url": f"data:image/jpeg;base64,{avatar_base64}"
            },
            "fontSize": "small"
        }
        
        # Add emoji status to payload if available
        if emoji_status_id:
            # The API expects the emoji_status field to be the emoji document ID as a string
            from_payload["emoji_status"] = emoji_status_id
            logger.info(f"Added emoji_status to payload: {emoji_status_id}")
        else:
            logger.warning(f"No emoji status ID fetched for user {user_id}")
        
        # Final validation of entities, especially premium emojis
        if message_entities:
            # Log all entities for verification
            for i, entity in enumerate(message_entities):
                logger.info(f"Final entity {i+1}: {entity}")
                
                # Ensure all custom emoji entities have document_id as string
                if entity.get("type") == "custom_emoji":
                    if "document_id" in entity:
                        # Validate document_id is a string
                        entity["document_id"] = str(entity["document_id"])
                        logger.info(f"Premium emoji {i+1} validated: document_id={entity['document_id']}")
                    else:
                        logger.warning(f"Premium emoji {i+1} is missing document_id!")
        
        # Prepare JSON data for Quotly API with entities included for premium emojis
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
                    "textFontSize": "small",
                    "replyMessage": {}
                }
            ]
        }
        
        # Log JSON payload for debugging
        logger.debug(f"Quotly API JSON payload: {json.dumps(json_data, indent=2)}")
        
        # Send API request in a non-blocking way
        logger.info("Sending request to Quotly API")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, lambda: requests.post('https://bot.lyo.su/quote/generate', json=json_data))
        
        if response.status_code != 200:
            logger.error(f"Quotly API error: {response.status_code} - {response.text}")
            raise Exception(f"API returned status code {response.status_code}")
            
        response_json = response.json()
        if 'result' not in response_json or 'image' not in response_json['result']:
            logger.error(f"Invalid response from API: {response_json}")
            raise Exception("Invalid response from API")
        
        # Process the response and generate sticker
        logger.info("Processing API response and creating sticker")
        buffer = base64.b64decode(response_json['result']['image'])
        file_path = 'Quotly.webp'
        with open(file_path, 'wb') as f:
            f.write(buffer)
        
        # Send the sticker with explicit alt attribute
        await client.send_sticker(message.chat.id, file_path, emoji="")
        logger.info("Sticker sent successfully")
    
    except Exception as e:
        # Log the error and send error message
        logger.error(f"Error generating quote: {e}", exc_info=True)
        await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)
    
    finally:
        # Clean up temporary files
        logger.info("Cleaning up temporary files")
        if 'avatar_file_path' in locals() and avatar_file_path and os.path.exists(avatar_file_path):
            os.remove(avatar_file_path)
            logger.info(f"Removed avatar file: {avatar_file_path}")
        if os.path.exists('Quotly.webp'):
            os.remove('Quotly.webp')
            logger.info("Removed sticker file")

def setup_q_handler(app: Client):
    @app.on_message(filters.command(["q", "qoute", "csticker"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def q_command(client: Client, message: Message):
        try:
            await generate_quote(client, message)
        except Exception as e:
            logger.error(f"Unhandled exception in q_command: {e}", exc_info=True)
            await client.send_message(message.chat.id, "**❌Failed To Generate Sticker**", parse_mode=ParseMode.MARKDOWN)