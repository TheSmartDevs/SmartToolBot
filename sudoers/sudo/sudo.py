# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from config import OWNER_ID, COMMAND_PREFIX
from core import auth_admins
from utils import LOGGER
from pyrogram.errors import UserIdInvalid, UsernameInvalid, PeerIdInvalid

def setup_sudo_handler(app: Client):
    async def get_auth_admins():
        """Retrieve all authorized admins from MongoDB."""
        try:
            admins = await auth_admins.find({}, {"user_id": 1, "title": 1, "auth_date": 1, "_id": 0}).to_list(None)
            return {admin["user_id"]: {"title": admin["title"], "auth_date": admin["auth_date"]} for admin in admins}
        except Exception as e:
            LOGGER.error(f"Error fetching auth admins: {e}")
            return {}

    async def add_auth_admin(user_id: int, title: str):
        """Add or update an authorized admin in MongoDB with timestamp."""
        try:
            await auth_admins.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "title": title, "auth_date": datetime.utcnow()}},
                upsert=True
            )
            LOGGER.info(f"Added/Updated admin {user_id} with title {title}")
            return True
        except Exception as e:
            LOGGER.error(f"Error adding/updating admin {user_id}: {e}")
            return False

    async def remove_auth_admin(user_id: int):
        """Remove an authorized admin from MongoDB."""
        try:
            result = await auth_admins.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                LOGGER.info(f"Removed admin {user_id}")
                return True
            else:
                LOGGER.info(f"Admin {user_id} not found for removal")
                return False
        except Exception as e:
            LOGGER.error(f"Error removing admin {user_id}: {e}")
            return False

    async def resolve_user(client: Client, identifier: str):
        """Resolve user by ID or username to get user_id and full name."""
        try:
            if identifier.startswith("@"):
                user = await client.get_users(identifier)
                return user.id, f"{user.first_name} {user.last_name or ''}".strip()
            else:
                user_id = int(identifier)
                user = await client.get_users(user_id)  # Verify user exists
                return user_id, f"{user.first_name} {user.last_name or ''}".strip()
        except (UserIdInvalid, UsernameInvalid, PeerIdInvalid, ValueError) as e:
            LOGGER.error(f"Error resolving user {identifier}: {e}")
            return None, None

    @app.on_message(filters.command(["getadmins"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def get_admins_command(client, message):
        user_id = message.from_user.id
        if user_id != OWNER_ID:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Kids Not Allowed To Do This ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        loading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**✘ Fetching Admins List ↯**",
            parse_mode=ParseMode.MARKDOWN
        )
        await asyncio.sleep(1)

        admin_list = ["**✘ Bot Admins List ↯**"]
        # Add OWNER_ID with title "Owner"
        try:
            user = await client.get_users(OWNER_ID)
            full_name = f"{user.first_name} {user.last_name or ''}".strip()
            admin_list.append(
                f"\n**✘ Name: {full_name} ↯**\n"
                f"**✘ Title: Owner ↯**\n"
                f"**✘ Auth Date: Not applicable ↯**"
            )
        except Exception:
            admin_list.append(
                f"\n**✘ Name: ID {OWNER_ID} (Not found) ↯**\n"
                f"**✘ Title: Owner ↯**\n"
                f"**✘ Auth Date: Not applicable ↯**"
            )

        # Add AUTH_ADMIN_IDS from MongoDB
        auth_admins_data = await get_auth_admins()
        for admin_id, data in auth_admins_data.items():
            try:
                user = await client.get_users(admin_id)
                full_name = f"{user.first_name} {user.last_name or ''}".strip()
                auth_date = data["auth_date"].strftime("%Y-%m-%d %H:%M:%S")
                admin_list.append(
                    f"\n**✘ Name: {full_name} ↯**\n"
                    f"**✘ Title: {data['title']} ↯**\n"
                    f"**✘ Auth Date: {auth_date} ↯**"
                )
            except Exception:
                auth_date = data["auth_date"].strftime("%Y-%m-%d %H:%M:%S")
                admin_list.append(
                    f"\n**✘ Name: ID {admin_id} (Not found) ↯**\n"
                    f"**✘ Title: {data['title']} ↯**\n"
                    f"**✘ Auth Date: {auth_date} ↯**"
                )

        if len(admin_list) == 1:
            admin_list.append("\nNo additional admins found.")

        await loading_message.edit_text(
            text="\n".join(admin_list),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✘ Close ↯", callback_data="close_admins$")]
            ])
        )

    @app.on_message(filters.command(["auth"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def auth_command(client, message):
        user_id = message.from_user.id
        if user_id != OWNER_ID:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Kids Not Allowed To Do This ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Bruh! Provide A Username Or Userid ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        identifier, title = args[1], args[2]
        target_user_id, full_name = await resolve_user(client, identifier)
        if not target_user_id:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Kids Can't Be Promoted ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if target_user_id == OWNER_ID:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Cannot Modify Owners Permission ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        loading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**✘ Adding User To Bot Admins List ↯**",
            parse_mode=ParseMode.MARKDOWN
        )
        await asyncio.sleep(1)

        if await add_auth_admin(target_user_id, title):
            await loading_message.edit_text(
                text=f"**✘ Successfully Authorized User {full_name or identifier} As {title} ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await loading_message.edit_text(
                text="**✘ Kids Can't Be Promoted ↯**",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_message(filters.command(["unauth"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def unauth_command(client, message):
        user_id = message.from_user.id
        if user_id != OWNER_ID:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Kids Not Allowed To Do This ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Bruh! Provide A Username Or Userid ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        identifier = args[1]
        target_user_id, full_name = await resolve_user(client, identifier)
        if not target_user_id:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Invalid user ID or username! ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if target_user_id == OWNER_ID:
            await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Cannot Modify Owners Permission ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        loading_message = await client.send_message(
            chat_id=message.chat.id,
            text="**✘ Removing User From Bot Admins List ↯**",
            parse_mode=ParseMode.MARKDOWN
        )
        await asyncio.sleep(1)

        if await remove_auth_admin(target_user_id):
            await loading_message.edit_text(
                text=f"**✘ Successfully Removed User {full_name or identifier} From Admins ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await loading_message.edit_text(
                text=f"**✘ The User Is Not In Admin List ↯**",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_callback_query(filters.regex(r"^close_admins\$"))
    async def handle_close_callback(client: Client, query: CallbackQuery):
        user_id = query.from_user.id
        if user_id != OWNER_ID:
            await query.answer(
                text="✘ Kids Not Allowed To Do This ↯",
                show_alert=True
            )
            return
        await query.message.delete()
        await query.answer()
