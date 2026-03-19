from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.logger import logger
from utils.file_handler import FileManager
from utils.validators import FileValidator
from utils.pdf_operations import PDFOperations
from database.firebase_db import firebase_db
from database.models import OperationType, OperationStatus
from config.settings import Settings
import os

# Conversation states
WAITING_FOR_PDF = 1

async def handle_pdf_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF document uploads"""
    user = update.effective_user
    user_id = user.id
    document = update.message.document
    
    # Update user in database
    firebase_db.create_or_update_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Validate file
    is_valid, validation_message = FileValidator.validate_pdf(
        document.file_name, 
        document.file_size
    )
    
    if not is_valid:
        await update.message.reply_text(validation_message)
        return
    
    # Initialize session if needed
    session = firebase_db.get_session(user_id)
    if not session:
        session = firebase_db.create_or_update_session(user_id, OperationType.MERGE_PDF.value)
    
    # Check file count limit
    current_files = session.files if session.files else []
    can_add, limit_message = FileValidator.validate_session_file_count(len(current_files))
    
    if not can_add:
        await update.message.reply_text(limit_message)
        return
    
    try:
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Downloading PDF...")
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()
        
        # Save file
        saved_path = FileManager.save_file(
            user_id=user_id,
            file_data=bytes(file_data),
            extension='.pdf',
            prefix='merge'
        )
        
        # Validate PDF
        is_valid_pdf, pdf_validation_msg = PDFOperations.validate_pdf(saved_path)
        if not is_valid_pdf:
            os.remove(saved_path)
            await processing_msg.edit_text(f"❌ {pdf_validation_msg}")
            return
        
        # Get PDF info
        pdf_info = PDFOperations.get_pdf_info(saved_path)
        
        # Add to session
        file_info = {
            'file_id': document.file_id,
            'file_name': document.file_name,
            'file_path': saved_path,
            'file_size': document.file_size,
            'num_pages': pdf_info['num_pages'],
            'added_at': logger.handlers[0].formatter.formatTime(logger.makeRecord('', 0, '', 0, '', (), None))
        }
        
        firebase_db.add_file_to_session(user_id, file_info)
        
        # Get updated session
        session = firebase_db.get_session(user_id)
        current_file_count = len(session.files)
        
        # Format file size
        size_str = FileManager.format_file_size(document.file_size)
        
        # Success message
        success_message = f"""
✅ **PDF Added Successfully!**

📄 **File:** `{document.file_name}`
📊 **Pages:** {pdf_info['num_pages']}
💾 **Size:** {size_str}

━━━━━━━━━━━━━━━━━━━━
📚 **Current Session:**
• Total files: **{current_file_count}**
• Ready to merge: {'✅ Yes' if current_file_count >= 2 else '❌ Need more files'}

