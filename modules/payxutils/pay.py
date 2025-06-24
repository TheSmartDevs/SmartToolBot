# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# This Script Mainly Based On https://github.com/abirxdhackz/SmartPayBot
import uuid
import hashlib
import time
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.messages import SendMedia, SetBotPrecheckoutResults, SetBotShippingResults
from pyrogram.raw.types import (
    InputMediaInvoice,
    Invoice,
    DataJSON,
    LabeledPrice,
    UpdateBotPrecheckoutQuery,
    UpdateBotShippingQuery,
    UpdateNewMessage,
    MessageService,
    MessageActionPaymentSentMe,
    PeerUser,
    PeerChat,
    PeerChannel,
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonBuy
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, RawUpdateHandler
from config import COMMAND_PREFIX, OWNER_ID, DEVELOPER_USER_ID
from utils import LOGGER  # Import LOGGER from utils
from core import banned_users  # Check if user is banned

# Use the imported LOGGER
logger = LOGGER

# Shared Strings and Emojis
DONATION_OPTIONS_TEXT = """
💥 **Why support Smart Tools?** 💥
**✘ ━━━━━━━━━━━━━━━━━━ ✘**
🌟 **Love the service?** 🌟
Your support helps keep **SmartTools** fast, reliable, and free for everyone. ✨
Even a small **Gift or Donation** makes a big difference! 💖

👇 **Choose an amount to contribute:** 👀

❄️ **Why contribute?** ❄️
More support = more motivation 🌐
More motivation = better tools 💫
Better tools = more productivity 🔥
More productivity = less wasted time 🇧🇩
Less wasted time = more done with **Smart Tools** 💡
**More Muhahaha… 🤓🔥**
"""

PAYMENT_SUCCESS_TEXT = """
**✅ Contribution Successful!**

🎉 Huge thanks **{0}** for contributing **{1} Stars** to support **Smart Tools!**
Your support helps keep everything running smooth and awesome 🚀

**🧾 Transaction ID:** `{2}`
"""

ADMIN_NOTIFICATION_TEXT = """
🌟 **Hey Bruh! New Contribution Received!** 👀
✨ **From:** {0} 💫
⁉️ **User ID:** `{1}`
🌐 **Username:** {2}
💥 **Amount:** {3} Stars 🌟
📝 **Transaction ID:** `{4}`
"""

INVOICE_CREATION_TEXT = "Generating invoice for {0} Stars...\nPlease wait ⏳"
INVOICE_CONFIRMATION_TEXT = "**✅ Invoice for {0} Stars has been generated! You can now proceed to pay via the button below.**"
DUPLICATE_INVOICE_TEXT = "**🚫 Wait Bro! Contribution Already in Progress!**"
INVALID_INPUT_TEXT = "**❌ Sorry Bro! Invalid Input! Use a positive number.**"
INVOICE_FAILED_TEXT = "**❌ Invoice Creation Failed, Bruh! Try Again!**"
PAYMENT_FAILED_TEXT = "**❌ Sorry Bro! Payment Declined! Contact Support!**"

# Store active invoices to prevent duplicates (in-memory, replace with DB for production)
active_invoices = {}

# Modular Handler Setup
def setup_donate_handler(app):
    # Generate Dynamic Contribution Buttons
    def get_donation_buttons(amount: int = 5):
        if amount == 5:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{amount} 🌟", callback_data=f"gift_{amount}"),
                 InlineKeyboardButton("+5", callback_data=f"increment_gift_{amount}")]
            ])
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("-5", callback_data=f"decrement_gift_{amount}"),
             InlineKeyboardButton(f"{amount} 🌟", callback_data=f"gift_{amount}"),
             InlineKeyboardButton("+5", callback_data=f"increment_gift_{amount}")]
        ])

    # Generate and Send Invoice Function
    async def generate_invoice(client: Client, chat_id: int, user_id: int, amount: int):
        if active_invoices.get(user_id):
            await client.send_message(chat_id, DUPLICATE_INVOICE_TEXT, parse_mode=ParseMode.MARKDOWN)
            return

        # Send loading message with back button
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_donate_options")]])
        loading_message = await client.send_message(
            chat_id,
            INVOICE_CREATION_TEXT.format(amount),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button
        )

        try:
            active_invoices[user_id] = True

            # Generate unique payload with UUID
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            invoice_payload = f"contribution_{user_id}_{amount}_{timestamp}_{unique_id}"
            random_id = int(hashlib.sha256(invoice_payload.encode()).hexdigest(), 16) % (2**63)

            title = "Support Smart Tools"
            description = f"Contribute {amount} Stars to support ongoing development and keep the tools free, fast, and reliable for everyone 💫 Every star helps us grow!"
            currency = "XTR"

            # Create Invoice object
            invoice = Invoice(
                currency=currency,
                prices=[LabeledPrice(label=f"⭐ {amount} Stars", amount=amount)],
                max_tip_amount=0,
                suggested_tip_amounts=[],
                recurring=False,
                test=False,
                name_requested=False,
                phone_requested=False,
                email_requested=False,
                shipping_address_requested=False,
                flexible=False
            )

            # Create InputMediaInvoice
            media = InputMediaInvoice(
                title=title,
                description=description,
                invoice=invoice,
                payload=invoice_payload.encode(),
                provider="STARS",
                provider_data=DataJSON(data="{}")
            )

            # Create ReplyInlineMarkup with KeyboardButtonBuy
            markup = ReplyInlineMarkup(
                rows=[
                    KeyboardButtonRow(
                        buttons=[
                            KeyboardButtonBuy(text="💫 Donate Via Stars")
                        ]
                    )
                ]
            )

            # Resolve peer
            peer = await client.resolve_peer(chat_id)

            # Send the invoice
            await client.invoke(
                SendMedia(
                    peer=peer,
                    media=media,
                    message="",
                    random_id=random_id,
                    reply_markup=markup
                )
            )

            # Edit loading message to confirmation
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                INVOICE_CONFIRMATION_TEXT.format(amount),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )

            logger.info(f"✅ Invoice sent for {amount} stars to user {user_id} with payload {invoice_payload}")
        except Exception as e:
            logger.error(f"❌ Failed to generate invoice for user {user_id}: {str(e)}")
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                INVOICE_FAILED_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )
        finally:
            active_invoices.pop(user_id, None)

    # Handle /donate and /gift Commands
    async def donate_command(client: Client, message: Message):
        # Check if user is banned
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            return

        logger.info(f"Donation command received: user: {user_id or 'unknown'}, chat: {message.chat.id}")
        if len(message.command) == 1:
            # Show contribution options with dynamic buttons
            reply_markup = get_donation_buttons()
            await client.send_message(
                chat_id=message.chat.id,
                text=DONATION_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif len(message.command) == 2 and message.command[1].isdigit() and int(message.command[1]) > 0:
            # Generate invoice for specified amount
            amount = int(message.command[1])
            await generate_invoice(client, message.chat.id, message.from_user.id, amount)
        else:
            # Invalid command
            await client.send_message(
                chat_id=message.chat.id,
                text=INVALID_INPUT_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.id
            )

    # Handle Callback Queries for Contribution Buttons and "Back"
    async def handle_donate_callback(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        # Check if user is banned
        if user_id and await banned_users.find_one({"user_id": user_id}):
            await client.send_message(chat_id, "**✘Sorry You're Banned From Using Me↯**", parse_mode=ParseMode.MARKDOWN)
            await callback_query.answer("You are banned!", show_alert=True)
            return

        logger.info(f"Callback query received: data={data}, user: {user_id}, chat: {chat_id}")
        if data.startswith("gift_"):
            # Handle gift_X
            quantity = int(data.split("_")[1])
            await generate_invoice(client, chat_id, user_id, quantity)
            await callback_query.answer("✅ Invoice Generated! Pay Now! 🌟")
        elif data.startswith("increment_gift_"):
            current_amount = int(data.split("_")[2])
            new_amount = current_amount + 5
            reply_markup = get_donation_buttons(new_amount)
            await client.edit_message_text(
                chat_id,
                callback_query.message.id,
                DONATION_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            await callback_query.answer(f"Updated to {new_amount} Stars")
        elif data.startswith("decrement_gift_"):
            current_amount = int(data.split("_")[2])
            new_amount = max(5, current_amount - 5)  # Minimum 5 Stars
            reply_markup = get_donation_buttons(new_amount)
            await client.edit_message_text(
                chat_id,
                callback_query.message.id,
                DONATION_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            await callback_query.answer(f"Updated to {new_amount} Stars")
        elif data == "show_donate_options":
            # Show contribution options again
            reply_markup = get_donation_buttons()
            await client.edit_message_text(
                chat_id,
                callback_query.message.id,
                DONATION_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            await callback_query.answer()

    # Raw Update Handler for Payment Processing
    async def raw_update_handler(client: Client, update, users, chats):
        if isinstance(update, UpdateBotPrecheckoutQuery):
            try:
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=True
                    )
                )
                logger.info(f"✅ Pre-checkout query {update.query_id} OK for user {update.user_id}")
            except Exception as e:
                logger.error(f"❌ Pre-checkout query {update.query_id} failed: {str(e)}")
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=False,
                        error="Failed to process pre-checkout."
                    )
                )
        elif isinstance(update, UpdateBotShippingQuery):
            try:
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        shipping_options=[]  # No shipping for digital contributions
                    )
                )
                logger.info(f"✅ Shipping query {update.query_id} OK for user {update.user_id}")
            except Exception as e:
                logger.error(f"❌ Shipping query {update.query_id} failed: {str(e)}")
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        error="Shipping not needed for contributions."
                    )
                )
        elif isinstance(update, UpdateNewMessage) and isinstance(update.message, MessageService) and isinstance(update.message.action, MessageActionPaymentSentMe):
            payment = update.message.action
            try:
                # Extract user_id and chat_id
                user_id = update.message.from_id.user_id if update.message.from_id and hasattr(update.message.from_id, 'user_id') else None
                if not user_id and users:
                    possible_user_ids = [uid for uid in users if uid > 0]
                    user_id = possible_user_ids[0] if possible_user_ids else None

                if not user_id:
                    raise ValueError(f"Invalid user_id ({user_id})")

                # Check if user is banned
                if await banned_users.find_one({"user_id": user_id}):
                    await client.send_message(
                        user_id,
                        "**✘Sorry You're Banned From Using Me↯**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return

                if isinstance(update.message.peer_id, PeerUser):
                    chat_id = update.message.peer_id.user_id
                elif isinstance(update.message.peer_id, PeerChat):
                    chat_id = update.message.peer_id.chat_id
                elif isinstance(update.message.peer_id, PeerChannel):
                    chat_id = update.message.peer_id.channel_id
                else:
                    chat_id = None

                if not chat_id and user_id:
                    chat_id = user_id  # Assume private chat

                if not chat_id:
                    raise ValueError(f"Invalid chat_id ({chat_id})")

                # Get user details
                user = users.get(user_id)
                full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown" if user else "Unknown"
                username = f"@{user.username}" if user and user.username else "@N/A"

                # Send success message to user
                await client.send_message(
                    chat_id=chat_id,
                    text=PAYMENT_SUCCESS_TEXT.format(full_name, payment.total_amount, payment.charge.id),
                    parse_mode=ParseMode.MARKDOWN
                )

                # Notify Admins
                admin_text = ADMIN_NOTIFICATION_TEXT.format(full_name, user_id, username, payment.total_amount, payment.charge.id)
                for admin_id in OWNER_ID:
                    try:
                        await client.send_message(
                            chat_id=admin_id,
                            text=admin_text,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to notify admin {admin_id}: {str(e)}")

            except Exception as e:
                logger.error(f"❌ Payment processing failed for user {user_id if user_id else 'unknown'}: {str(e)}")
                if 'chat_id' in locals() and chat_id:
                    await client.send_message(
                        chat_id=chat_id,
                        text=PAYMENT_FAILED_TEXT,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Support", url=f"tg://user?id={DEVELOPER_USER_ID}")]])
                    )

    # Register Handlers
    app.add_handler(
        MessageHandler(
            donate_command,
            filters=filters.command(["donate", "gift"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(
            handle_donate_callback,
            filters=filters.regex(r'^(gift_\d+|increment_gift_\d+|decrement_gift_\d+|show_donate_options)$')
        ),
        group=2
    )
    app.add_handler(
        RawUpdateHandler(raw_update_handler),
        group=3
    )
