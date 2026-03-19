import os
from typing import List, Optional
from pypdf import PdfWriter, PdfReader
from utils.logger import logger
from utils.file_handler import FileManager

class PDFOperations:
    """Handle PDF operations like merging, splitting, etc."""
    
    @staticmethod
    def merge_pdfs(input_files: List[str], output_path: str) -> tuple[bool, str, int]:
        """
        Merge multiple PDF files into one
        
        Args:
            input_files: List of PDF file paths to merge
            output_path: Path where merged PDF will be saved
            
        Returns:
            Tuple of (success: bool, message: str, file_size: int)
        """
        try:
            if not input_files:
                return False, "❌ No PDF files provided", 0
            
            if len(input_files) < 2:
                return False, "❌ Need at least 2 PDF files to merge", 0
            
            # Verify all files exist
            for file_path in input_files:
                if not os.path.exists(file_path):
                    return False, f"❌ File not found: {os.path.basename(file_path)}", 0
            
            logger.info(f"Starting PDF merge of {len(input_files)} files")
            
            # Create PDF merger
            merger = PdfWriter()
            
            # Add all PDFs to merger
            for idx, pdf_file in enumerate(input_files, 1):
                try:
                    logger.info(f"Adding file {idx}/{len(input_files)}: {os.path.basename(pdf_file)}")
                    merger.append(pdf_file)
                except Exception as e:
                    logger.error(f"Error adding PDF {pdf_file}: {e}")
                    merger.close()
                    return False, f"❌ Error reading PDF file: {os.path.basename(pdf_file)}", 0
            
            # Write merged PDF
            logger.info(f"Writing merged PDF to: {output_path}")
            merger.write(output_path)
            merger.close()
            
            # Get output file size
            output_size = FileManager.get_file_size(output_path)
            
            logger.info(f"✅ Successfully merged {len(input_files)} PDFs. Output size: {output_size} bytes")
            return True, f"✅ Successfully merged {len(input_files)} PDF files", output_size
            
        except Exception as e:
            logger.error(f"Error merging PDFs: {e}")
            return False, f"❌ Error merging PDFs: {str(e)}", 0
    
    @staticmethod
    def get_pdf_info(file_path: str) -> dict:
        """
        Get information about a PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            reader = PdfReader(file_path)
            
            info = {
                'num_pages': len(reader.pages),
                'file_size': FileManager.get_file_size(file_path),
                'file_name': os.path.basename(file_path),
                'is_encrypted': reader.is_encrypted
            }
            
            # Try to get metadata
            if reader.metadata:
                info['title'] = reader.metadata.get('/Title', 'N/A')
                info['author'] = reader.metadata.get('/Author', 'N/A')
                info['creator'] = reader.metadata.get('/Creator', 'N/A')
            else:
                info['title'] = 'N/A'
                info['author'] = 'N/A'
                info['creator'] = 'N/A'
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {
                'num_pages': 0,
                'file_size': FileManager.get_file_size(file_path),
                'file_name': os.path.basename(file_path),
                'is_encrypted': False,
                'error': str(e)
            }
    
    @staticmethod
    def validate_pdf(file_path: str) -> tuple[bool, str]:
        """
        Validate if file is a valid PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            reader = PdfReader(file_path)
            
            # Check if encrypted
            if reader.is_encrypted:
                return False, "PDF is password protected"
            
            # Check if has pages
            if len(reader.pages) == 0:
                return False, "PDF has no pages"
            
            return True, "Valid PDF"
            
        except Exception as e:
            logger.error(f"PDF validation error: {e}")
            return False, f"Invalid PDF: {str(e)}"
    
    @staticmethod
    def estimate_merge_size(file_paths: List[str]) -> int:
        """
        Estimate the size of merged PDF
        
        Args:
            file_paths: List of PDF file paths
            
        Returns:
            Estimated size in bytes
        """
        total_size = sum(FileManager.get_file_size(f) for f in file_paths)
        # Merging usually reduces size slightly due to shared resources
        estimated_size = int(total_size * 0.95)
        return estimated_size