{'**Send another PDF to add more files**' if current_file_count < 2 else '**Ready to merge! Use the buttons below:**'}
"""
        
        # Create keyboard
        keyboard = []
        
        if current_file_count >= 2:
            keyboard.append([
                InlineKeyboardButton("🔄 Merge PDFs", callback_data="merge_pdfs"),
                InlineKeyboardButton("📋 View List", callback_data="list_pdfs")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📋 View Files", callback_data="list_pdfs")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🗑️ Clear All", callback_data="clear_session"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(success_message, parse_mode='Markdown', reply_markup=reply_markup)
        
        logger.info(f"User {user_id} added PDF. Total files: {current_file_count}")
        
    except Exception as e:
        logger.error(f"Error handling PDF: {e}")
        await update.message.reply_text(
            "❌ **Error Processing PDF**\n\n"
            "An error occurred while processing your file.\n"
            "Please try again or use /cancel to start over.",
            parse_mode='Markdown'
        )

async def list_pdfs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of uploaded PDFs"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files:
        await query.edit_message_text("📭 No PDF files in current session.\n\nSend me a PDF file to start!")
        return
    
    # Build file list
    file_list = "📚 **Uploaded PDF Files:**\n\n"
    total_pages = 0
    total_size = 0
    
    for idx, file in enumerate(session.files, 1):
        file_name = file['file_name']
        num_pages = file['num_pages']
        file_size = FileManager.format_file_size(file['file_size'])
        
        file_list += f"{idx}. 📄 `{file_name}`\n"
        file_list += f"   • Pages: {num_pages}\n"
        file_list += f"   • Size: {file_size}\n\n"
        
        total_pages += num_pages
        total_size += file['file_size']
    
    file_list += f"━━━━━━━━━━━━━━━━━━━━\n"
    file_list += f"📊 **Total:**\n"
    file_list += f"• Files: **{len(session.files)}**\n"
    file_list += f"• Pages: **{total_pages}**\n"
    file_list += f"• Size: **{FileManager.format_file_size(total_size)}**\n\n"
    
    # Estimate merged size
    file_paths = [f['file_path'] for f in session.files]
    estimated_size = PDFOperations.estimate_merge_size(file_paths)
    file_list += f"📦 **Estimated merged size:** {FileManager.format_file_size(estimated_size)}"
    
    # Keyboard
    keyboard = []
    if len(session.files) >= 2:
        keyboard.append([InlineKeyboardButton("🔄 Merge Now", callback_data="merge_pdfs")])
    keyboard.append([
        InlineKeyboardButton("🗑️ Clear All", callback_data="clear_session"),
        InlineKeyboardButton("« Back", callback_data="back_to_main")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(file_list, parse_mode='Markdown', reply_markup=reply_markup)

async def merge_pdfs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Merge uploaded PDFs"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or len(session.files) < 2:
        await query.edit_message_text(
            "❌ Need at least 2 PDF files to merge.\n\nSend me PDF files first!",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Show processing message
        await query.edit_message_text(
            "⏳ **Merging PDFs...**\n\n"
            f"Processing {len(session.files)} files...\n"
            "This may take a moment.",
            parse_mode='Markdown'
        )
        
        # Create operation record
        total_input_size = sum(f['file_size'] for f in session.files)
        operation = firebase_db.create_operation(
            user_id=user_id,
            operation_type=OperationType.MERGE_PDF.value,
            file_count=len(session.files),
            input_size_bytes=total_input_size
        )
        
        # Update operation status
        firebase_db.update_operation_status(operation.operation_id, OperationStatus.IN_PROGRESS.value)
        
        # Get file paths
        file_paths = [f['file_path'] for f in session.files]
        
        # Generate output path
        output_filename = FileManager.generate_unique_filename('.pdf', prefix='merged')
        output_path = os.path.join(FileManager.get_user_folder(user_id), output_filename)
        
        # Merge PDFs
        success, message, output_size = PDFOperations.merge_pdfs(file_paths, output_path)
        
        if not success:
            # Update operation as failed
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=message
            )
            
            await query.edit_message_text(
                f"{message}\n\nPlease try again or contact support.",
                parse_mode='Markdown'
            )
            return
        
        # Get merged PDF info
        merged_info = PDFOperations.get_pdf_info(output_path)
        
        # Update operation as completed
        firebase_db.update_operation_status(
            operation.operation_id,
            OperationStatus.COMPLETED.value,
            output_size_bytes=output_size
        )
        
        # Increment user operations count
        firebase_db.increment_user_operations(user_id)
        
        # Send success message
        success_msg = f"""
✅ **PDFs Merged Successfully!**

━━━━━━━━━━━━━━━━━━━━
📊 **Merge Summary:**
• Input files: **{len(session.files)}**
• Total input size: **{FileManager.format_file_size(total_input_size)}**

📄 **Output:**
• Total pages: **{merged_info['num_pages']}**
• File size: **{FileManager.format_file_size(output_size)}**
• Compression: **{((1 - output_size/total_input_size) * 100):.1f}%**

⬇️ Sending merged PDF...
"""
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Send merged PDF
        with open(output_path, 'rb') as pdf_file:
            await context.bot.send_document(
                chat_id=user_id,
                document=pdf_file,
                filename=f"merged_{len(session.files)}_files.pdf",
                caption=f"🔄 Merged PDF\n📄 {merged_info['num_pages']} pages • 💾 {FileManager.format_file_size(output_size)}"
            )
        
        # Clean up
        firebase_db.clear_session(user_id)
        FileManager.cleanup_user_files(user_id)
        
        # Final message with options
        keyboard = [
            [InlineKeyboardButton("🔄 Merge More PDFs", callback_data="start_new_merge")],
            [InlineKeyboardButton("📊 View Stats", callback_data="view_stats")],
            [InlineKeyboardButton("« Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="✨ **What would you like to do next?**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Successfully merged {len(session.files)} PDFs for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in merge callback: {e}")
        
        # Update operation as failed
        if 'operation' in locals():
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=str(e)
            )
        
        await query.edit_message_text(
            "❌ **Error During Merge**\n\n"
            "An unexpected error occurred.\n"
            "Please try again or use /cancel to start over.",
            parse_mode='Markdown'
        )

async def clear_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear current session"""
    query = update.callback_query
    await query.answer("Clearing session...")
    
    user_id = update.effective_user.id
    
    # Clear session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    
    await query.edit_message_text(
        "🗑️ **Session Cleared**\n\n"
        "All files have been removed.\n"
        "Send me PDF files to start a new merge!",
        parse_mode='Markdown'
    )
    
    logger.info(f"Cleared session for user {user_id}")

async def cancel_operation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    query = update.callback_query
    await query.answer("Operation cancelled")
    
    user_id = update.effective_user.id
    
    # Clear session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await query.edit_message_text(
        "❌ **Operation Cancelled**\n\n"
        "All files cleared.\n"
        "Use /start to begin again.",
        parse_mode='Markdown'
    )

