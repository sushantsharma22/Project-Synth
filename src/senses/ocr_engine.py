"""
OCR Engine - Extract text from images
Uses pytesseract for optical character recognition

Author: Sushant Sharma
"""

import os
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class OCREngine:
    """Extract text from images using OCR"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize OCR engine
        
        Args:
            tesseract_path: Path to tesseract executable (optional)
        """
        self.available = TESSERACT_AVAILABLE
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text(self, image_path: str) -> Dict:
        """Extract text from an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with:
                - text: Extracted text
                - confidence: OCR confidence score (0-1)
                - success: Whether extraction succeeded
        """
        if not self.available:
            # Fallback: Try to use macOS built-in OCR or just read filename
            return {
                'text': f"[OCR not available - install pytesseract]\nImage: {Path(image_path).name}",
                'confidence': 0.0,
                'success': False,
                'method': 'fallback'
            }
        
        try:
            # Open image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence = avg_confidence / 100.0  # Convert to 0-1 scale
            except:
                confidence = 0.8  # Default confidence
            
            return {
                'text': text.strip(),
                'confidence': confidence,
                'success': True,
                'method': 'pytesseract'
            }
            
        except Exception as e:
            return {
                'text': f"[OCR Error: {str(e)}]",
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def extract_from_region(self, image_path: str, bbox: tuple) -> Dict:
        """Extract text from a specific region of an image
        
        Args:
            image_path: Path to image file
            bbox: Bounding box (x, y, width, height)
            
        Returns:
            Dict with extracted text and metadata
        """
        if not self.available:
            return {
                'text': '[OCR not available]',
                'confidence': 0.0,
                'success': False
            }
        
        try:
            image = Image.open(image_path)
            
            # Crop to region
            x, y, w, h = bbox
            region = image.crop((x, y, x + w, y + h))
            
            # Extract text from region
            text = pytesseract.image_to_string(region)
            
            return {
                'text': text.strip(),
                'confidence': 0.8,
                'success': True,
                'region': bbox
            }
            
        except Exception as e:
            return {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            }
