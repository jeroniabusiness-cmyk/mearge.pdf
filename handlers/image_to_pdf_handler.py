from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.logger import logger
from utils.file_handler import FileManager
from utils.validators import FileValidator
from utils.image_operations import ImageOperations
from database.firebase_db import firebase_db
from database.models import OperationType, OperationStatus
from config.settings import Settings
import os

# Conversation states
WAITING_FOR_IMAGES = 1
SELECTING_OPTIONS = 2

async def start_img2pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start image to PDF conversion"""
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
    
    # Create new session
    firebase_db.create_or_update_session(user_id, OperationType.IMAGE_TO_PDF.value)
    
    welcome_msg = """
🖼️ **Image to PDF Converter**

📤 **Send me images** to convert them to a PDF file.

━━━━━━━━━━━━━━━━━━━━
✅ **Supported formats:**
• JPG, JPEG
• PNG
• WEBP
• BMP
• TIFF

━━━━━━━━━━━━━━━━━━━━
📋 **Features:**
• Combine multiple images
• Reorder images
• Rotate images (90°, 180°, 270°)
• Choose page size (A4, Letter, etc.)
• High-quality output

━━━━━━━━━━━━━━━━━━━━
🎯 **How to use:**
1️⃣ Send your images (one by one)
2️⃣ Arrange them as needed
3️⃣ Click "Create PDF"
4️⃣ Download your PDF!