async def start_new_merge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new merge operation"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Clear old session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    
    # Create new session
    firebase_db.create_or_update_session(user_id, OperationType.MERGE_PDF.value)
    
    await query.edit_message_text(
        "🔄 **New Merge Operation Started**\n\n"
        "📤 Send me 2 or more PDF files to merge them together.\n\n"
        "Use /cancel to stop at any time.",
        parse_mode='Markdown'
    )

async def view_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user statistics"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = firebase_db.get_user(user_id)
    
    if not user_data:
        await query.edit_message_text("❌ User data not found.")
        return
    
    # Get recent operations
    recent_ops = firebase_db.get_user_operations(user_id, limit=5)
    
    stats_msg = f"""
📊 **Your Statistics**

━━━━━━━━━━━━━━━━━━━━
👤 **User Info:**
• Total operations: **{user_data.total_operations}**
• Member since: {user_data.created_at.strftime('%Y-%m-%d')}
• Last active: {user_data.last_active.strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━
"""
    
    if recent_ops:
        stats_msg += "📝 **Recent Operations:**\n"
        for i, op in enumerate(recent_ops[:5], 1):
            status_emoji = "✅" if op.status == "completed" else "❌" if op.status == "failed" else "⏳"
            op_type = op.operation_type.replace('_', ' ').title()
            stats_msg += f"{i}. {status_emoji} {op_type} - {op.created_at.strftime('%m/%d %H:%M')}\n"
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_msg, parse_mode='Markdown', reply_markup=reply_markup)

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    query = update.callback_query
    await query.answer()
    
    menu_text = """
🤖 **PDF Assistant Bot - Main Menu**

Choose an operation to get started:

📄 **Merge PDFs** - Combine multiple PDF files into one
🖼️ **Images to PDF** - Convert images to PDF format  
🔄 **Convert PDF** - Convert PDF to images, DOCX, or TXT

━━━━━━━━━━━━━━━━━━━━
💡 **Quick Actions:**
Use /help for detailed instructions
Use /stats to view your statistics
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📄 Merge PDFs", callback_data="start_new_merge"),
            InlineKeyboardButton("🖼️ Images to PDF", callback_data="start_new_img2pdf")
        ],
        [
            InlineKeyboardButton("🔄 Convert PDF", callback_data="start_new_convert"),
        ],
        [
            InlineKeyboardButton("📊 My Statistics", callback_data="view_stats"),
            InlineKeyboardButton("ℹ️ Help", callback_data="show_help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(menu_text, parse_mode='Markdown', reply_markup=reply_markup)

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu preserving session"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if session and session.files:
        file_count = len(session.files)
        text = f"""
📚 **Current Session Active**

You have **{file_count}** PDF file(s) ready.

Send more PDFs or use the buttons below:
"""
        keyboard = []
        if file_count >= 2:
            keyboard.append([InlineKeyboardButton("🔄 Merge PDFs", callback_data="merge_pdfs")])
        keyboard.append([
            InlineKeyboardButton("📋 View List", callback_data="list_pdfs"),
            InlineKeyboardButton("🗑️ Clear", callback_data="clear_session")
        ])
    else:
        text = "📤 Send me PDF files to start merging!"
        keyboard = [[InlineKeyboardButton("« Main Menu", callback_data="main_menu")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def show_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    query = update.callback_query
    await query.answer()
    
    help_text = f"""
📚 **How to Use This Bot**

━━━━━━━━━━━━━━━━━━━━
**🔹 Merge PDFs:**
1️⃣ Select "Merge PDFs" from the menu
2️⃣ Send me 2 or more PDF files
3️⃣ Click "Merge PDFs" button
4️⃣ Use /clear or click "Clear" to start over

━━━━━━━━━━━━━━━━━━━━
**🔹 Images to PDF:**
1️⃣ Select "Images to PDF" from the menu
2️⃣ Send me images (JPG, PNG, etc.)
3️⃣ Arrange or rotate them with options
4️⃣ Click "Create PDF" button

━━━━━━━━━━━━━━━━━━━━
**🔹 PDF Converter:**
1️⃣ Select "Convert PDF" from the menu
2️⃣ Send your PDF file
3️⃣ Choose: Images, Word (DOCX), or Text (TXT)
4️⃣ Download your converted files

━━━━━━━━━━━━━━━━━━━━
**⚙️ Commands:**
/start - Start the bot & Main Menu
/help - Show this help message
/img2pdf - Convert images to PDF
/convert - PDF to Image/DOCX/TXT
/merge - Merge uploaded PDFs
/list - Show file list
/clear - Clear session
/stats - Your statistics
/cancel - Cancel operation

━━━━━━━━━━━━━━━━━━━━
**📋 Limits:**
• Max file size: **{Settings.MAX_FILE_SIZE_MB}MB**
• Max files per session: **{Settings.MAX_FILES_PER_SESSION}**
• Session timeout: **{Settings.SESSION_TIMEOUT_MINUTES} minutes**
"""
    
    keyboard = [[InlineKeyboardButton("« Back", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
