from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.logger import logger
from config.settings import Settings
from database.firebase_db import firebase_db
from utils.file_handler import FileManager

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Create or update user in database
    try:
        user_data = firebase_db.create_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        logger.info(f"User {user.id} ({user.username}) started the bot")
    except Exception as e:
        logger.error(f"Error saving user to database: {e}")
        user_data = None
    
    total_ops = user_data.total_operations if user_data else 0
    member_since = user_data.created_at.strftime('%Y-%m-%d') if user_data else 'Today'
    
    welcome_message = f"""
👋 **Welcome {user.first_name}!**

I'm your **PDF Assistant Bot**. I can help you with:

📄 **Merge PDFs** - Combine multiple PDF files into one
🖼️ **Images to PDF** - Convert images to PDF format  
🔄 **Convert PDF** - Convert PDF to images, DOCX, or TXT

━━━━━━━━━━━━━━━━━━━━
🚀 **Quick Start:**
Choose an operation from the menu below to get started!

📊 **Your Stats:**
• Total operations: {total_ops}
• Member since: {member_since}

Let's get started! 🎉
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
            InlineKeyboardButton("📚 How to Use", callback_data="show_help"),
            InlineKeyboardButton("📊 My Statistics", callback_data="view_stats")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    
    help_message = f"""
📚 **How to Use This Bot**

━━━━━━━━━━━━━━━━━━━━
**🔹 Merge PDFs:**
1️⃣ Send me 2 or more PDF files
2️⃣ Use /merge to combine them
3️⃣ Use /list to see uploaded files
4️⃣ Use /clear to start over

━━━━━━━━━━━━━━━━━━━━
**🔹 Images to PDF:**
1️⃣ Use /img2pdf command
2️⃣ Send me images (JPG, PNG, etc.)
3️⃣ Optionally rotate or reorder images
4️⃣ Click "Create PDF" button
5️⃣ Download your PDF

━━━━━━━━━━━━━━━━━━━━
**🔹 PDF Converter:**
1️⃣ Use /convert command
2️⃣ Upload your PDF file
3️⃣ Choose: Images, Word (DOCX), or Text (TXT)
4️⃣ Configure settings (pages, quality)
5️⃣ Download your converted files

━━━━━━━━━━━━━━━━━━━━
**⚙️ Commands:**
/start - Start the bot
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

━━━━━━━━━━━━━━━━━━━━
Need help? Contact support 💬
"""
    
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - Show user statistics"""
    user = update.effective_user
    
    try:
        # Get user from database
        user_data = firebase_db.get_user(user.id)
        
        if user_data:
            # Get user's recent operations
            recent_ops = firebase_db.get_user_operations(user.id, limit=5)
            
            stats_message = f"""
📊 **Your Statistics**

━━━━━━━━━━━━━━━━━━━━
👤 **User Info:**
• User ID: `{user_data.user_id}`
• Username: @{user_data.username or 'N/A'}
• Member since: {user_data.created_at.strftime('%Y-%m-%d')}
• Last active: {user_data.last_active.strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━━━
📈 **Usage:**
• Total operations: **{user_data.total_operations}**
• Recent operations: **{len(recent_ops)}**

━━━━━━━━━━━━━━━━━━━━
🎯 **Account Status:**
• Status: {'⭐ Premium' if user_data.is_premium else '🆓 Free'}
• Blocked: {'❌ Yes' if user_data.is_blocked else '✅ No'}
"""
            
            if recent_ops:
                stats_message += "\n━━━━━━━━━━━━━━━━━━━━\n📝 **Recent Operations:**\n"
                for i, op in enumerate(recent_ops[:5], 1):
                    status_emoji = "✅" if op.status == "completed" else "❌" if op.status == "failed" else "⏳"
                    stats_message += f"{i}. {status_emoji} {op.operation_type} - {op.created_at.strftime('%m/%d %H:%M')}\n"
            
            await update.message.reply_text(stats_message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ User data not found. Please use /start first.")
            
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        await update.message.reply_text("❌ Error retrieving statistics. Please try again later.")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    user_id = update.effective_user.id
    
    try:
        # Clear user session from database
        firebase_db.clear_session(user_id)
        
        # Clear user data from context
        context.user_data.clear()
        
        # Clean up user files
        FileManager.cleanup_user_files(user_id)
        
        logger.info(f"User {user_id} cancelled operation")
        
        await update.message.reply_text(
            "❌ **Operation Cancelled**\n\n"
            "All files have been cleared.\n"
            "Use /start to begin again.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in cancel command: {e}")
        await update.message.reply_text("❌ Error cancelling operation.")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command - Clear current session"""
    user_id = update.effective_user.id
    
    try:
        # Clear session
        firebase_db.clear_session(user_id)
        context.user_data.clear()
        FileManager.cleanup_user_files(user_id)
        
        await update.message.reply_text(
            "🗑️ **Session Cleared**\n\n"
            "All uploaded files have been removed.\n"
            "You can start a new operation now.",
            parse_mode='Markdown'
        )
        logger.info(f"Cleared session for user: {user_id}")
        
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        await update.message.reply_text("❌ Error clearing session.")

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adminstats command - Show bot statistics (Admin only)"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in Settings.ADMIN_USER_IDS:
        await update.message.reply_text("❌ This command is only available to administrators.")
        return
    
    try:
        stats = firebase_db.get_statistics()
        
        admin_message = f"""
🔧 **Bot Statistics** (Admin)

━━━━━━━━━━━━━━━━━━━━
👥 **Users:**
• Total users: **{stats.get('total_users', 0)}**

━━━━━━━━━━━━━━━━━━━━
📊 **Operations:**
• Total operations: **{stats.get('total_operations', 0)}**

**By Type:**
• Merge PDF: {stats.get('operations_by_type', {}).get('merge_pdf', 0)}
• Image to PDF: {stats.get('operations_by_type', {}).get('image_to_pdf', 0)}

**By Status:**
• ✅ Completed: {stats.get('operations_by_status', {}).get('completed', 0)}
• ❌ Failed: {stats.get('operations_by_status', {}).get('failed', 0)}

━━━━━━━━━━━━━━━━━━━━
"""
        
        await update.message.reply_text(admin_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await update.message.reply_text("❌ Error retrieving statistics.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ **An Error Occurred**\n\n"
                "Something went wrong while processing your request.\n"
                "Please try again or use /cancel to start over.\n\n"
                "If the problem persists, contact support.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")
