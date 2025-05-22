#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import time
import threading
import requests
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX, IMGAI_SIZE_LIMIT
from utils import notify_admin  # Import notify_admin

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ImageEnhancer:
    def __init__(self):
        self.status_check_interval = 1  # Faster polling (1 second)
        self.max_status_checks = 30
        self.timeout = 45

    def check_status(self, code, result_container):
        status_url = "https://photoai.imglarger.com/api/PhoAi/CheckStatus"
        status_headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "referer": "https://image-enhancer-snowy.vercel.app/"
        }
        
        for attempt in range(self.max_status_checks):
            try:
                status_payload = {"type": "2", "code": code}
                status_response = requests.post(status_url, headers=status_headers, json=status_payload, timeout=5)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if status_data.get('data', {}).get('downloadUrls', []):
                    download_url = status_data['data']['downloadUrls'][0]
                    if download_url.startswith(f"https://photoai.imglarger.com/color-enhancer/{code}.jpg"):
                        result_container["url"] = download_url
                        return
                
                time.sleep(self.status_check_interval)
                
            except Exception as e:
                logger.error(f"Status check attempt {attempt + 1} failed: {str(e)}")
                result_container["error"] = f"Status check error: {str(e)}"
                return

        result_container["error"] = "Image processing timed out."

    def enhance_image(self, image_path: str) -> str:
        try:
            if not image_path or not os.path.exists(image_path):
                return "Error: Invalid image path"

            file_size = os.path.getsize(image_path)
            if file_size > IMGAI_SIZE_LIMIT:
                return "Error: Image size exceeds limit."

            # Upload to Imglarger
            upload_url = "https://photoai.imglarger.com/api/PhoAi/Upload"
            boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
            
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": f"multipart/form-data; boundary={boundary}",
                "referer": "https://image-enhancer-snowy.vercel.app/"
            }
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            payload = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="type"\r\n\r\n'
                f"2\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="scaleRadio"\r\n\r\n'
                f"1\r\n"
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="image.jpg"\r\n'
                f"Content-Type: image/jpeg\r\n\r\n"
            ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

            response = requests.post(upload_url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            upload_data = response.json()
            
            if not upload_data.get('data', {}).get('code'):
                return "Error: No code received in upload response."
            
            code = upload_data['data']['code']
            
            # Use threading for status checks
            result_container = {}
            status_thread = threading.Thread(target=self.check_status, args=(code, result_container))
            status_thread.start()
            status_thread.join(timeout=self.timeout)
            
            if "url" in result_container:
                return result_container["url"]
            elif "error" in result_container:
                return result_container["error"]
            else:
                return "Error: Image processing timed out."
            
        except requests.exceptions.RequestException as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            logger.error(f"Enhancement failed: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"

enhancer = ImageEnhancer()

def setup_remini_handler(app: Client):
    @app.on_message(filters.command(["enh"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def enhance_command_handler(client: Client, message: Message):
        if not message.reply_to_message:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Reply to a photo to enhance face**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not message.reply_to_message.photo:
            await client.send_message(
                chat_id=message.chat.id,
                text="**Reply to a photo to enhance face**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if message.reply_to_message.photo.file_size > IMGAI_SIZE_LIMIT:
            await client.send_message(
                chat_id=message.chat.id,
                text="**File Is Too Large To Enhance**",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        processing_msg = await client.send_message(
            chat_id=message.chat.id,
            text="**✨Enhancing Your Photo...**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        file_path = None
        try:
            # Create temp directory if not exists
            os.makedirs("temp", exist_ok=True)
            
            # Download with explicit file path
            file_path = await client.download_media(
                message.reply_to_message,
                file_name=f"temp/temp_{message.id}.jpg"
            )
            
            if not file_path or not os.path.exists(file_path):
                raise ValueError("Failed to download image")

            enhanced_url = enhancer.enhance_image(file_path)
            
            if enhanced_url.startswith("http"):
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=enhanced_url,
                    caption="✅ **Here Is You Enhnaced Photo!**",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"**Sorry Smart Enhnacer Dead**",
                    parse_mode=ParseMode.MARKDOWN
                )
                # Notify admins if enhancement fails
                await notify_admin(client, "/enh", Exception(enhanced_url), message)
                
        except Exception as e:
            error_msg = f"**Sorry Smart Enhnacer Dead**"
            await client.send_message(
                chat_id=message.chat.id,
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.error(f"Handler error: {str(e)}", exc_info=True)
            # Notify admins of handler error
            await notify_admin(client, "/enh", e, message)
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temp file: {str(e)}")
            
            try:
                await processing_msg.delete()
            except Exception as e:
                logger.warning(f"Could not delete processing message: {str(e)}")
