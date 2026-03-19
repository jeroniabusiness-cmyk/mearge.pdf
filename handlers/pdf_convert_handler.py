from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.logger import logger
from utils.file_handler import FileManager
from utils.validators import FileValidator
from utils.pdf_converter import PDFConverter
from utils.pdf_operations import PDFOperations
from database.firebase_db import firebase_db
from database.models import OperationType, OperationStatus
from config.settings import Settings
import os

# Conversation states
WAITING_FOR_PDF = 1
SELECTING_FORMAT = 2
SELECTING_PAGES = 3
SELECTING_OPTIONS = 4

async def start_convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start PDF conversion"""
    user = update.effective_user
    user_id = user.id
    
    # Update user in database
    firebase_db.create_or_update_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Clear any existing session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    welcome_msg = """
🔄 **PDF Converter**

📤 **Send me a PDF file** to convert it to other formats.

━━━━━━━━━━━━━━━━━━━━
✅ **Available Conversions:**

📸 **PDF to Images**
• Convert pages to JPG or PNG
• Select specific pages or all
• Choose quality (Low/Medium/High)
• Get ZIP file with all images

📝 **PDF to DOCX**
• Convert to Microsoft Word format
• Preserve formatting
• Select specific pages

📃 **PDF to TXT**
• Extract all text
• Plain text format
• Preserves layout (optional)

━━━━━━━━━━━━━━━━━━━━
🎯 **How to use:**
1️⃣ Send your PDF file
2️⃣ Choose conversion format
3️⃣ Select pages (optional)
4️⃣ Download converted file(s)

