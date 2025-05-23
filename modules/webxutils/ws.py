#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
import os
import re
import asyncio
import zipfile
import io
import aiohttp
import aiofiles
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX

class UrlDownloader:
    """Download webpage components based on the input URL, optimized for speed."""
    def __init__(self, imgFlg=True, linkFlg=True, scriptFlg=True):
        self.soup = None
        self.imgFlg = imgFlg
        self.linkFlg = linkFlg
        self.scriptFlg = scriptFlg
        self.linkType = ('css', 'png', 'ico', 'jpg', 'jpeg', 'mov', 'ogg', 'gif', 'xml', 'js')
        self.size_limit = 10 * 1024 * 1024  # 10 MB limit
        self.semaphore = asyncio.Semaphore(50)  # Limit concurrent connections

    async def savePage(self, url, pagefolder='page', session=None):
        """Save webpage components based on the input URL and directory name."""
        try:
            async with session.get(url, timeout=10) as response:
                content = await response.read()
                if len(content) > self.size_limit:
                    return False, "Size limit of 10 MB exceeded."
                self.soup = BeautifulSoup(content, features="lxml")
            if not os.path.exists(pagefolder):
                os.makedirs(pagefolder, exist_ok=True)
            tasks = []
            if self.imgFlg:
                tasks.append(self._soupfindnSave(url, pagefolder, tag2find='img', inner='src', session=session))
            if self.linkFlg:
                tasks.append(self._soupfindnSave(url, pagefolder, tag2find='link', inner='href', session=session))
            if self.scriptFlg:
                tasks.append(self._soupfindnSave(url, pagefolder, tag2find='script', inner='src', session=session))
            await asyncio.gather(*tasks)
            async with aiofiles.open(os.path.join(pagefolder, 'page.html'), 'wb') as file:
                await file.write(self.soup.prettify('utf-8'))
            return True, None
        except Exception as e:
            return False, f"Failed to download: {str(e)}"

    async def _soupfindnSave(self, url, pagefolder, tag2find='img', inner='src', session=None):
        """Saves all tag2find objects in the kred pagefolder."""
        pagefolder = os.path.join(pagefolder, tag2find)
        if not os.path.exists(pagefolder):
            os.makedirs(pagefolder, exist_ok=True)
        tasks = []
        for res in self.soup.findAll(tag2find):
            if not res.has_attr(inner):
                continue
            filename = re.sub(r'\W+', '.', os.path.basename(res[inner]))
            if tag2find == 'link' and not any(ext in filename for ext in self.linkType):
                filename += '.html'
            fileurl = urljoin(url, res.get(inner))
            filepath = os.path.join(pagefolder, filename)
            res[inner] = os.path.join(os.path.basename(pagefolder), filename)
            tasks.append(self._download_file(fileurl, filepath, session))
        # Batch tasks to avoid overwhelming the event loop
        for i in range(0, len(tasks), 50):  # Process in batches of 50
            await asyncio.gather(*tasks[i:i+50])

    async def _download_file(self, fileurl, filepath, session):
        """Download a single file and save it asynchronously."""
        async with self.semaphore:
            try:
                async with session.get(fileurl, timeout=5) as response:
                    content = await response.read()
                    if len(content) > self.size_limit or len(content) == 0:
                        return
                    async with aiofiles.open(filepath, 'wb') as file:
                        await file.write(content)
            except Exception as exc:
                print(f"Error downloading {fileurl}: {exc}", file=sys.stderr)

def create_zip(folder_path):
    """Create a zip file from the folder in memory."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, folder_path))
    zip_buffer.seek(0)
    return zip_buffer

def setup_ws_handler(app: Client):
    @app.on_message(filters.command(["ws", "websource"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def websource(client: Client, message):
        if len(message.command) < 2:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Please provide at least one valid URL.**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        url = message.command[1]
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        loading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**Downloading Website Source...**",
            parse_mode=ParseMode.MARKDOWN
        )

        async with aiohttp.ClientSession() as session:
            downloader = UrlDownloader()
            pagefolder = f"page_{message.chat.id}_{message.id}"
            success, error = await downloader.savePage(url, pagefolder, session)

            if not success:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=loading_message.id,
                    text="**❌ Failed to download source code. Please check the URL and try again.**",
                    parse_mode=ParseMode.MARKDOWN
                )
                if os.path.exists(pagefolder):
                    import shutil
                    shutil.rmtree(pagefolder)
                return

            zip_buffer = create_zip(pagefolder)
            user = message.from_user
            user_mention = f"[{user.first_name} {user.last_name or ''}](tg://user?id={user.id})".strip()
            caption = (
                f"**Source Code Downloaded ✅**\n"
                f"**━━━━━━━━━━━**\n"
                f"**Site:** `{url}`\n"
                f"**Files:** `HTML`, `CSS`, `JS`\n"
                f"**━━━━━━━━━━━**\n"
                f"**Downloaded By:** {user_mention}"
            )

            await client.delete_messages(chat_id=message.chat.id, message_ids=loading_message.id)
            await client.send_document(
                chat_id=message.chat.id,
                document=zip_buffer,
                file_name=f"{urlparse(url).netloc}_source.zip",
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )

            import shutil
            shutil.rmtree(pagefolder)
