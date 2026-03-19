from keep_alive import keep_alive
keep_alive()

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from config.settings import Settings
from utils.logger import logger
from utils.file_handler import FileManager
from database.firebase_config import FirebaseConfig

# Import handlers
from handlers.basic_handlers import (
    start_command,
    help_command,
    stats_command,
    cancel_command,
    clear_command,
    admin_stats_command,
    error_handler
)
from handlers.pdf_merge_handler import (
    handle_pdf_document,
    list_pdfs_callback,
    merge_pdfs_callback,
    clear_session_callback,
    cancel_operation_callback,
    start_new_merge_callback,
    view_stats_callback,
    main_menu_callback,
    back_to_main_callback,
    show_help_callback
)
from handlers.pdf_commands import (
    merge_command,
    list_command
)
from handlers.image_to_pdf_handler import (
    start_img2pdf_command,
    handle_image_upload,
    list_images_callback,
    show_pdf_options_callback as img_show_pdf_options,
    select_page_size_callback,
    set_page_size_callback,
    toggle_fit_to_page_callback,
    select_rotate_image_callback,
    rotate_image_callback,
    apply_rotation_callback,
    select_remove_image_callback,
    remove_image_callback,
    create_pdf_from_images_callback,
    clear_img_session_callback,
    cancel_img2pdf_callback,
    start_new_img2pdf_callback,
    back_to_img_upload_callback,
    cancel_img2pdf_command,
    WAITING_FOR_IMAGES,
    SELECTING_OPTIONS as IMG_SELECTING_OPTIONS
)
from handlers.pdf_convert_handler import (
    start_convert_command,
    handle_convert_pdf_upload,
    convert_to_images_callback,
    toggle_image_format_callback,
    select_image_quality_callback,
    set_quality_callback,
    select_image_dpi_callback,
    set_dpi_callback,
    select_pages_images_callback,
    set_pages_callback,
    handle_page_range_text,
    execute_convert_images_callback,
    convert_to_docx_callback,
    convert_to_txt_callback,
    back_to_format_select_callback,
    cancel_convert_callback,
    start_new_convert_callback,
    cancel_convert_command,
    WAITING_FOR_PDF,
    SELECTING_FORMAT,
    SELECTING_PAGES,
    SELECTING_OPTIONS as CONV_SELECTING_OPTIONS
)
from telegram import Update

