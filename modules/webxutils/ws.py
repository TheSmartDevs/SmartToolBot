#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import re
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import zipfile
import shutil
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType
from config import COMMAND_PREFIX

# Directory to save the downloaded files temporarily
DOWNLOAD_DIRECTORY = "./downloads/"

# Maximum size limit for the entire download (5MB = 5 * 1024 * 1024 bytes)
MAX_TOTAL_SIZE = 5 * 1024 * 1024

# Maximum number of files per resource type
MAX_CSS_FILES = 10
MAX_JS_FILES = 10

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

class URLDownloader:
    """Download the webpage components based on the input URL with size limitations."""
    
    def __init__(self, img_flg=False, link_flg=True, script_flg=True):
        self.soup = None
        self.img_flg = img_flg
        self.link_flg = link_flg
        self.script_flg = script_flg
        self.link_type = ('css', 'js')
        self.total_size = 0
        self.download_count = {'css': 0, 'js': 0}
        self.size_limit_reached = False
        
    async def fetch(self, session, url, max_size=1024 * 1024):
        """Fetch URL content with size limit per request"""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None
                
                # Get content length if available
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > max_size:
                    print(f"Skipping {url}: File too large ({content_length} bytes)")
                    return None
                
                # Start reading with size limit
                content = b""
                chunk_size = 8192
                size = 0
                
                async for chunk in response.content.iter_chunked(chunk_size):
                    size += len(chunk)
                    if size > max_size:
                        print(f"Skipping {url}: Download exceeded size limit")
                        return None
                    content += chunk
                
                return content
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Error fetching {url}: {str(e)}")
            return None
        
    async def save_page(self, url, page_folder='page'):
        """Save the web page components based on the input URL and directory name."""
        try:
            # Ensure the URL has a scheme
            if not urlparse(url).scheme:
                url = "https://" + url

            async with aiohttp.ClientSession() as session:
                # Fetch the main HTML page first
                response = await self.fetch(session, url)
                if not response:
                    return None
                
                self.total_size += len(response)
                if self.total_size > MAX_TOTAL_SIZE:
                    print(f"Main HTML page exceeds size limit: {self.total_size} bytes")
                    return None
                
                self.soup = BeautifulSoup(response, "html.parser")
                if not os.path.exists(page_folder):
                    os.mkdir(page_folder)
                
                tasks = []
                if self.link_flg:
                    tasks.append(self._soup_find_and_save(session, url, page_folder, 'link', 'href'))
                if self.script_flg:
                    tasks.append(self._soup_find_and_save(session, url, page_folder, 'script', 'src'))
                
                await asyncio.gather(*tasks)
                
                # Don't save the HTML if size limit was reached during resource downloads
                if self.size_limit_reached:
                    return None
                
                with open(os.path.join(page_folder, 'page.html'), 'wb') as file:
                    file.write(self.soup.prettify('utf-8'))
                
                zip_path = self._zip_folder(page_folder, url)
                return zip_path
        except Exception as e:
            print(f"> save_page(): Create files failed: {str(e)}")
            return None

    async def _soup_find_and_save(self, session, url, page_folder, tag_to_find='link', inner='href'):
        """Save specified tag_to_find objects in the page_folder with limits."""
        page_folder = os.path.join(page_folder, tag_to_find)
        if not os.path.exists(page_folder):
            os.mkdir(page_folder)
        
        tasks = []
        resource_type_count = {'css': 0, 'js': 0}
        
        for res in self.soup.findAll(tag_to_find):
            if res.has_attr(inner):
                # Skip if we already reached the download limit
                if self.size_limit_reached:
                    continue
                    
                # Process resource URL
                resource_url = res.get(inner)
                resource_type = self._get_resource_type(resource_url)
                
                # Skip non-CSS/JS resources for link tags
                if tag_to_find == 'link' and resource_type != 'css':
                    continue
                
                # Check if we've hit the per-type file limits
                if resource_type == 'css' and self.download_count['css'] >= MAX_CSS_FILES:
                    continue
                if resource_type == 'js' and self.download_count['js'] >= MAX_JS_FILES:
                    continue
                
                # Add this download task
                tasks.append(self._download_resource(session, url, res, page_folder, inner, resource_type))
                
        if tasks:
            await asyncio.gather(*tasks)
    
    def _get_resource_type(self, url):
        """Determine resource type from URL"""
        if url:
            lower_url = url.lower()
            if lower_url.endswith('.css') or '?css' in lower_url or '/css/' in lower_url:
                return 'css'
            elif lower_url.endswith('.js') or '?js' in lower_url or '/js/' in lower_url:
                return 'js'
        return 'other'
    
    async def _download_resource(self, session, url, res, page_folder, inner, resource_type):
        """Download and save a resource with size limits."""
        try:
            # Skip if we already reached the size limit
            if self.size_limit_reached:
                return

            # Get the file URL and create a safe filename
            file_url = urljoin(url, res.get(inner))
            filename = re.sub(r'\W+', '.', os.path.basename(res[inner]))
            
            # Add extension if missing
            if not filename.endswith(f'.{resource_type}') and resource_type in ('css', 'js'):
                filename += f'.{resource_type}'
                
            file_path = os.path.join(page_folder, filename)
            
            # Update reference in the HTML
            res[inner] = os.path.join(os.path.basename(page_folder), filename)
            
            # Skip already downloaded files
            if os.path.isfile(file_path):
                return
                
            # Fetch the resource content
            content = await self.fetch(session, file_url)
            if not content:
                return
                
            # Check if this would exceed our total size limit
            if self.total_size + len(content) > MAX_TOTAL_SIZE:
                print(f"Size limit reached: {self.total_size} + {len(content)} > {MAX_TOTAL_SIZE}")
                self.size_limit_reached = True
                return
                
            # Update counters
            self.total_size += len(content)
            if resource_type in self.download_count:
                self.download_count[resource_type] += 1
                
            # Save the file
            with open(file_path, 'wb') as file:
                file.write(content)
                
        except Exception as exc:
            print(f"Error downloading resource {res.get(inner)}: {exc}")

    def _zip_folder(self, folder_path, url):
        """Zip the folder."""
        sanitized_url = re.sub(r'\W+', '_', url)
        zip_name = f"Smart_Tool_{sanitized_url}.zip"
        zip_path = os.path.join("downloads", zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=folder_path)
                    zipf.write(file_path, arcname)
        return zip_path

    def _remove_folder(self, folder_path):
        """Remove a folder and its contents."""
        shutil.rmtree(folder_path)

