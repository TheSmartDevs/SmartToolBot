# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
# This Script Mainly Based On https://github.com/abirxdhackz/SmartPayBot
import logging
import uuid
import hashlib
import time
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
from pyrogram.enums import ParseMode
from config import OWNER_ID, DEVELOPER_USER_ID

# Setup logging
logger = logging.getLogger(__name__)

# Shared Strings and Emojis
DONATION_OPTIONS_TEXT = """
**Why should you donate to Smart Tools?** 
**━━━━━━━━━━━━━━━━━━**
🌟 **Love the service?** 
Your support helps keep **SmartTools** fast, reliable, and free for everyone. 
Even a small **Donation** makes a big difference! 💖

👇 **Choose an amount to donate:** 

**Why donate?** 
More donation = more motivation 
More motivation = better tools 
Better tools = more productivity 
More productivity = less wasted time 
Less wasted time = more done with **Smart Tools** 💡
**More Muhahaha… 🤓🔥**
"""

PAYMENT_SUCCESS_TEXT = """
**✅ Donation Successful!**

🎉 Huge thanks **{0}** for donating **{1} Stars** to support **Smart Tools!**
Your contribution helps keep everything running smooth and awesome 🚀

**🧾 Transaction ID:** `{2}`
"""

ADMIN_NOTIFICATION_TEXT = """
🌟 **Hey Bruh! New Donation Received!** 👀
✨ **From:** {0} 💫
⁉️ **User ID:** `{1}`
🌐 **Username:** {2}
💥 **Amount:** {3} Stars 🌟
📝 **Transaction ID:** `{4}`
"""

INVOICE_CREATION_TEXT = "Generating invoice for {0} Stars...\nPlease wait ⏳"
INVOICE_CONFIRMATION_TEXT = "**✅ Invoice for {0} Stars has been generated! You can now proceed to pay via the button below.**"
DUPLICATE_INVOICE_TEXT = "**🚫 Wait Bro! Donation Already in Progress!**"
INVOICE_FAILED_TEXT = "**❌ Invoice Creation Failed, Bruh! Try Again!**"
PAYMENT_FAILED_TEXT = "**❌ Sorry Bro! Payment Declined! Contact Support!**"

# Store active invoice requests (in-memory, replace with DB for production)
active_invoices = {}

# Function to format time durations
def timeof_fmt(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

# Generate Dynamic Donation Buttons
def get_donation_buttons(amount: int = 5):
    buttons = []
    if amount == 5:
        buttons.append([
            InlineKeyboardButton(f"{amount} ⭐️", callback_data=f"donate_{amount}"),
            InlineKeyboardButton("+5", callback_data=f"increment_donate_{amount}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("-5", callback_data=f"decrement_donate_{amount}"),
            InlineKeyboardButton(f"{amount} ⭐️", callback_data=f"donate_{amount}"),
            InlineKeyboardButton("+5", callback_data=f"increment_donate_{amount}")
        ])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="about_me")])
    return InlineKeyboardMarkup(buttons)

# Generate and Send Invoice Function
async def generate_invoice(client: Client, chat_id: int, user_id: int, quantity: int, is_callback: bool = False, callback_query: CallbackQuery = None):
    """Generate and send an invoice with minimal message edits for speed."""
    if user_id in active_invoices:
        if is_callback:
            await callback_query.answer("Donation already in progress!")
        else:
            await client.send_message(chat_id, DUPLICATE_INVOICE_TEXT, parse_mode=ParseMode.MARKDOWN)
        return

    active_invoices[user_id] = True
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="about_me")]])

    try:
        # Generate unique payload
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        invoice_payload = f"donation_{user_id}_{quantity}_{timestamp}_{unique_id}"
        random_id = int(hashlib.sha256(invoice_payload.encode()).hexdigest(), 16) % (2**63)

        title = "Support Smart Tools"
        description = f"Contribute {quantity} Stars to support ongoing development and keep the tools free, fast, and reliable for everyone 💫 Every star helps us grow!"
        currency = "XTR"

        # Create Invoice object
        invoice = Invoice(
            currency=currency,
            prices=[LabeledPrice(label=f"⭐️ {quantity} Stars", amount=quantity)],
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
            rows=[KeyboardButtonRow(buttons=[KeyboardButtonBuy(text="💫 Donate via Stars")])]
        )

        # Resolve peer
        peer = await client.resolve_peer(chat_id)

        # Send loading message only if not a callback
        if not is_callback:
            loading_message = await client.send_message(
                chat_id,
                INVOICE_CREATION_TEXT.format(quantity),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )

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

        # Update message to confirmation
        if is_callback:
            await callback_query.message.edit_text(
                INVOICE_CONFIRMATION_TEXT.format(quantity),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )
            await callback_query.answer("✅ Invoice Generated! Pay Now! ⭐️")
        else:
            await loading_message.edit_text(
                INVOICE_CONFIRMATION_TEXT.format(quantity),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )

    except Exception as e:
        await client.send_message(
            chat_id,
            INVOICE_FAILED_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button
        )
        if is_callback:
            await callback_query.answer("Failed to create invoice.")
    finally:
        active_invoices.pop(user_id, None)

