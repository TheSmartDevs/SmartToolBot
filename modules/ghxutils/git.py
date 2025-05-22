# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import shutil
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from config import COMMAND_PREFIX
from utils import notify_admin  # Import notify_admin from utils

# Configure logging
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def check_git_installed():
    """Check if git is available on server"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        if proc.returncode != 0:
            raise Exception("Git is not installed or not working")
        return True
    except Exception as e:
        logger.error(f"Git installation check failed: {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}git", e, None)
        return False

async def get_repo_branches(repo_url):
    """Fetch all branches from remote repo"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "ls-remote", "--heads", repo_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"Failed to fetch branches: {stderr.decode()}")
        return [line.split("refs/heads/")[-1] 
                for line in stdout.decode().splitlines() 
                if "refs/heads/" in line]
    except Exception as e:
        logger.error(f"Error fetching branches for repo '{repo_url}': {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}git", e, None)
        return None

async def fetch_github_api(session, url):
    """Fetch data from GitHub API"""
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an exception for non-200 status codes
            return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"GitHub API error for URL '{url}': {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}git", e, None)
        return None

async def get_github_repo_details(repo_url):
    """Get repository details from GitHub API"""
    try:
        parts = repo_url.rstrip('/').split('/')
        user_name = parts[-2]
        repo_name = parts[-1].replace(".git", "")
        
        async with aiohttp.ClientSession() as session:
            api_url = f"https://api.github.com/repos/{user_name}/{repo_name}"
            repo_data = await fetch_github_api(session, api_url)
            
            if not repo_data:
                raise Exception("Failed to fetch repo details")
                
            return {
                'forks_count': repo_data.get('forks_count', 0),
                'description': repo_data.get('description', 'No description available'),
                'default_branch': repo_data.get('default_branch', 'main')
            }
    except Exception as e:
        logger.error(f"Error fetching GitHub repo details for '{repo_url}': {e}")
        # Notify admins
        await notify_admin(None, f"{COMMAND_PREFIX}git", e, None)
        return None

async def git_download_handler(client, message):
    # Check git installation
    if not await check_git_installed():
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>❌ This Repo Can Not Be Installed On My Server </b>",
            parse_mode=ParseMode.HTML
        )
        return

    if len(message.command) < 2:
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>⚠️ Please provide a valid GitHub URL</b>",
            parse_mode=ParseMode.HTML
        )
        return

    repo_url = message.command[1]
    requested_branch = message.command[2] if len(message.command) > 2 else None

    # Validate URL
    if "github.com" not in repo_url:
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>❌ Invalid Github URL Or Repo Unavailable</b>",
            parse_mode=ParseMode.HTML
        )
        return

    status_msg = await client.send_message(
        chat_id=message.chat.id,
        text="<b>🔍 Analyzing The Repository...</b>",
        parse_mode=ParseMode.HTML
    )

    try:
        # Extract repo info from URL
        parts = repo_url.rstrip('/').split('/')
        user_name = parts[-2]
        repo_name = parts[-1].replace(".git", "")

        # Get GitHub API details
        repo_details = await get_github_repo_details(repo_url)
        forks_count = repo_details['forks_count'] if repo_details else 0
        description = repo_details['description'] if repo_details else 'No description available'

        # Get available branches
        branches = await get_repo_branches(repo_url)
        if not branches:
            await client.send_message(
                chat_id=message.chat.id,
                text="<b>Broh The Repository Is Private </b>",
                parse_mode=ParseMode.HTML
            )
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}git", Exception("Repository is private or inaccessible"), message)
            return

        # Determine branch to use
        if requested_branch:
            if requested_branch not in branches:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=(
                        f"<b>⚠️ Branch '{requested_branch}' not found</b>\n\n"
                        f"<b>Available branches:</b>\n{', '.join(branches)}"
                    ),
                    parse_mode=ParseMode.HTML
                )
                return
            branch = requested_branch
        else:
            branch = "main" if "main" in branches else "master" if "master" in branches else branches[0]

        await status_msg.edit_text(
            f"<b>⏬ Downloading {branch} As Zip...</b>",
            parse_mode=ParseMode.HTML
        )

        # Prepare directories
        clone_dir = f"repos/{repo_name}_{branch}"
        os.makedirs("repos", exist_ok=True)

        # Clone repository
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "-b", branch, "--depth", "1", repo_url, clone_dir
        )
        await proc.wait()

        if proc.returncode != 0:
            raise Exception("Failed to clone repository")

        # Create zip archive
        await status_msg.edit_text(
            "<b>✨ Compressing The Repository...</b>",
            parse_mode=ParseMode.HTML
        )
        zip_path = f"{clone_dir}.zip"
        shutil.make_archive(clone_dir, 'zip', clone_dir)

        # Prepare repository details message
        repo_info = (
            "<b>📁 Downloaded Repository Details</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Repo Owner:</b> <code>{user_name}</code>\n"
            f"📂 <b>Repo Name:</b> <code>{repo_name}</code>\n"
            f"🔀 <b>Forks Count:</b> <code>{forks_count}</code>\n"
            f"🌿 <b>Branch:</b> <code>{branch}</code>\n"
            f"🔗 <b>URL:</b> <code>{repo_url}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>Repo Description:</b>\n<code>{description}</code>\n\n"
            f"🌱 <b>Available Branches:</b> <code>{', '.join(branches)}</code>"
        )

        # Send results
        await status_msg.edit_text(
            "<b>Uploading The Repository...</b>",
            parse_mode=ParseMode.HTML
        )
        await client.send_document(
            chat_id=message.chat.id,
            document=zip_path,
            caption=repo_info,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"Error downloading GitHub repo '{repo_url}': {e}")
        # Notify admins
        await notify_admin(client, f"{COMMAND_PREFIX}git", e, message)
        # Send user-facing error message
        await client.send_message(
            chat_id=message.chat.id,
            text="<b>❌ Sorry Bro Github Repo Dl API Dead</b>",
            parse_mode=ParseMode.HTML
        )
    finally:
        # Cleanup
        try:
            await status_msg.delete()
            if 'clone_dir' in locals() and os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)
            if 'zip_path' in locals() and os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            # Notify admins
            await notify_admin(client, f"{COMMAND_PREFIX}git", e, message)

def setup_git_handler(app):
    """Register git command handler"""
    app.add_handler(
        MessageHandler(
            git_download_handler,
            filters.command(["git"], prefixes=COMMAND_PREFIX) & 
            (filters.group | filters.private)
        )
    )