**Send your PDF file now!** 📄
"""
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_convert")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)
    logger.info(f"User {user_id} started PDF conversion")
    
    return WAITING_FOR_PDF

async def handle_convert_pdf_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF upload for conversion"""
    user_id = update.effective_user.id
    document = update.message.document
    
    # Validate PDF
    is_valid, validation_message = FileValidator.validate_pdf(
        document.file_name,
        document.file_size
    )
    
    if not is_valid:
        await update.message.reply_text(validation_message)
        return WAITING_FOR_PDF
    
    try:
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Processing PDF...")
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_data = await file.download_as_bytearray()
        
        # Save file
        saved_path = FileManager.save_file(
            user_id=user_id,
            file_data=bytes(file_data),
            extension='.pdf',
            prefix='convert'
        )
        
        # Validate PDF
        is_valid_pdf, pdf_validation_msg = PDFOperations.validate_pdf(saved_path)
        if not is_valid_pdf:
            os.remove(saved_path)
            await processing_msg.edit_text(f"❌ {pdf_validation_msg}")
            return WAITING_FOR_PDF
        
        # Get PDF info
        pdf_info = PDFOperations.get_pdf_info(saved_path)
        page_count = pdf_info['num_pages']
        
        # Store in context
        context.user_data['pdf_path'] = saved_path
        context.user_data['pdf_filename'] = document.file_name
        context.user_data['pdf_pages'] = page_count
        context.user_data['pdf_size'] = document.file_size
        
        # Get text preview
        text_preview = PDFConverter.get_pdf_text_preview(saved_path, 200)
        has_text = len(text_preview.strip()) > 10 and text_preview != "No text found"
        
        # Success message
        success_message = f"""
✅ **PDF Uploaded Successfully!**

📄 **File:** `{document.file_name}`
📊 **Pages:** {page_count}
💾 **Size:** {FileManager.format_file_size(document.file_size)}
📝 **Text content:** {'✅ Detected' if has_text else '❌ None (scanned image?)'}

━━━━━━━━━━━━━━━━━━━━
🔄 **Choose conversion format:**
"""
        
        # Create keyboard with conversion options
        keyboard = [
            [InlineKeyboardButton("📸 PDF → Images (JPG/PNG)", callback_data="convert_to_images")],
        ]
        
        # Only show text conversion if text is detected
        if has_text:
            keyboard.append([InlineKeyboardButton("📝 PDF → DOCX (Word)", callback_data="convert_to_docx")])
            keyboard.append([InlineKeyboardButton("📃 PDF → TXT (Text)", callback_data="convert_to_txt")])
        else:
            success_message += "\n⚠️ **Note:** No text detected. Only image conversion available."
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_convert")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(success_message, parse_mode='Markdown', reply_markup=reply_markup)
        
        logger.info(f"User {user_id} uploaded PDF for conversion: {page_count} pages")
        
        return SELECTING_FORMAT
        
    except Exception as e:
        logger.error(f"Error handling PDF upload: {e}")
        await update.message.reply_text(
            "❌ **Error Processing PDF**\n\n"
            "An error occurred while processing your file.\n"
            "Please try again or use /cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_PDF

async def convert_to_images_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start PDF to images conversion"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['conversion_type'] = 'images'
    context.user_data['image_format'] = 'jpg'  # Default
    context.user_data['image_dpi'] = 'medium'  # Default
    context.user_data['image_quality'] = 'medium'  # Default
    context.user_data['page_range'] = 'all'  # Default
    
    page_count = context.user_data.get('pdf_pages', 0)
    
    msg = f"""
📸 **PDF to Images Conversion**

📄 **Your PDF:** {page_count} pages

━━━━━━━━━━━━━━━━━━━━
⚙️ **Current Settings:**
• Format: **JPG**
• Quality: **Medium**
• DPI: **300**
• Pages: **All pages**

━━━━━━━━━━━━━━━━━━━━
💡 **Configure your conversion:**
"""
    
    keyboard = [
        [InlineKeyboardButton("📏 Select Pages", callback_data="select_pages_images")],
        [InlineKeyboardButton("🖼️ Format: JPG", callback_data="toggle_image_format")],
        [InlineKeyboardButton("⚙️ Quality: Medium", callback_data="select_image_quality")],
        [InlineKeyboardButton("📊 DPI: Medium (300)", callback_data="select_image_dpi")],
        [
            InlineKeyboardButton("✅ Convert Now", callback_data="execute_convert_images"),
            InlineKeyboardButton("« Back", callback_data="back_to_format_select")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return SELECTING_OPTIONS

async def toggle_image_format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle between JPG and PNG"""
    query = update.callback_query
    
    current_format = context.user_data.get('image_format', 'jpg')
    new_format = 'png' if current_format == 'jpg' else 'jpg'
    context.user_data['image_format'] = new_format
    
    await query.answer(f"Format changed to {new_format.upper()}")
    
    # Refresh the options screen
    return await convert_to_images_callback(update, context)

async def select_image_quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select image quality"""
    query = update.callback_query
    await query.answer()
    
    current_quality = context.user_data.get('image_quality', 'medium')
    
    msg = f"""
⚙️ **Select Image Quality**

Current: **{current_quality.title()}**

Higher quality = Larger file size
"""
    
    keyboard = [
        [InlineKeyboardButton(
            f"{'✅' if current_quality == 'low' else '☐'} Low (60%)",
            callback_data="set_quality_low"
        )],
        [InlineKeyboardButton(
            f"{'✅' if current_quality == 'medium' else '☐'} Medium (85%)",
            callback_data="set_quality_medium"
        )],
        [InlineKeyboardButton(
            f"{'✅' if current_quality == 'high' else '☐'} High (95%)",
            callback_data="set_quality_high"
        )],
        [InlineKeyboardButton("« Back", callback_data="convert_to_images")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return SELECTING_OPTIONS

async def set_quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set image quality"""
    query = update.callback_query
    
    quality = query.data.replace('set_quality_', '')
    context.user_data['image_quality'] = quality
    
    await query.answer(f"Quality set to {quality.title()}")
    
    return await convert_to_images_callback(update, context)

async def select_image_dpi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select image DPI"""
    query = update.callback_query
    await query.answer()
    
    current_dpi = context.user_data.get('image_dpi', 'medium')
    
    msg = f"""
📊 **Select DPI (Resolution)**

Current: **{current_dpi.title()}**

Higher DPI = Better quality but larger size
"""
    
    keyboard = [
        [InlineKeyboardButton(
            f"{'✅' if current_dpi == 'low' else '☐'} Low (150 DPI)",
            callback_data="set_dpi_low"
        )],
        [InlineKeyboardButton(
            f"{'✅' if current_dpi == 'medium' else '☐'} Medium (300 DPI)",
            callback_data="set_dpi_medium"
        )],
        [InlineKeyboardButton(
            f"{'✅' if current_dpi == 'high' else '☐'} High (600 DPI)",
            callback_data="set_dpi_high"
        )],
        [InlineKeyboardButton("« Back", callback_data="convert_to_images")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return SELECTING_OPTIONS

async def set_dpi_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set DPI"""
    query = update.callback_query
    
    dpi = query.data.replace('set_dpi_', '')
    context.user_data['image_dpi'] = dpi
    
    await query.answer(f"DPI set to {dpi.title()}")
    
    return await convert_to_images_callback(update, context)

async def select_pages_images_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select pages to convert to images"""
    query = update.callback_query
    await query.answer()
    
    page_count = context.user_data.get('pdf_pages', 0)
    current_range = context.user_data.get('page_range', 'all')
    
    msg = f"""
📏 **Select Pages to Convert**

**Total pages:** {page_count}
**Current selection:** {current_range}

━━━━━━━━━━━━━━━━━━━━
**Examples:**
• `all` - All pages
• `1-5` - Pages 1 to 5
• `1,3,5` - Specific pages
• `1-3,7,9-12` - Mixed range

━━━━━━━━━━━━━━━━━━━━
**Send page range or use buttons:**
"""
    
    keyboard = [
        [InlineKeyboardButton("📄 All Pages", callback_data="set_pages_all")],
        [InlineKeyboardButton("1️⃣ First Page Only", callback_data="set_pages_first")],
        [InlineKeyboardButton("🔢 First 5 Pages", callback_data="set_pages_first5")],
        [InlineKeyboardButton("« Back", callback_data="convert_to_images")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return SELECTING_PAGES

async def set_pages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set page range"""
    query = update.callback_query
    
    selection = query.data.replace('set_pages_', '')
    
    if selection == 'all':
        context.user_data['page_range'] = 'all'
        await query.answer("All pages selected")
    elif selection == 'first':
        context.user_data['page_range'] = '1'
        await query.answer("First page selected")
    elif selection == 'first5':
        context.user_data['page_range'] = '1-5'
        await query.answer("First 5 pages selected")
    
    return await convert_to_images_callback(update, context)

async def handle_page_range_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual page range input"""
    user_id = update.effective_user.id
    page_range = update.message.text.strip()
    
    # Validate page range
    page_count = context.user_data.get('pdf_pages', 0)
    
    try:
        parsed_pages = PDFConverter.parse_page_range(page_range, page_count)
        if parsed_pages:
            context.user_data['page_range'] = page_range
            await update.message.reply_text(
                f"✅ Page range set: {page_range}\n"
                f"({len(parsed_pages)} pages will be converted)"
            )
        else:
            await update.message.reply_text("❌ Invalid page range. Please try again.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error parsing page range: {str(e)}")
    
    return SELECTING_PAGES

async def execute_convert_images_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute PDF to images conversion"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pdf_path = context.user_data.get('pdf_path')
    
    if not pdf_path or not os.path.exists(pdf_path):
        await query.edit_message_text("❌ PDF file not found. Please upload again.")
        return ConversationHandler.END
    
    try:
        # Get settings
        image_format = context.user_data.get('image_format', 'jpg')
        image_dpi = context.user_data.get('image_dpi', 'medium')
        image_quality = context.user_data.get('image_quality', 'medium')
        page_range = context.user_data.get('page_range', 'all')
        
        # Show processing message
        await query.edit_message_text(
            "⏳ **Converting PDF to Images...**\n\n"
            "This may take a moment depending on file size.\n"
            "Please wait...",
            parse_mode='Markdown'
        )
        
        # Create operation record
        operation = firebase_db.create_operation(
            user_id=user_id,
            operation_type=OperationType.PDF_TO_IMAGE.value,
            file_count=1,
            input_size_bytes=context.user_data.get('pdf_size', 0)
        )
        
        firebase_db.update_operation_status(operation.operation_id, OperationStatus.IN_PROGRESS.value)
        
        # Create output folder
        output_folder = FileManager.get_user_folder(user_id)
        
        # Convert PDF to images
        success, message, image_paths = PDFConverter.pdf_to_images(
            pdf_path=pdf_path,
            output_folder=output_folder,
            page_range=page_range,
            dpi=image_dpi,
            image_format=image_format,
            quality=image_quality
        )
        
        if not success or not image_paths:
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=message
            )
            
            await query.edit_message_text(
                f"❌ **Conversion Failed**\n\n{message}",
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Create ZIP if multiple images
        if len(image_paths) > 1:
            zip_filename = FileManager.generate_unique_filename('.zip', prefix='pdf_images')
            zip_path = os.path.join(output_folder, zip_filename)
            
            zip_success, zip_msg, zip_size = PDFConverter.create_zip_from_images(image_paths, zip_path)
            
            if not zip_success:
                await query.edit_message_text(f"❌ Error creating ZIP: {zip_msg}")
                return ConversationHandler.END
            
            # Update operation
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.COMPLETED.value,
                output_size_bytes=zip_size
            )
            firebase_db.increment_user_operations(user_id)
            
            # Send success message
            success_msg = f"""
✅ **Conversion Complete!**

━━━━━━━━━━━━━━━━━━━━
📊 **Summary:**
• Images created: **{len(image_paths)}**
• Format: **{image_format.upper()}**
• Quality: **{image_quality.title()}**
• DPI: **{image_dpi.title()}**
• ZIP size: **{FileManager.format_file_size(zip_size)}**

⬇️ Sending ZIP file...
"""
            
            await query.edit_message_text(success_msg, parse_mode='Markdown')
            
            # Send ZIP file
            with open(zip_path, 'rb') as zip_file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=zip_file,
                    filename=f"pdf_images_{len(image_paths)}_pages.zip",
                    caption=f"📸 {len(image_paths)} images from PDF • 💾 {FileManager.format_file_size(zip_size)}"
                )
        else:
            # Single image - send directly
            image_path = image_paths[0]
            image_size = FileManager.get_file_size(image_path)
            
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.COMPLETED.value,
                output_size_bytes=image_size
            )
            firebase_db.increment_user_operations(user_id)
            
            with open(image_path, 'rb') as img_file:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=img_file,
                    filename=os.path.basename(image_path),
                    caption=f"📸 Page 1 • {FileManager.format_file_size(image_size)}"
                )
        
        # Clean up
        FileManager.cleanup_user_files(user_id)
        context.user_data.clear()
        
        # Final options
        keyboard = [
            [InlineKeyboardButton("🔄 Convert Another PDF", callback_data="start_new_convert")],
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
        
        logger.info(f"Successfully converted PDF to {len(image_paths)} images for user {user_id}")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in convert to images: {e}")
        
        if 'operation' in locals():
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=str(e)
            )
        
        await query.edit_message_text(
            "❌ **Conversion Error**\n\n"
            "An unexpected error occurred.\n"
            "Please try again or contact support.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def convert_to_docx_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert PDF to DOCX"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pdf_path = context.user_data.get('pdf_path')
    page_count = context.user_data.get('pdf_pages', 0)
    
    try:
        await query.edit_message_text(
            "⏳ **Converting PDF to DOCX...**\n\n"
            f"Processing {page_count} pages...\n"
            "This may take a few minutes.",
            parse_mode='Markdown'
        )
        
        # Create operation
        operation = firebase_db.create_operation(
            user_id=user_id,
            operation_type=OperationType.PDF_TO_DOCX.value,
            file_count=1,
            input_size_bytes=context.user_data.get('pdf_size', 0)
        )
        
        firebase_db.update_operation_status(operation.operation_id, OperationStatus.IN_PROGRESS.value)
        
        # Generate output path
        output_filename = FileManager.generate_unique_filename('.docx', prefix='converted')
        output_path = os.path.join(FileManager.get_user_folder(user_id), output_filename)
        
        # Convert
        success, message, output_size = PDFConverter.pdf_to_docx(
            pdf_path=pdf_path,
            output_path=output_path,
            page_range='all'
        )
        
        if not success:
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=message
            )
            await query.edit_message_text(f"❌ {message}")
            return ConversationHandler.END
        
        # Update operation
        firebase_db.update_operation_status(
            operation.operation_id,
            OperationStatus.COMPLETED.value,
            output_size_bytes=output_size
        )
        firebase_db.increment_user_operations(user_id)
        
        # Send DOCX
        success_msg = f"""
✅ **Conversion Complete!**

📝 **PDF → DOCX**
• Pages: **{page_count}**
• Size: **{FileManager.format_file_size(output_size)}**

⬇️ Sending DOCX file...
"""
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        with open(output_path, 'rb') as docx_file:
            await context.bot.send_document(
                chat_id=user_id,
                document=docx_file,
                filename=f"converted_{context.user_data.get('pdf_filename', 'document')}.docx",
                caption=f"📝 DOCX • {FileManager.format_file_size(output_size)}"
            )
        
        # Clean up
        FileManager.cleanup_user_files(user_id)
        context.user_data.clear()
        
        # Final options
        keyboard = [
            [InlineKeyboardButton("🔄 Convert Another", callback_data="start_new_convert")],
            [InlineKeyboardButton("« Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="✨ **Conversion complete!**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error converting to DOCX: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END

async def convert_to_txt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert PDF to TXT"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    pdf_path = context.user_data.get('pdf_path')
    page_count = context.user_data.get('pdf_pages', 0)
    
    try:
        await query.edit_message_text(
            "⏳ **Extracting Text from PDF...**\n\n"
            f"Processing {page_count} pages...",
            parse_mode='Markdown'
        )
        
        # Create operation
        operation = firebase_db.create_operation(
            user_id=user_id,
            operation_type=OperationType.PDF_TO_TXT.value,
            file_count=1,
            input_size_bytes=context.user_data.get('pdf_size', 0)
        )
        
        firebase_db.update_operation_status(operation.operation_id, OperationStatus.IN_PROGRESS.value)
        
        # Generate output path
        output_filename = FileManager.generate_unique_filename('.txt', prefix='extracted_text')
        output_path = os.path.join(FileManager.get_user_folder(user_id), output_filename)
        
        # Convert
        success, message, output_size = PDFConverter.pdf_to_text(
            pdf_path=pdf_path,
            output_path=output_path,
            page_range='all',
            preserve_layout=True
        )
        
        if not success:
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=message
            )
            await query.edit_message_text(f"❌ {message}")
            return ConversationHandler.END
        
        # Update operation
        firebase_db.update_operation_status(
            operation.operation_id,
            OperationStatus.COMPLETED.value,
            output_size_bytes=output_size
        )
        firebase_db.increment_user_operations(user_id)
        
        # Send TXT
        success_msg = f"""
✅ **Text Extraction Complete!**

📃 **PDF → TXT**
• Pages: **{page_count}**
• Size: **{FileManager.format_file_size(output_size)}**

⬇️ Sending text file...
"""
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        with open(output_path, 'rb') as txt_file:
            await context.bot.send_document(
                chat_id=user_id,
                document=txt_file,
                filename=f"extracted_{context.user_data.get('pdf_filename', 'text')}.txt",
                caption=f"📃 Extracted Text • {FileManager.format_file_size(output_size)}"
            )
        
        # Clean up
        FileManager.cleanup_user_files(user_id)
        context.user_data.clear()
        
        # Final options
        keyboard = [
            [InlineKeyboardButton("🔄 Convert Another", callback_data="start_new_convert")],
            [InlineKeyboardButton("« Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="✨ **Extraction complete!**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error converting to TXT: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}")
        return ConversationHandler.END

async def back_to_format_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to format selection"""
    query = update.callback_query
    await query.answer()
    
    # Just re-trigger the PDF upload handler message
    page_count = context.user_data.get('pdf_pages', 0)
    pdf_filename = context.user_data.get('pdf_filename', 'document.pdf')
    pdf_size = context.user_data.get('pdf_size', 0)
    
    msg = f"""
✅ **PDF Ready for Conversion**

📄 **File:** `{pdf_filename}`
📊 **Pages:** {page_count}
💾 **Size:** {FileManager.format_file_size(pdf_size)}

━━━━━━━━━━━━━━━━━━━━
🔄 **Choose conversion format:**
"""
    
    keyboard = [
        [InlineKeyboardButton("📸 PDF → Images (JPG/PNG)", callback_data="convert_to_images")],
        [InlineKeyboardButton("📝 PDF → DOCX (Word)", callback_data="convert_to_docx")],
        [InlineKeyboardButton("📃 PDF → TXT (Text)", callback_data="convert_to_txt")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_convert")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    
    return SELECTING_FORMAT

async def cancel_convert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversion"""
    query = update.callback_query
    await query.answer("Conversion cancelled")
    
    user_id = update.effective_user.id
    
    # Clean up
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await query.edit_message_text(
        "❌ **Conversion Cancelled**\n\n"
        "All files cleared.\n"
        "Use /convert to start again.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def start_new_convert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start new conversion"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Clean up old files
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await query.edit_message_text(
        "🔄 **New Conversion Started**\n\n"
        "📤 Send me a PDF file to convert.\n\n"
        "Use /cancel to stop at any time.",
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_PDF

async def cancel_convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel via command"""
    user_id = update.effective_user.id
    
    # Clean up
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ **PDF Conversion Cancelled**\n\n"
        "All files cleared.\n"
        "Use /convert to start again.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END
