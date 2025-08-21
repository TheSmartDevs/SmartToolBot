#Copyright @ISmartCoder
#Updates Channel t.me/TheSmartDev 
import uuid
import hashlib
import time
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardButtonBuy, LabeledPrice
from pyrogram.raw.functions.messages import SetBotPrecheckoutResults, SetBotShippingResults
from pyrogram.raw.types import (
    UpdateBotPrecheckoutQuery,
    UpdateBotShippingQuery,
    UpdateNewMessage,
    MessageService,
    MessageActionPaymentSentMe,
    PeerUser,
    PeerChat,
    PeerChannel
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, RawUpdateHandler
from config import COMMAND_PREFIX, OWNER_ID, DEVELOPER_USER_ID, BAN_REPLY
from utils import LOGGER
from core import banned_users

logger = LOGGER

DONATION_OPTIONS_TEXT = """
**Why support Smart Tools?** 
**━━━━━━━━━━━━━━━━━━**
🌟 **Love the service?** 
Your support helps keep **SmartTools** fast, reliable, and free for everyone. 
Even a small **Gift or Donation** makes a big difference! 💖

👇 **Choose an amount to contribute:** 

**Why contribute?** 
More support = more motivation 
More motivation = better tools 
Better tools = more productivity 
More productivity = less wasted time 
Less wasted time = more done with **Smart Tools** 💡
**More Muhahaha… 🤓🔥**
"""

PAYMENT_SUCCESS_TEXT = """
**✅ Donation Successful!**

🎉 Huge thanks **{0}** for donating **{1}** ⭐️ to support **Smart Tool!**
Your contribution helps keep everything running smooth and awesome 🚀

**🧾 Transaction ID:** `{2}`
"""

ADMIN_NOTIFICATION_TEXT = """
**Hey New Donation Received 🤗**
**━━━━━━━━━━━━━━━**
**From: ** {0}
**Username:** {2}
**UserID:** `{1}`
**Amount:** {3} ⭐️
**Transaction ID:** `{4}`
**━━━━━━━━━━━━━━━**
**Click Below Button If Need Refund 💸**
"""

INVOICE_CREATION_TEXT = "Generating invoice for {0} Stars...\nPlease wait ⏳"
INVOICE_CONFIRMATION_TEXT = "**✅ Invoice for {0} Stars has been generated! You can now proceed to pay via the button below.**"
DUPLICATE_INVOICE_TEXT = "**🚫 Wait Bro! Contribution Already in Progress!**"
INVALID_INPUT_TEXT = "**❌ Sorry Bro! Invalid Input! Use a positive number.**"
INVOICE_FAILED_TEXT = "**❌ Invoice Creation Failed, Bruh! Try Again!**"
PAYMENT_FAILED_TEXT = "**❌ Sorry Bro! Payment Declined! Contact Support!**"
REFUND_SUCCESS_TEXT = "**✅ Refund Successfully Completed Bro!**\n\n**{0} Stars** have been refunded to **[{1}](tg://user?id={2})**"
REFUND_FAILED_TEXT = "**❌ Refund Failed!**\n\nFailed to refund **{0} Stars** to **{1}** (ID: `{2}`)\nError: {3}"

active_invoices = {}
payment_data = {}

def setup_donate_handler(app):
    def get_donation_buttons(amount: int = 5):
        if amount == 5:
            return InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{amount} ⭐️", callback_data=f"gift_{amount}"),
                 InlineKeyboardButton("+5", callback_data=f"increment_gift_{amount}")]
            ])
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("-5", callback_data=f"decrement_gift_{amount}"),
             InlineKeyboardButton(f"{amount} ⭐️", callback_data=f"gift_{amount}"),
             InlineKeyboardButton("+5", callback_data=f"increment_gift_{amount}")]
        ])

    async def generate_invoice(client: Client, chat_id: int, user_id: int, amount: int):
        if active_invoices.get(user_id):
            await client.send_message(chat_id, DUPLICATE_INVOICE_TEXT, parse_mode=ParseMode.MARKDOWN)
            return

        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_donate_options")]])
        loading_message = await client.send_message(
            chat_id,
            INVOICE_CREATION_TEXT.format(amount),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button
        )

        try:
            active_invoices[user_id] = True

            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            invoice_payload = f"contribution_{user_id}_{amount}_{timestamp}_{unique_id}"

            title = "Support Smart Tools"
            description = f"Contribute {amount} Stars to support ongoing development and keep the tools free, fast, and reliable for everyone 💫 Every star helps us grow!"
            currency = "XTR"
            
            prices = [LabeledPrice(label=f"⭐️ {amount} Stars", amount=amount)]
            
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButtonBuy("💫 Donate Via Stars")]
            ])

            await client.send_invoice(
                chat_id=chat_id,
                title=title,
                description=description,
                payload=invoice_payload,
                currency=currency,
                prices=prices,
                start_parameter="Basic",
                reply_markup=reply_markup
            )

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

    async def donate_command(client: Client, message: Message):
        user_id = message.from_user.id if message.from_user else None
        if user_id and await banned_users.banned_users.find_one({"user_id": user_id}):
            await client.send_message(message.chat.id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            return

        logger.info(f"Donation command received: user: {user_id or 'unknown'}, chat: {message.chat.id}")
        if len(message.command) == 1:
            reply_markup = get_donation_buttons()
            await client.send_message(
                chat_id=message.chat.id,
                text=DONATION_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif len(message.command) == 2 and message.command[1].isdigit() and int(message.command[1]) > 0:
            amount = int(message.command[1])
            await generate_invoice(client, message.chat.id, message.from_user.id, amount)
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=INVALID_INPUT_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.id
            )

    async def handle_donate_callback(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        if user_id and await banned_users.banned_users.find_one({"user_id": user_id}):
            await client.send_message(chat_id, BAN_REPLY, parse_mode=ParseMode.MARKDOWN)
            await callback_query.answer("You are banned!", show_alert=True)
            return

        logger.info(f"Callback query received: data={data}, user: {user_id}, chat: {chat_id}")
        
        if data.startswith("gift_"):
            quantity = int(data.split("_")[1])
            await generate_invoice(client, chat_id, user_id, quantity)
            await callback_query.answer("✅ Invoice Generated! Donate Now! ⭐️")
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
            new_amount = max(5, current_amount - 5)
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
            reply_markup = get_donation_buttons()
            await client.edit_message_text(
                chat_id,
                callback_query.message.id,
                DONATION_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            await callback_query.answer()
        elif data.startswith("refund_"):
            admin_ids = OWNER_ID if isinstance(OWNER_ID, (list, tuple)) else [OWNER_ID]
            if user_id in admin_ids or user_id == DEVELOPER_USER_ID:
                payment_id = data.replace("refund_", "")
                
                user_info = payment_data.get(payment_id)
                if not user_info:
                    await callback_query.answer("❌ Payment data not found!", show_alert=True)
                    return
                
                refund_user_id = user_info['user_id']
                refund_amount = user_info['amount']
                full_charge_id = user_info['charge_id']
                full_name = user_info['full_name']
                
                try:
                    result = await client.refund_star_payment(refund_user_id, full_charge_id)
                    if result:
                        await callback_query.message.edit_text(
                            REFUND_SUCCESS_TEXT.format(refund_amount, full_name, refund_user_id),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        await callback_query.answer("✅ Refund processed successfully!")
                        payment_data.pop(payment_id, None)
                    else:
                        await callback_query.answer("❌ Refund failed!", show_alert=True)
                except Exception as e:
                    logger.error(f"❌ Refund failed for user {refund_user_id}: {str(e)}")
                    await callback_query.message.edit_text(
                        REFUND_FAILED_TEXT.format(refund_amount, full_name, refund_user_id, str(e)),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await callback_query.answer("❌ Refund failed!", show_alert=True)
            else:
                await callback_query.answer("❌ You don't have permission to refund!", show_alert=True)

    async def raw_update_handler(client: Client, update, users, chats):
        if isinstance(update, UpdateBotPrecheckoutQuery):
            try:
                await client.answer_pre_checkout_query(
                    pre_checkout_query_id=update.query_id,
                    success=True
                )
                logger.info(f"✅ Pre-checkout query {update.query_id} OK for user {update.user_id}")
            except Exception as e:
                logger.error(f"❌ Pre-checkout query {update.query_id} failed: {str(e)}")
                await client.answer_pre_checkout_query(
                    pre_checkout_query_id=update.query_id,
                    success=False,
                    error="Failed to process pre-checkout."
                )
        elif isinstance(update, UpdateBotShippingQuery):
            try:
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        shipping_options=[]
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
            user_id = None
            chat_id = None
            
            try:
                if update.message.from_id and hasattr(update.message.from_id, 'user_id'):
                    user_id = update.message.from_id.user_id
                elif users:
                    possible_user_ids = [uid for uid in users if uid > 0]
                    user_id = possible_user_ids[0] if possible_user_ids else None

                if not user_id:
                    raise ValueError(f"Invalid user_id ({user_id})")

                if await banned_users.banned_users.find_one({"user_id": user_id}):
                    await client.send_message(
                        user_id,
                        BAN_REPLY,
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
                    chat_id = user_id

                if not chat_id:
                    raise ValueError(f"Invalid chat_id ({chat_id})")

                user = users.get(user_id) if users else None
                full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown" if user else "Unknown"
                username = f"@{user.username}" if user and user.username else "@N/A"

                payment_id = str(uuid.uuid4())[:16]
                payment_data[payment_id] = {
                    'user_id': user_id,
                    'full_name': full_name,
                    'username': username,
                    'amount': payment.total_amount,
                    'charge_id': payment.charge.id
                }

                success_message = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Transaction ID", copy_text=payment.charge.id)]
                ])

                await client.send_message(
                    chat_id=chat_id,
                    text=PAYMENT_SUCCESS_TEXT.format(full_name, payment.total_amount, payment.charge.id),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=success_message
                )

                admin_text = ADMIN_NOTIFICATION_TEXT.format(full_name, user_id, username, payment.total_amount, payment.charge.id)
                refund_button = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Refund {payment.total_amount} ⭐️", callback_data=f"refund_{payment_id}")]
                ])

                admin_ids = OWNER_ID if isinstance(OWNER_ID, (list, tuple)) else [OWNER_ID]
                if DEVELOPER_USER_ID not in admin_ids:
                    admin_ids.append(DEVELOPER_USER_ID)

                for admin_id in admin_ids:
                    try:
                        await client.send_message(
                            chat_id=admin_id,
                            text=admin_text,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=refund_button
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to notify admin {admin_id}: {str(e)}")

            except Exception as e:
                logger.error(f"❌ Payment processing failed for user {user_id if user_id else 'unknown'}: {str(e)}")
                if chat_id:
                    await client.send_message(
                        chat_id=chat_id,
                        text=PAYMENT_FAILED_TEXT,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Support", user_id=DEVELOPER_USER_ID)]])
                    )

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
            filters=filters.regex(r'^(gift_\d+|increment_gift_\d+|decrement_gift_\d+|show_donate_options|refund_.+)$')
        ),
        group=2
    )
    app.add_handler(
        RawUpdateHandler(raw_update_handler),
        group=3
    )

