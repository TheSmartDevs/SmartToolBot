import logging
from pyrogram import Client
from pyrogram.types import Message
from config import ADMIN_IDS

async def notify_admin(client: Client, command: str, error: Exception, message: Message):
    """
    Notify admins about an error with concise information.
    
    Args:
        client: Pyrogram Client instance
        command: The command that caused the error (e.g., '/ai')
        error: The exception object
        message: The Message object containing user and chat details
    """
    try:
        # Get user details
        user = message.from_user
        user_fullname = f"{user.first_name} {user.last_name or ''}".strip()
        user_id = user.id
        
        # Format error message
        error_message = (
            f"**Hey Admin Sir, There Is A Issue With Command `{command}` **"
            f"**And The Issue Is {str(error)} From `{user_fullname}` ** "
            f"**And ChatID `{message.chat.id}` **"
        )
        
        # Send notification to all admins
        for admin_id in ADMIN_IDS:
            try:
                await client.send_message(admin_id, error_message)
            except Exception as admin_error:
                logging.error(f"Failed to notify admin {admin_id}: {admin_error}")
                
    except Exception as e:
        logging.error(f"Error in notify_admin: {e}")