**Send your first image now!** 📸
"""
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_img2pdf")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=reply_markup)
    logger.info(f"User {user_id} started image to PDF conversion")
    
    return WAITING_FOR_IMAGES

async def handle_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image uploads"""
    user_id = update.effective_user.id
    
    # Check if photo or document
    if update.message.photo:
        # Get highest resolution photo
        photo = update.message.photo[-1]
        file_id = photo.file_id
        file_size = photo.file_size
        file_name = f"image_{photo.file_unique_id}.jpg"
    elif update.message.document:
        document = update.message.document
        file_id = document.file_id
        file_size = document.file_size
        file_name = document.file_name
        
        # Validate image document
        is_valid, validation_message = FileValidator.validate_image(file_name, file_size)
        if not is_valid:
            await update.message.reply_text(validation_message)
            return WAITING_FOR_IMAGES
    else:
        await update.message.reply_text("❌ Please send an image file.")
        return WAITING_FOR_IMAGES
    
    # Get session
    session = firebase_db.get_session(user_id)
    if not session:
        session = firebase_db.create_or_update_session(user_id, OperationType.IMAGE_TO_PDF.value)
    
    # Check file count limit
    current_files = session.files if session.files else []
    can_add, limit_message = FileValidator.validate_session_file_count(len(current_files))
    
    if not can_add:
        await update.message.reply_text(limit_message)
        return WAITING_FOR_IMAGES
    
    try:
        # Show processing message
        processing_msg = await update.message.reply_text("⏳ Processing image...")
        
        # Download file
        file = await context.bot.get_file(file_id)
        file_data = await file.download_as_bytearray()
        
        # Save file
        file_ext = os.path.splitext(file_name)[1] or '.jpg'
        saved_path = FileManager.save_file(
            user_id=user_id,
            file_data=bytes(file_data),
            extension=file_ext,
            prefix='img2pdf'
        )
        
        # Validate image
        is_valid_image, img_validation_msg = ImageOperations.validate_image(saved_path)
        if not is_valid_image:
            os.remove(saved_path)
            await processing_msg.edit_text(f"❌ {img_validation_msg}")
            return WAITING_FOR_IMAGES
        
        # Get image info
        img_info = ImageOperations.get_image_info(saved_path)
        
        # Add to session
        file_info = {
            'file_id': file_id,
            'file_name': file_name,
            'file_path': saved_path,
            'file_size': file_size,
            'width': img_info.get('width', 0),
            'height': img_info.get('height', 0),
            'format': img_info.get('format', 'Unknown'),
            'orientation': img_info.get('orientation', 'Unknown'),
            'rotation': 0  # Track rotation
        }
        
        firebase_db.add_file_to_session(user_id, file_info)
        
        # Get updated session
        session = firebase_db.get_session(user_id)
        current_file_count = len(session.files)
        
        # Format file size
        size_str = FileManager.format_file_size(file_size)
        
        # Success message
        success_message = f"""
✅ **Image Added Successfully!**

🖼️ **File:** `{file_name}`
📐 **Size:** {img_info.get('width')}x{img_info.get('height')} px
📊 **Format:** {img_info.get('format')}
🔄 **Orientation:** {img_info.get('orientation')}
💾 **File size:** {size_str}

━━━━━━━━━━━━━━━━━━━━
📚 **Current images:** {current_file_count}/{Settings.MAX_FILES_PER_SESSION}

{'**Send more images or create PDF:**' if current_file_count >= 1 else '**Send more images:**'}
"""
        
        # Create keyboard
        keyboard = []
        
        if current_file_count >= 1:
            keyboard.append([
                InlineKeyboardButton("📄 Create PDF", callback_data="create_pdf_from_images"),
                InlineKeyboardButton("📋 View Images", callback_data="list_images")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🗑️ Clear All", callback_data="clear_img_session"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_img2pdf")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(success_message, parse_mode='Markdown', reply_markup=reply_markup)
        
        logger.info(f"User {user_id} added image. Total images: {current_file_count}")
        
        return WAITING_FOR_IMAGES
        
    except Exception as e:
        logger.error(f"Error handling image: {e}")
        await update.message.reply_text(
            "❌ **Error Processing Image**\n\n"
            "An error occurred while processing your image.\n"
            "Please try again or use /cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_IMAGES

async def list_images_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of uploaded images"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files:
        await query.edit_message_text("📭 No images uploaded.\n\nSend me images to start!")
        return WAITING_FOR_IMAGES
    
    # Build image list
    image_list = "🖼️ **Uploaded Images:**\n\n"
    total_size = 0
    
    for idx, file in enumerate(session.files, 1):
        file_name = file['file_name']
        width = file.get('width', 0)
        height = file.get('height', 0)
        orientation = file.get('orientation', 'Unknown')
        file_size = FileManager.format_file_size(file['file_size'])
        rotation = file.get('rotation', 0)
        
        rotation_icon = ""
        if rotation == 90:
            rotation_icon = "↻"
        elif rotation == 180:
            rotation_icon = "↻↻"
        elif rotation == 270:
            rotation_icon = "↺"
        
        image_list += f"{idx}. 📸 `{file_name}` {rotation_icon}\n"
        image_list += f"   • Size: {width}x{height} px\n"
        image_list += f"   • Orientation: {orientation}\n"
        image_list += f"   • File size: {file_size}\n\n"
        
        total_size += file['file_size']
    
    image_list += f"━━━━━━━━━━━━━━━━━━━━\n"
    image_list += f"📊 **Total:**\n"
    image_list += f"• Images: **{len(session.files)}**\n"
    image_list += f"• Total size: **{FileManager.format_file_size(total_size)}**\n"
    
    # Keyboard with options
    keyboard = [
        [
            InlineKeyboardButton("📄 Create PDF", callback_data="create_pdf_from_images"),
            InlineKeyboardButton("⚙️ Options", callback_data="show_pdf_options")
        ],
        [
            InlineKeyboardButton("🔄 Rotate Image", callback_data="select_rotate_image"),
            InlineKeyboardButton("🗑️ Remove Image", callback_data="select_remove_image")
        ],
        [
            InlineKeyboardButton("🗑️ Clear All", callback_data="clear_img_session"),
            InlineKeyboardButton("« Back", callback_data="back_to_img_upload")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(image_list, parse_mode='Markdown', reply_markup=reply_markup)
    return WAITING_FOR_IMAGES

async def show_pdf_options_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show PDF creation options"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    # Get current settings from context or use defaults
    page_size = context.user_data.get('page_size', 'A4')
    fit_to_page = context.user_data.get('fit_to_page', True)
    
    options_msg = f"""
⚙️ **PDF Creation Options**

━━━━━━━━━━━━━━━━━━━━
📄 **Current Settings:**

**Page Size:** {page_size}
**Fit to Page:** {'✅ Yes' if fit_to_page else '❌ No'}

━━━━━━━━━━━━━━━━━━━━
💡 **Choose your preferences:**
"""
    
    keyboard = [
        [InlineKeyboardButton("📏 Change Page Size", callback_data="select_page_size")],
        [InlineKeyboardButton(
            f"{'✅' if fit_to_page else '☐'} Fit Images to Page", 
            callback_data="toggle_fit_to_page"
        )],
        [
            InlineKeyboardButton("📄 Create PDF", callback_data="create_pdf_from_images"),
            InlineKeyboardButton("« Back", callback_data="list_images")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(options_msg, parse_mode='Markdown', reply_markup=reply_markup)
    return SELECTING_OPTIONS

async def select_page_size_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show page size selection"""
    query = update.callback_query
    await query.answer()
    
    current_size = context.user_data.get('page_size', 'A4')
    
    msg = f"""
📏 **Select Page Size**

Current: **{current_size}**

Choose the page size for your PDF:
"""
    
    keyboard = []
    for size_name, dimensions in ImageOperations.PAGE_SIZES.items():
        icon = "✅" if size_name == current_size else "☐"
        keyboard.append([InlineKeyboardButton(
            f"{icon} {size_name} ({int(dimensions[0]/72)}x{int(dimensions[1]/72)} in)",
            callback_data=f"set_page_size_{size_name}"
        )])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="show_pdf_options")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return SELECTING_OPTIONS

async def set_page_size_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set page size"""
    query = update.callback_query
    
    # Extract page size from callback data
    page_size = query.data.replace('set_page_size_', '')
    
    # Save to user data
    context.user_data['page_size'] = page_size
    
    await query.answer(f"Page size set to {page_size}")
    
    # Return to options
    return await show_pdf_options_callback(update, context)

async def toggle_fit_to_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle fit to page option"""
    query = update.callback_query
    
    # Toggle setting
    current = context.user_data.get('fit_to_page', True)
    context.user_data['fit_to_page'] = not current
    
    await query.answer(f"Fit to page: {'ON' if not current else 'OFF'}")
    
    # Return to options
    return await show_pdf_options_callback(update, context)

async def select_rotate_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select image to rotate"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files:
        await query.edit_message_text("❌ No images to rotate.")
        return WAITING_FOR_IMAGES
    
    msg = "🔄 **Select image to rotate:**\n\n"
    
    keyboard = []
    for idx, file in enumerate(session.files):
        rotation = file.get('rotation', 0)
        rotation_icon = ""
        if rotation == 90:
            rotation_icon = " ↻"
        elif rotation == 180:
            rotation_icon = " ↻↻"
        elif rotation == 270:
            rotation_icon = " ↺"
        
        keyboard.append([InlineKeyboardButton(
            f"{idx + 1}. {file['file_name']}{rotation_icon}",
            callback_data=f"rotate_image_{idx}"
        )])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="list_images")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return WAITING_FOR_IMAGES

async def rotate_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rotate selected image"""
    query = update.callback_query
    
    # Extract image index
    image_idx = int(query.data.replace('rotate_image_', ''))
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or image_idx >= len(session.files):
        await query.answer("❌ Image not found")
        return WAITING_FOR_IMAGES
    
    # Show rotation options
    msg = f"🔄 **Rotate image {image_idx + 1}**\n\nSelect rotation angle:"
    
    keyboard = [
        [InlineKeyboardButton("↻ 90° Clockwise", callback_data=f"apply_rotation_{image_idx}_90")],
        [InlineKeyboardButton("↻↻ 180°", callback_data=f"apply_rotation_{image_idx}_180")],
        [InlineKeyboardButton("↺ 270° (90° Counter)", callback_data=f"apply_rotation_{image_idx}_270")],
        [InlineKeyboardButton("« Back", callback_data="select_rotate_image")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return WAITING_FOR_IMAGES

async def apply_rotation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apply rotation to image"""
    query = update.callback_query
    await query.answer("Rotating image...")
    
    # Parse callback data: apply_rotation_INDEX_ANGLE
    parts = query.data.split('_')
    image_idx = int(parts[2])
    angle = int(parts[3])
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or image_idx >= len(session.files):
        await query.answer("❌ Image not found")
        return WAITING_FOR_IMAGES
    
    try:
        # Get image file
        image_file = session.files[image_idx]
        file_path = image_file['file_path']
        
        # Rotate image
        success, msg = ImageOperations.rotate_image(file_path, angle)
        
        if success:
            # Update rotation tracking
            current_rotation = image_file.get('rotation', 0)
            new_rotation = (current_rotation + angle) % 360
            
            # Update session
            session.files[image_idx]['rotation'] = new_rotation
            
            # Update in Firebase
            session_ref = firebase_db.sessions_collection.document(str(user_id))
            session_ref.update({'files': session.files})
            
            await query.answer(f"✅ Rotated {angle}°")
            
            # Return to image list
            return await list_images_callback(update, context)
        else:
            await query.answer(f"❌ {msg}")
            return WAITING_FOR_IMAGES
            
    except Exception as e:
        logger.error(f"Error rotating image: {e}")
        await query.answer("❌ Error rotating image")
        return WAITING_FOR_IMAGES

async def select_remove_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select image to remove"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files:
        await query.edit_message_text("❌ No images to remove.")
        return WAITING_FOR_IMAGES
    
    msg = "🗑️ **Select image to remove:**\n\n"
    
    keyboard = []
    for idx, file in enumerate(session.files):
        keyboard.append([InlineKeyboardButton(
            f"{idx + 1}. {file['file_name']}",
            callback_data=f"remove_image_{idx}"
        )])
    
    keyboard.append([InlineKeyboardButton("« Back", callback_data="list_images")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    return WAITING_FOR_IMAGES

async def remove_image_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove selected image"""
    query = update.callback_query
    
    # Extract image index
    image_idx = int(query.data.replace('remove_image_', ''))
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or image_idx >= len(session.files):
        await query.answer("❌ Image not found")
        return WAITING_FOR_IMAGES
    
    try:
        # Get image file
        image_file = session.files[image_idx]
        file_name = image_file['file_name']
        file_path = image_file['file_path']
        
        # Remove file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from session
        session.files.pop(image_idx)
        
        # Update in Firebase
        session_ref = firebase_db.sessions_collection.document(str(user_id))
        session_ref.update({'files': session.files})
        
        await query.answer(f"✅ Removed {file_name}")
        
        # Return to list or upload screen
        if session.files:
            return await list_images_callback(update, context)
        else:
            await query.edit_message_text(
                "🗑️ All images removed.\n\nSend me images to start again!",
                parse_mode='Markdown'
            )
            return WAITING_FOR_IMAGES
            
    except Exception as e:
        logger.error(f"Error removing image: {e}")
        await query.answer("❌ Error removing image")
        return WAITING_FOR_IMAGES

async def create_pdf_from_images_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create PDF from uploaded images"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if not session or not session.files:
        await query.edit_message_text(
            "❌ No images uploaded.\n\nSend me images first!",
            parse_mode='Markdown'
        )
        return WAITING_FOR_IMAGES
    
    try:
        # Show processing message
        await query.edit_message_text(
            "⏳ **Creating PDF...**\n\n"
            f"Processing {len(session.files)} images...\n"
            "This may take a moment.",
            parse_mode='Markdown'
        )
        
        # Create operation record
        total_input_size = sum(f['file_size'] for f in session.files)
        operation = firebase_db.create_operation(
            user_id=user_id,
            operation_type=OperationType.IMAGE_TO_PDF.value,
            file_count=len(session.files),
            input_size_bytes=total_input_size
        )
        
        # Update operation status
        firebase_db.update_operation_status(operation.operation_id, OperationStatus.IN_PROGRESS.value)
        
        # Get settings
        page_size = context.user_data.get('page_size', 'A4')
        fit_to_page = context.user_data.get('fit_to_page', True)
        
        # Get file paths
        image_paths = [f['file_path'] for f in session.files]
        
        # Generate output path
        output_filename = FileManager.generate_unique_filename('.pdf', prefix='images_to_pdf')
        output_path = os.path.join(FileManager.get_user_folder(user_id), output_filename)
        
        # Create PDF
        success, message, output_size = ImageOperations.create_pdf_from_images(
            image_paths=image_paths,
            output_path=output_path,
            page_size=page_size,
            fit_to_page=fit_to_page
        )
        
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
            return WAITING_FOR_IMAGES
        
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
✅ **PDF Created Successfully!**

━━━━━━━━━━━━━━━━━━━━
📊 **Conversion Summary:**
• Images used: **{len(session.files)}**
• Page size: **{page_size}**
• Fit to page: **{'Yes' if fit_to_page else 'No'}**
• Total input size: **{FileManager.format_file_size(total_input_size)}**

📄 **Output:**
• Pages: **{len(session.files)}**
• File size: **{FileManager.format_file_size(output_size)}**

⬇️ Sending PDF...
"""
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Send PDF
        with open(output_path, 'rb') as pdf_file:
            await context.bot.send_document(
                chat_id=user_id,
                document=pdf_file,
                filename=f"images_to_pdf_{len(session.files)}_pages.pdf",
                caption=f"📄 PDF from {len(session.files)} images • 💾 {FileManager.format_file_size(output_size)}"
            )
        
        # Clean up
        firebase_db.clear_session(user_id)
        FileManager.cleanup_user_files(user_id)
        context.user_data.clear()
        
        # Final message with options
        keyboard = [
            [InlineKeyboardButton("🖼️ Convert More Images", callback_data="start_new_img2pdf")],
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
        
        logger.info(f"Successfully created PDF from {len(session.files)} images for user {user_id}")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in create PDF callback: {e}")
        
        # Update operation as failed
        if 'operation' in locals():
            firebase_db.update_operation_status(
                operation.operation_id,
                OperationStatus.FAILED.value,
                error_message=str(e)
            )
        
        await query.edit_message_text(
            "❌ **Error Creating PDF**\n\n"
            "An unexpected error occurred.\n"
            "Please try again or use /cancel.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_IMAGES

async def clear_img_session_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear image session"""
    query = update.callback_query
    await query.answer("Clearing session...")
    
    user_id = update.effective_user.id
    
    # Clear session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await query.edit_message_text(
        "🗑️ **Session Cleared**\n\n"
        "All images have been removed.\n"
        "Send me images to start again!",
        parse_mode='Markdown'
    )
    
    logger.info(f"Cleared image session for user {user_id}")
    return WAITING_FOR_IMAGES

async def cancel_img2pdf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel image to PDF operation"""
    query = update.callback_query
    await query.answer("Operation cancelled")
    
    user_id = update.effective_user.id
    
    # Clear session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await query.edit_message_text(
        "❌ **Operation Cancelled**\n\n"
        "All images cleared.\n"
        "Use /img2pdf to start again.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END

async def start_new_img2pdf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start new image to PDF conversion"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Clear old session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    # Create new session
    firebase_db.create_or_update_session(user_id, OperationType.IMAGE_TO_PDF.value)
    
    await query.edit_message_text(
        "🖼️ **New Image to PDF Conversion Started**\n\n"
        "📤 Send me images to convert them to PDF.\n\n"
        "Use /cancel to stop at any time.",
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_IMAGES

async def back_to_img_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to image upload screen"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = firebase_db.get_session(user_id)
    
    if session and session.files:
        file_count = len(session.files)
        text = f"""
🖼️ **Current Session Active**

You have **{file_count}** image(s) ready.

Send more images or use the buttons below:
"""
        keyboard = [
            [
                InlineKeyboardButton("📄 Create PDF", callback_data="create_pdf_from_images"),
                InlineKeyboardButton("📋 View Images", callback_data="list_images")
            ],
            [
                InlineKeyboardButton("🗑️ Clear", callback_data="clear_img_session"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_img2pdf")
            ]
        ]
    else:
        text = "📤 Send me images to start!"
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_img2pdf")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    return WAITING_FOR_IMAGES

async def cancel_img2pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel via command"""
    user_id = update.effective_user.id
    
    # Clear session
    firebase_db.clear_session(user_id)
    FileManager.cleanup_user_files(user_id)
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ **Image to PDF Cancelled**\n\n"
        "All images cleared.\n"
        "Use /img2pdf to start again.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END
