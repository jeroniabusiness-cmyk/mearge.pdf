import os
from typing import List, Optional, Tuple
from PIL import Image
import img2pdf
from utils.logger import logger
from utils.file_handler import FileManager

class ImageOperations:
    """Handle image operations and PDF conversion"""
    
    # Page sizes in points (1 inch = 72 points)
    PAGE_SIZES = {
        'A4': (595.28, 841.89),      # 210 x 297 mm
        'Letter': (612, 792),         # 8.5 x 11 inches
        'Legal': (612, 1008),         # 8.5 x 14 inches
        'A3': (841.89, 1190.55),     # 297 x 420 mm
        'A5': (419.53, 595.28),      # 148 x 210 mm
    }
    
    @staticmethod
    def validate_image(file_path: str) -> Tuple[bool, str]:
        """
        Validate if file is a valid image
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Try to open image
            with Image.open(file_path) as img:
                # Verify image
                img.verify()
                
            # Re-open for actual processing (verify closes the file)
            with Image.open(file_path) as img:
                # Check if image has content
                if img.size[0] == 0 or img.size[1] == 0:
                    return False, "Image has zero dimensions"
                
                logger.info(f"Valid image: {os.path.basename(file_path)} - {img.format} {img.size} {img.mode}")
                
            return True, "Valid image"
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False, f"Invalid image: {str(e)}"
    
    @staticmethod
    def get_image_info(file_path: str) -> dict:
        """
        Get information about an image
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary with image information
        """
        try:
            with Image.open(file_path) as img:
                info = {
                    'file_name': os.path.basename(file_path),
                    'file_size': FileManager.get_file_size(file_path),
                    'format': img.format,
                    'mode': img.mode,
                    'width': img.size[0],
                    'height': img.size[1],
                    'aspect_ratio': img.size[0] / img.size[1],
                    'orientation': 'Portrait' if img.size[1] > img.size[0] else 'Landscape'
                }
                
                # Get DPI if available
                if 'dpi' in img.info:
                    info['dpi'] = img.info['dpi']
                else:
                    info['dpi'] = (72, 72)  # Default DPI
                
                return info
                
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {
                'file_name': os.path.basename(file_path),
                'file_size': FileManager.get_file_size(file_path),
                'error': str(e)
            }
    
    @staticmethod
    def rotate_image(file_path: str, angle: int) -> Tuple[bool, str]:
        """
        Rotate image by specified angle
        
        Args:
            file_path: Path to image file
            angle: Rotation angle (90, 180, 270)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if angle not in [90, 180, 270]:
                return False, "Invalid rotation angle. Use 90, 180, or 270"
            
            with Image.open(file_path) as img:
                # Rotate image (negative for clockwise)
                rotated = img.rotate(-angle, expand=True)
                
                # Save rotated image
                rotated.save(file_path)
                
            logger.info(f"Rotated image {os.path.basename(file_path)} by {angle}°")
            return True, f"Rotated {angle}°"
            
        except Exception as e:
            logger.error(f"Error rotating image: {e}")
            return False, f"Error rotating image: {str(e)}"
    
    @staticmethod
    def resize_image_to_fit(file_path: str, max_width: int, max_height: int) -> Tuple[bool, str]:
        """
        Resize image to fit within max dimensions while maintaining aspect ratio
        
        Args:
            file_path: Path to image file
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with Image.open(file_path) as img:
                # Calculate new size maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                img.save(file_path, quality=95)
                
            logger.info(f"Resized image {os.path.basename(file_path)} to fit {max_width}x{max_height}")
            return True, "Image resized"
            
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return False, f"Error resizing image: {str(e)}"
    
    @staticmethod
    def convert_to_rgb(file_path: str) -> Tuple[bool, str]:
        """
        Convert image to RGB mode (required for PDF conversion)
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if not already
                if img.mode != 'RGB':
                    rgb_img = img.convert('RGB')
                    rgb_img.save(file_path)
                    logger.info(f"Converted {os.path.basename(file_path)} from {img.mode} to RGB")
                    return True, f"Converted from {img.mode} to RGB"
                else:
                    return True, "Already in RGB mode"
                    
        except Exception as e:
            logger.error(f"Error converting to RGB: {e}")
            return False, f"Error converting to RGB: {str(e)}"
    
    @staticmethod
    def create_pdf_from_images(
        image_paths: List[str], 
        output_path: str,
        page_size: str = 'A4',
        fit_to_page: bool = True
    ) -> Tuple[bool, str, int]:
        """
        Create PDF from multiple images
        
        Args:
            image_paths: List of image file paths
            output_path: Output PDF file path
            page_size: Page size (A4, Letter, etc.)
            fit_to_page: Whether to fit images to page size
            
        Returns:
            Tuple of (success: bool, message: str, file_size: int)
        """
        try:
            if not image_paths:
                return False, "No images provided", 0
            
            logger.info(f"Creating PDF from {len(image_paths)} images")
            
            # Validate all images first
            for img_path in image_paths:
                is_valid, msg = ImageOperations.validate_image(img_path)
                if not is_valid:
                    return False, f"Invalid image {os.path.basename(img_path)}: {msg}", 0
            
            # Convert all images to RGB
            for img_path in image_paths:
                ImageOperations.convert_to_rgb(img_path)
            
            # Get page size
            if page_size in ImageOperations.PAGE_SIZES:
                layout_fun = img2pdf.get_layout_fun(ImageOperations.PAGE_SIZES[page_size])
            else:
                layout_fun = img2pdf.get_layout_fun(ImageOperations.PAGE_SIZES['A4'])
            
            # Create PDF
            with open(output_path, "wb") as f:
                if fit_to_page:
                    # Fit images to page size
                    f.write(img2pdf.convert(image_paths, layout_fun=layout_fun))
                else:
                    # Use original image sizes
                    f.write(img2pdf.convert(image_paths))
            
            output_size = FileManager.get_file_size(output_path)
            
            logger.info(f"✅ Created PDF with {len(image_paths)} images. Size: {output_size} bytes")
            return True, f"✅ Created PDF with {len(image_paths)} images", output_size
            
        except Exception as e:
            logger.error(f"Error creating PDF from images: {e}")
            return False, f"❌ Error creating PDF: {str(e)}", 0
    
    @staticmethod
    def create_thumbnail(file_path: str, output_path: str, size: Tuple[int, int] = (200, 200)) -> Tuple[bool, str]:
        """
        Create thumbnail of image
        
        Args:
            file_path: Path to original image
            output_path: Path to save thumbnail
            size: Thumbnail size (width, height)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with Image.open(file_path) as img:
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(output_path, quality=85)
                
            logger.info(f"Created thumbnail for {os.path.basename(file_path)}")
            return True, "Thumbnail created"
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return False, f"Error creating thumbnail: {str(e)}"
    
    @staticmethod
    def get_optimal_page_size(image_paths: List[str]) -> str:
        """
        Determine optimal page size based on image orientations
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Recommended page size name
        """
        try:
            portrait_count = 0
            landscape_count = 0
            
            for img_path in image_paths:
                info = ImageOperations.get_image_info(img_path)
                if info.get('orientation') == 'Portrait':
                    portrait_count += 1
                else:
                    landscape_count += 1
            
            # Return most common orientation's default size
            if portrait_count > landscape_count:
                return 'A4'  # Portrait
            else:
                return 'Letter'  # Landscape-friendly
                
        except Exception as e:
            logger.error(f"Error determining optimal page size: {e}")
            return 'A4'  # Default
