import os
from typing import List, Tuple, Optional
from pypdf import PdfReader
import pdfplumber
from pdf2docx import Converter
from pdf2image import convert_from_path
from PIL import Image
from utils.logger import logger
from utils.file_handler import FileManager
import zipfile

class PDFConverter:
    """Handle PDF conversion to various formats"""
    
    # Image DPI options
    DPI_OPTIONS = {
        'low': 150,
        'medium': 300,
        'high': 600
    }
    
    # Image quality options
    QUALITY_OPTIONS = {
        'low': 60,
        'medium': 85,
        'high': 95
    }
    
    @staticmethod
    def get_pdf_page_count(pdf_path: str) -> int:
        """Get number of pages in PDF"""
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 0
    
    @staticmethod
    def parse_page_range(page_range: str, total_pages: int) -> List[int]:
        """
        Parse page range string to list of page numbers
        
        Args:
            page_range: String like "1-5", "1,3,5", "all"
            total_pages: Total number of pages in PDF
            
        Returns:
            List of page numbers (0-indexed)
        """
        try:
            if not page_range or page_range.lower() == 'all':
                return list(range(total_pages))
            
            pages = []
            parts = page_range.split(',')
            
            for part in parts:
                part = part.strip()
                
                if '-' in part:
                    # Range like "1-5"
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    
                    # Convert to 0-indexed
                    start = max(1, min(start, total_pages)) - 1
                    end = max(1, min(end, total_pages))
                    
                    pages.extend(range(start, end))
                else:
                    # Single page
                    page = int(part)
                    page = max(1, min(page, total_pages)) - 1
                    pages.append(page)
            
            # Remove duplicates and sort
            pages = sorted(list(set(pages)))
            return pages
            
        except Exception as e:
            logger.error(f"Error parsing page range: {e}")
            return list(range(total_pages))
    
    @staticmethod
    def pdf_to_images(
        pdf_path: str,
        output_folder: str,
        page_range: str = 'all',
        dpi: str = 'medium',
        image_format: str = 'jpg',
        quality: str = 'medium'
    ) -> Tuple[bool, str, List[str]]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_path: Path to PDF file
            output_folder: Folder to save images
            page_range: Page range to convert
            dpi: DPI quality (low/medium/high)
            image_format: Output format (jpg/png)
            quality: Image quality (low/medium/high)
            
        Returns:
            Tuple of (success, message, list of image paths)
        """
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            
            # Get total pages
            total_pages = PDFConverter.get_pdf_page_count(pdf_path)
            if total_pages == 0:
                return False, "PDF has no pages", []
            
            # Parse page range
            pages_to_convert = PDFConverter.parse_page_range(page_range, total_pages)
            if not pages_to_convert:
                return False, "No valid pages to convert", []
            
            # Get DPI
            dpi_value = PDFConverter.DPI_OPTIONS.get(dpi, 300)
            quality_value = PDFConverter.QUALITY_OPTIONS.get(quality, 85)
            
            logger.info(f"Converting {len(pages_to_convert)} pages at {dpi_value} DPI")
            
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=dpi_value,
                fmt=image_format,
                first_page=pages_to_convert[0] + 1,  # convert_from_path uses 1-indexed
                last_page=pages_to_convert[-1] + 1
            )
            
            # Save images
            image_paths = []
            for idx, (page_num, image) in enumerate(zip(pages_to_convert, images)):
                output_filename = f"page_{page_num + 1:03d}.{image_format}"
                output_path = os.path.join(output_folder, output_filename)
                
                # Save with quality settings
                if image_format.lower() == 'jpg' or image_format.lower() == 'jpeg':
                    image.save(output_path, 'JPEG', quality=quality_value, optimize=True)
                else:
                    image.save(output_path, 'PNG', optimize=True)
                
                image_paths.append(output_path)
                logger.info(f"Saved page {page_num + 1} to {output_filename}")
            
            message = f"✅ Converted {len(image_paths)} pages to {image_format.upper()}"
            return True, message, image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            return False, f"Error: {str(e)}", []
    
    @staticmethod
    def pdf_to_text(
        pdf_path: str,
        output_path: str,
        page_range: str = 'all',
        preserve_layout: bool = True
    ) -> Tuple[bool, str, int]:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            output_path: Path to save text file
            page_range: Page range to convert
            preserve_layout: Try to preserve text layout
            
        Returns:
            Tuple of (success, message, file_size)
        """
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            
            # Get total pages
            total_pages = PDFConverter.get_pdf_page_count(pdf_path)
            if total_pages == 0:
                return False, "PDF has no pages", 0
            
            # Parse page range
            pages_to_convert = PDFConverter.parse_page_range(page_range, total_pages)
            if not pages_to_convert:
                return False, "No valid pages to convert", 0
            
            extracted_text = ""
            
            if preserve_layout:
                # Use pdfplumber for better layout preservation
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num in pages_to_convert:
                        if page_num < len(pdf.pages):
                            page = pdf.pages[page_num]
                            text = page.extract_text()
                            if text:
                                extracted_text += f"\n{'='*60}\n"
                                extracted_text += f"Page {page_num + 1}\n"
                                extracted_text += f"{'='*60}\n\n"
                                extracted_text += text + "\n\n"
            else:
                # Use PyPDF for simple text extraction
                reader = PdfReader(pdf_path)
                for page_num in pages_to_convert:
                    if page_num < len(reader.pages):
                        page = reader.pages[page_num]
                        text = page.extract_text()
                        if text:
                            extracted_text += f"\n--- Page {page_num + 1} ---\n\n"
                            extracted_text += text + "\n\n"
            
            if not extracted_text.strip():
                return False, "No text found in PDF (might be scanned images)", 0
            
            # Save text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            file_size = FileManager.get_file_size(output_path)
            
            logger.info(f"Extracted text from {len(pages_to_convert)} pages")
            return True, f"✅ Extracted text from {len(pages_to_convert)} pages", file_size
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return False, f"Error: {str(e)}", 0
    
    @staticmethod
    def pdf_to_docx(
        pdf_path: str,
        output_path: str,
        page_range: str = 'all'
    ) -> Tuple[bool, str, int]:
        """
        Convert PDF to DOCX
        
        Args:
            pdf_path: Path to PDF file
            output_path: Path to save DOCX file
            page_range: Page range to convert
            
        Returns:
            Tuple of (success, message, file_size)
        """
        try:
            logger.info(f"Converting PDF to DOCX: {pdf_path}")
            
            # Get total pages
            total_pages = PDFConverter.get_pdf_page_count(pdf_path)
            if total_pages == 0:
                return False, "PDF has no pages", 0
            
            # Parse page range
            pages_to_convert = PDFConverter.parse_page_range(page_range, total_pages)
            if not pages_to_convert:
                return False, "No valid pages to convert", 0
            
            # Convert PDF to DOCX
            cv = Converter(pdf_path)
            
            # If specific pages, convert only those
            if len(pages_to_convert) < total_pages:
                # pdf2docx uses 1-indexed pages
                start_page = pages_to_convert[0] + 1
                end_page = pages_to_convert[-1] + 1
                cv.convert(output_path, start=start_page, end=end_page)
            else:
                # Convert all pages
                cv.convert(output_path)
            
            cv.close()
            
            file_size = FileManager.get_file_size(output_path)
            
            logger.info(f"Converted {len(pages_to_convert)} pages to DOCX")
            return True, f"✅ Converted {len(pages_to_convert)} pages to DOCX", file_size
            
        except Exception as e:
            logger.error(f"Error converting PDF to DOCX: {e}")
            return False, f"Error: {str(e)}", 0
    
    @staticmethod
    def create_zip_from_images(image_paths: List[str], zip_path: str) -> Tuple[bool, str, int]:
        """
        Create ZIP archive from image files
        
        Args:
            image_paths: List of image file paths
            zip_path: Path to save ZIP file
            
        Returns:
            Tuple of (success, message, file_size)
        """
        try:
            logger.info(f"Creating ZIP with {len(image_paths)} images")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        # Add file with just the filename (no full path)
                        arcname = os.path.basename(image_path)
                        zipf.write(image_path, arcname)
            
            file_size = FileManager.get_file_size(zip_path)
            
            logger.info(f"Created ZIP archive: {FileManager.format_file_size(file_size)}")
            return True, f"✅ Created ZIP with {len(image_paths)} images", file_size
            
        except Exception as e:
            logger.error(f"Error creating ZIP: {e}")
            return False, f"Error creating ZIP: {str(e)}", 0
    
    @staticmethod
    def get_pdf_text_preview(pdf_path: str, max_chars: int = 500) -> str:
        """
        Get preview of PDF text content
        
        Args:
            pdf_path: Path to PDF file
            max_chars: Maximum characters to return
            
        Returns:
            Preview text
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if pdf.pages:
                    text = pdf.pages[0].extract_text() or ""
                    if len(text) > max_chars:
                        return text[:max_chars] + "..."
                    return text
            return "No text found"
            
        except Exception as e:
            logger.error(f"Error getting text preview: {e}")
            return "Error reading text"