# Handle Callback Queries for Donation Buttons
async def handle_donate_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if data == "donate":
        reply_markup = get_donation_buttons()
        await callback_query.message.edit_text(
            DONATION_OPTIONS_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        await callback_query.answer()
    elif data.startswith("donate_"):
        quantity = int(data.split("_")[1])
        await generate_invoice(client, chat_id, user_id, quantity, is_callback=True, callback_query=callback_query)
    elif data.startswith("increment_donate_"):
        current_amount = int(data.split("_")[2])
        new_amount = current_amount + 5
        reply_markup = get_donation_buttons(new_amount)
        await callback_query.message.edit_text(
            DONATION_OPTIONS_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        await callback_query.answer(f"Updated to {new_amount} Stars")
    elif data.startswith("decrement_donate_"):
        current_amount = int(data.split("_")[2])
        new_amount = max(5, current_amount - 5)
        reply_markup = get_donation_buttons(new_amount)
        await callback_query.message.edit_text(
            DONATION_OPTIONS_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        await callback_query.answer(f"Updated to {new_amount} Stars")

# Raw Update Handler for Payment Processing
async def raw_update_handler(client: Client, update, users, chats):
    if isinstance(update, UpdateBotPrecheckoutQuery):
        try:
            await client.invoke(
                SetBotPrecheckoutResults(query_id=update.query_id, success=True)
            )
        except Exception as e:
            await client.invoke(
                SetBotPrecheckoutResults(
                    query_id=update.query_id,
                    success=False,
                    error="Failed to process pre-checkout query."
                )
            )
    elif isinstance(update, UpdateBotShippingQuery):
        try:
            await client.invoke(
                SetBotShippingResults(query_id=update.query_id, shipping_options=[])
            )
        except Exception as e:
            await client.invoke(
                SetBotShippingResults(
                    query_id=update.query_id,
                    error="Shipping not required for donations."
                )
            )
    elif isinstance(update, UpdateNewMessage) and isinstance(update.message, MessageService) and isinstance(update.message.action, MessageActionPaymentSentMe):
        payment = update.message.action
        try:
            user_id = update.message.from_id.user_id if update.message.from_id and hasattr(update.message.from_id, 'user_id') else None
            if not user_id and users:
                possible_user_ids = [uid for uid in users if uid > 0]
                user_id = possible_user_ids[0] if possible_user_ids else None

            if isinstance(update.message.peer_id, PeerUser):
                chat_id = update.message.peer_id.user_id
            elif isinstance(update.message.peer_id, PeerChat):
                chat_id = update.message.peer_id.chat_id
            elif isinstance(update.message.peer_id, PeerChannel):
                chat_id = update.message.peer_id.channel_id
            else:
                chat_id = user_id

            if not user_id or not chat_id:
                raise ValueError(f"Invalid chat_id ({chat_id}) or user_id ({user_id})")

            user = users.get(user_id)
            full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown" if user else "Unknown"
            username = f"@{user.username}" if user and user.username else "@N/A"

            await client.send_message(
                chat_id,
                PAYMENT_SUCCESS_TEXT.format(full_name, payment.total_amount, payment.charge.id),
                parse_mode=ParseMode.MARKDOWN
            )

            admin_text = ADMIN_NOTIFICATION_TEXT.format(full_name, user_id, username, payment.total_amount, payment.charge.id)
            for admin_id in OWNER_ID:
                try:
                    await client.send_message(admin_id, admin_text, parse_mode=ParseMode.MARKDOWN)
                except Exception:
                    pass
        except Exception as e:
            if 'chat_id' in locals():
                await client.send_message(
                    chat_id,
                    PAYMENT_FAILED_TEXT,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Support", user_id=DEVELOPER_USER_ID)]])
                )