# ThreadPoolExecutor instance
executor = ThreadPoolExecutor(max_workers=5)

async def download_web_source(client: Client, message: Message):
    # Get the command and its arguments
    command_parts = message.text.split()

    # Check if the user provided a URL
    if len(command_parts) <= 1:
        await client.send_message(message.chat.id, "**❌ Provide at least one URL.**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return

    url = command_parts[1]

    # Notify the user that the source code is being downloaded
    downloading_msg = await client.send_message(message.chat.id, "**Downloading Source Code...**", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    try:
        # Create a unique folder for this download
        timestamp = int(time.time())
        page_folder = os.path.join("downloads", f"{urlparse(url).netloc}_{timestamp}")
        
        # Download the webpage components
        downloader = URLDownloader()
        
        # Run the save_page method
        loop = asyncio.get_event_loop()
        zip_path = await loop.run_in_executor(executor, lambda: asyncio.run(downloader.save_page(url, page_folder)))

        if zip_path:
            # Check final ZIP size
            zip_size = os.path.getsize(zip_path)
            if zip_size > MAX_TOTAL_SIZE:
                await client.send_message(
                    message.chat.id, 
                    f"**Failed To Download Database Too Big**", 
                    parse_mode=ParseMode.MARKDOWN
                )
                os.remove(zip_path)
            else:
                # Send the zip file to the user
                if message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP] and not message.from_user:
                    # In a group chat where user info is not available, link the group name with its URL
                    group_name = message.chat.title
                    group_url = f"https://t.me/{message.chat.username}" if message.chat.username else "Group"
                    caption = (
                        f"**Source code Download**\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"**Site:** {url}\n"
                        f"**Type:** HTML, CSS, JS\n"
                        f"**Size:** {zip_size/(1024*1024):.2f}MB\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"**Source Downloaded By:** [{group_name}]({group_url})"
                    )
                else:
                    # In private chat or where user info is available
                    user_full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
                    user_profile_link = f"https://t.me/{message.from_user.username}"
                    caption = (
                        f"**Source code Download**\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"**Site:** {url}\n"
                        f"**Type:** HTML, CSS, JS\n"
                        f"**Size:** {zip_size/(1024*1024):.2f}MB\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"**Source Downloaded By:** [{user_full_name}]({user_profile_link})"
                    )
                
                await client.send_document(
                    chat_id=message.chat.id,
                    document=zip_path,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN
                )
                os.remove(zip_path)
        else:
            await client.send_message(
                message.chat.id, 
                "**Failed To Download Database Too Big**", 
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        await client.send_message(
            message.chat.id, 
            f"**Sorry Bro Web Source DL API Dead**", 
            parse_mode=ParseMode.MARKDOWN
        )

    finally:
        # Delete the downloading message
        await downloading_msg.delete()
        
        # Clean up the page folder if it exists
        if 'page_folder' in locals() and os.path.exists(page_folder):
            shutil.rmtree(page_folder)

def setup_ws_handler(app: Client):
    @app.on_message(filters.command(["ws","websource"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def ws_command(client: Client, message: Message):
        # Run the download_web_source in the background to handle multiple requests simultaneously
        asyncio.create_task(download_web_source(client, message))