def main():
    """Start the bot"""
    logger.info("=" * 60)
    logger.info("    TELEGRAM PDF BOT - STARTING    ")
    logger.info("=" * 60)
    
    # Initialize Firebase
    try:
        FirebaseConfig.initialize()
        logger.info("✅ Firebase initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {e}")
        return
    
    # Create application
    logger.info("Creating Telegram application...")
    application = Application.builder().token(Settings.BOT_TOKEN).build()
    
    # Create conversation handler for Image to PDF
    img2pdf_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("img2pdf", start_img2pdf_command),
            CallbackQueryHandler(start_new_img2pdf_callback, pattern="^start_new_img2pdf$")
        ],
        states={
            WAITING_FOR_IMAGES: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image_upload),
                CallbackQueryHandler(list_images_callback, pattern="^list_images$"),
                CallbackQueryHandler(img_show_pdf_options, pattern="^show_pdf_options$"),
                CallbackQueryHandler(select_rotate_image_callback, pattern="^select_rotate_image$"),
                CallbackQueryHandler(rotate_image_callback, pattern="^rotate_image_\\d+$"),
                CallbackQueryHandler(apply_rotation_callback, pattern="^apply_rotation_\\d+_\\d+$"),
                CallbackQueryHandler(select_remove_image_callback, pattern="^select_remove_image$"),
                CallbackQueryHandler(remove_image_callback, pattern="^remove_image_\\d+$"),
                CallbackQueryHandler(create_pdf_from_images_callback, pattern="^create_pdf_from_images$"),
                CallbackQueryHandler(clear_img_session_callback, pattern="^clear_img_session$"),
                CallbackQueryHandler(cancel_img2pdf_callback, pattern="^cancel_img2pdf$"),
                CallbackQueryHandler(back_to_img_upload_callback, pattern="^back_to_img_upload$"),
            ],
            IMG_SELECTING_OPTIONS: [
                CallbackQueryHandler(select_page_size_callback, pattern="^select_page_size$"),
                CallbackQueryHandler(set_page_size_callback, pattern="^set_page_size_"),
                CallbackQueryHandler(toggle_fit_to_page_callback, pattern="^toggle_fit_to_page$"),
                CallbackQueryHandler(img_show_pdf_options, pattern="^show_pdf_options$"),
                CallbackQueryHandler(list_images_callback, pattern="^list_images$"),
                CallbackQueryHandler(create_pdf_from_images_callback, pattern="^create_pdf_from_images$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_img2pdf_command),
            CallbackQueryHandler(cancel_img2pdf_callback, pattern="^cancel_img2pdf$")
        ],
        name="img2pdf_conversation",
        persistent=False
    )
    
    # Create conversation handler for PDF Conversion
    pdf_convert_handler = ConversationHandler(
        entry_points=[
            CommandHandler("convert", start_convert_command),
            CallbackQueryHandler(start_new_convert_callback, pattern="^start_new_convert$")
        ],
        states={
            WAITING_FOR_PDF: [MessageHandler(filters.Document.PDF, handle_convert_pdf_upload)],
            SELECTING_FORMAT: [
                CallbackQueryHandler(convert_to_images_callback, pattern="^convert_to_images$"),
                CallbackQueryHandler(convert_to_docx_callback, pattern="^convert_to_docx$"),
                CallbackQueryHandler(convert_to_txt_callback, pattern="^convert_to_txt$"),
                CallbackQueryHandler(cancel_convert_callback, pattern="^cancel_convert$"),
            ],
            SELECTING_PAGES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_page_range_text),
                CallbackQueryHandler(set_pages_callback, pattern="^set_pages_"),
                CallbackQueryHandler(convert_to_images_callback, pattern="^convert_to_images$"), # Back button
            ],
            CONV_SELECTING_OPTIONS: [
                CallbackQueryHandler(toggle_image_format_callback, pattern="^toggle_image_format$"),
                CallbackQueryHandler(select_image_quality_callback, pattern="^select_image_quality$"),
                CallbackQueryHandler(set_quality_callback, pattern="^set_quality_"),
                CallbackQueryHandler(select_image_dpi_callback, pattern="^select_image_dpi$"),
                CallbackQueryHandler(set_dpi_callback, pattern="^set_dpi_"),
                CallbackQueryHandler(select_pages_images_callback, pattern="^select_pages_images$"),
                CallbackQueryHandler(execute_convert_images_callback, pattern="^execute_convert_images$"),
                CallbackQueryHandler(back_to_format_select_callback, pattern="^back_to_format_select$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_convert_command),
            CallbackQueryHandler(cancel_convert_callback, pattern="^cancel_convert$")
        ],
        name="pdf_convert_conversation",
        persistent=False
    )
    
    # Add conversation handlers
    application.add_handler(img2pdf_conv_handler)
    application.add_handler(pdf_convert_handler)
    
    # Add command handlers
    logger.info("Registering command handlers...")
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("merge", merge_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("adminstats", admin_stats_command))
    
    # Add document handler for PDFs (for Merge feature)
    logger.info("Registering document handlers...")
    application.add_handler(
        MessageHandler(
            filters.Document.PDF & ~filters.COMMAND,
            handle_pdf_document
        )
    )
    
    # Add callback query handlers
    logger.info("Registering callback handlers...")
    application.add_handler(CallbackQueryHandler(list_pdfs_callback, pattern="^list_pdfs$"))
    application.add_handler(CallbackQueryHandler(merge_pdfs_callback, pattern="^merge_pdfs$"))
    application.add_handler(CallbackQueryHandler(clear_session_callback, pattern="^clear_session$"))
    application.add_handler(CallbackQueryHandler(cancel_operation_callback, pattern="^cancel_operation$"))
    application.add_handler(CallbackQueryHandler(start_new_merge_callback, pattern="^start_new_merge$"))
    application.add_handler(CallbackQueryHandler(view_stats_callback, pattern="^view_stats$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(back_to_main_callback, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(show_help_callback, pattern="^show_help$"))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Clean up old files on startup
    logger.info("Cleaning up old files...")
    FileManager.cleanup_old_files(hours=24)
    
    # Start bot
    logger.info("=" * 60)
    logger.info("✅ Bot is running and ready to accept requests!")
    logger.info("=" * 60)
    logger.info(f"📊 Configuration:")
    logger.info(f"   • Max file size: {Settings.MAX_FILE_SIZE_MB}MB")
    logger.info(f"   • Session timeout: {Settings.SESSION_TIMEOUT_MINUTES} minutes")
    logger.info(f"   • Max files per session: {Settings.MAX_FILES_PER_SESSION}")
    logger.info(f"   • Temp folder: {Settings.TEMP_FOLDER}")
    logger.info("=" * 60)
    logger.info("📋 Available Features:")
    logger.info("   • PDF Merging ✅")
    logger.info("   • Image to PDF ✅")
    logger.info("   • PDF to Images ✅")
    logger.info("   • PDF to Word (DOCX) ✅")
    logger.info("   • PDF to Text (TXT) ✅")
    logger.info("=" * 60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Bot stopped by user (Ctrl+C)")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
