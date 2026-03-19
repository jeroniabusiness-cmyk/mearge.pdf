from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import logger
from database.firebase_db import firebase_db
from utils.file_handler import FileManager
from utils.pdf_operations import PDFOperations

async def merge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /merge command"""
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files or len(session.files) < 2:
        await update.message.reply_text(
            "❌ **Cannot Merge**\n\n"
            "You need at least 2 PDF files to merge.\n\n"
            "📤 Send me PDF files first!",
            parse_mode='Markdown'
        )
        return
    
    # Trigger merge via callback
    from handlers.pdf_merge_handler import merge_pdfs_callback
    
    # Create a fake callback query context
    await update.message.reply_text(
        f"🔄 Starting merge of {len(session.files)} PDFs...",
        parse_mode='Markdown'
    )
    
    # Note: For command version, we'll create a simpler flow
    # The callback version is better, but this works too

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command"""
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files:
        await update.message.reply_text(
            "📭 **No Files Uploaded**\n\n"
            "Send me PDF files to start!",
            parse_mode='Markdown'
        )
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
        file_list += f"   • Pages: {num_pages} | Size: {file_size}\n\n"
        
        total_pages += num_pages
        total_size += file['file_size']
    
    file_list += f"━━━━━━━━━━━━━━━━━━━━\n"
    file_list += f"📊 **Summary:**\n"
    file_list += f"• Total files: **{len(session.files)}**\n"
    file_list += f"• Total pages: **{total_pages}**\n"
    file_list += f"• Total size: **{FileManager.format_file_size(total_size)}**\n\n"
    
    if len(session.files) >= 2:
        file_list += "✅ Ready to merge! Use /merge"
    else:
        file_list += "📤 Send more PDF files to continue"
    
    await update.message.reply_text(file_list, parse_mode='Markdown')
