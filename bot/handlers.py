import os
import tempfile
import backoff
import asyncio 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services import gsheet_service, ai_service, drive_service
from database import session
from core.logger import logger

@backoff.on_exception(backoff.expo, Exception, max_tries=3)
def get_config_with_retry():
    return gsheet_service.get_system_settings()

def build_main_panel(txn_id, ai_result):
    text = (f"🧾 **Receipt Recognized Successfully**\n\n"
            f"🏢 Vendor: {ai_result.get('Vendor')} (SSM: {ai_result.get('Company_Reg_No', '-')})\n"
            f"📄 Invoice No: {ai_result.get('Invoice_No', '-')}\n"
            f"💰 Total: RM {ai_result.get('Amount')} (Tax: RM {ai_result.get('Tax_Amount', '0.00')})\n"
            f"🏷️ Category: {ai_result.get('Category')}\n"
            f"💳 Payment: {ai_result.get('Payment_Method')}\n\n"
            f"Please verify the information, or click the buttons below to edit.")
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Submit", callback_data=f"yes|{txn_id}")],
        [InlineKeyboardButton("✏️ Edit Category", callback_data=f"edit_cat|{txn_id}"),
         InlineKeyboardButton("✏️ Edit Payment", callback_data=f"edit_pay|{txn_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"no|{txn_id}")]
    ]
    return text, InlineKeyboardMarkup(keyboard)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    active_users, categories, payments = get_config_with_retry()
    
    if user_id not in active_users:
        await update.message.reply_text(f"⛔️ Unauthorized access.")
        return

    msg = await update.message.reply_text("⚙️ Receipt received! AI is analyzing, please wait...")
    photo_file = await update.message.photo[-1].get_file()
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
        local_path = temp_img.name
        
    try:
        await photo_file.download_to_drive(local_path)
        
        # Async Defense: Push AI task to a background thread
        ai_result = await asyncio.to_thread(
            ai_service.extract_receipt_info, local_path, categories, payments
        )
        
        txn_id = session.save_pending(user_id, ai_result, local_path)
        
        text, reply_markup = build_main_panel(txn_id, ai_result)
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Processing Failed: {e}", exc_info=True)
        await msg.edit_text("❌ Processing failed. Please check the clarity of the receipt.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("|")
    action = parts[0]
    txn_id = parts[1]
    
    if action == "yes":
        await query.edit_message_text(text="⏳ Uploading to Google Drive and submitting...")
        data = session.get_and_complete_pending(txn_id)
        
        if data:
            try:
                final_txn_id = gsheet_service.generate_txn_id(data["user_id"])
                
                drive_link = await asyncio.to_thread(
                    drive_service.upload_to_drive, data["local_path"], f"{final_txn_id}.jpg"
                )
                
                await asyncio.to_thread(
                    gsheet_service.append_transaction, data["ai_data"], drive_link, data["user_id"], final_txn_id
                )
                
                if os.path.exists(data["local_path"]): 
                    os.remove(data["local_path"])
                
                await query.edit_message_text(f"✅ Submitted successfully!\nTransaction ID: `{final_txn_id}`", parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Final Submission Failed: {e}")
                await query.edit_message_text(text="❌ Submission error. Please contact the administrator.")
                
    elif action == "no":
        data = session.get_and_complete_pending(txn_id)
        if data and os.path.exists(data["local_path"]): 
            os.remove(data["local_path"])
        await query.edit_message_text("❌ Entry cancelled.")
        
    elif action == "edit_cat":
        active_users, categories, payments = get_config_with_retry()
        keyboard = []
        for i, cat in enumerate(categories):
            keyboard.append([InlineKeyboardButton(cat, callback_data=f"set_cat|{txn_id}|{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"back|{txn_id}")])
        
        await query.edit_message_text("👇 Please select the correct category:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif action == "edit_pay":
        active_users, categories, payments = get_config_with_retry()
        keyboard = []
        for i, pay in enumerate(payments):
            keyboard.append([InlineKeyboardButton(pay, callback_data=f"set_pay|{txn_id}|{i}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"back|{txn_id}")])
        
        await query.edit_message_text("👇 Please select the correct payment method:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif action == "set_cat":
        idx = int(parts[2])
        active_users, categories, payments = get_config_with_retry()
        new_cat = categories[idx]
        
        pending_data = session.get_pending(txn_id)
        if pending_data:
            ai_data = pending_data["ai_data"]
            ai_data["Category"] = new_cat
            session.update_pending_data(txn_id, ai_data)
            
            text, markup = build_main_panel(txn_id, ai_data)
            await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
            
    elif action == "set_pay":
        idx = int(parts[2])
        active_users, categories, payments = get_config_with_retry()
        new_pay = payments[idx]
        
        pending_data = session.get_pending(txn_id)
        if pending_data:
            ai_data = pending_data["ai_data"]
            ai_data["Payment_Method"] = new_pay
            session.update_pending_data(txn_id, ai_data)
            
            text, markup = build_main_panel(txn_id, ai_data)
            await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')
            
    elif action == "back":
        pending_data = session.get_pending(txn_id)
        if pending_data:
            text, markup = build_main_panel(txn_id, pending_data["ai_data"])
            await query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')