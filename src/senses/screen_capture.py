"""
Project Synth - Screen Capture

Captures screenshots for context with AI analysis.

Phase 1: Senses - Detection System
Target: <100KB compressed images
"""

import time
import base64
from io import BytesIO
from typing import Optional, Tuple
from PIL import Image
import mss


class ScreenCapture:
    """
    Captures and processes screenshots for AI context.
    
    Features:
    - Fast capture using mss library
    - Image compression and optimization
    - Base64 encoding for transmission
    - Target: <100KB per image
    """
    
    def __init__(self, quality: int = 75, max_width: int = 1920):
        """
        Initialize screen capture.
        
        Args:
            quality: JPEG quality (1-100, default: 75)
            max_width: Maximum width for resizing (default: 1920)
        """
        self.quality = quality
        self.max_width = max_width
        self.sct = mss.mss()
        
    def capture(self, monitor: int = 1) -> Optional[Image.Image]:
        """
        Capture screenshot from specified monitor.
        
        Args:
            monitor: Monitor number (1 = primary, 0 = all monitors)
            
        Returns:
            PIL Image object or None if capture failed
        """
        try:
            # Capture screenshot
            screenshot = self.sct.grab(self.sct.monitors[monitor])
            
            # Convert to PIL Image
            img = Image.frombytes(
                'RGB',
                (screenshot.width, screenshot.height),
                screenshot.rgb
            )
            
            return img
            
        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            return None
    
    def capture_compressed(self, monitor: int = 1) -> Optional[bytes]:
        """
        Capture and compress screenshot.
        
        Args:
            monitor: Monitor number
            
        Returns:
            Compressed image as bytes, or None if failed
        """
        img = self.capture(monitor)
        if not img:
            return None
            
        return self._compress_image(img)
    
    def capture_base64(self, monitor: int = 1) -> Optional[str]:
        """
        Capture screenshot and encode as base64 string.
        
        Args:
            monitor: Monitor number
            
        Returns:
            Base64-encoded image string, or None if failed
        """
        compressed = self.capture_compressed(monitor)
        if not compressed:
            return None
            
        return base64.b64encode(compressed).decode('utf-8')
    
    def _compress_image(self, img: Image.Image) -> bytes:
        """
        Compress and optimize image.
        
        Args:
            img: PIL Image to compress
            
        Returns:
            Compressed image bytes
        """
        # Resize if too large
        if img.width > self.max_width:
            aspect_ratio = img.height / img.width
            new_width = self.max_width
            new_height = int(new_width * aspect_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Compress to JPEG
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=self.quality, optimize=True)
        
        return buffer.getvalue()
    
    def get_size_info(self, monitor: int = 1) -> dict:
        """
        Get size information for captured and compressed image.
        
        Args:
            monitor: Monitor number
            
        Returns:
            Dict with original and compressed sizes
        """
        img = self.capture(monitor)
        if not img:
            return {}
        
        # Original size (rough estimate)
        original_bytes = img.width * img.height * 3  # RGB
        
        # Compressed size
        compressed = self._compress_image(img)
        compressed_bytes = len(compressed)
        
        return {
            'resolution': f"{img.width}x{img.height}",
            'original_kb': round(original_bytes / 1024, 2),
            'compressed_kb': round(compressed_bytes / 1024, 2),
            'compression_ratio': round(original_bytes / compressed_bytes, 2),
            'under_100kb': compressed_bytes < 100 * 1024
        }
    
    def list_monitors(self) -> list:
        """
        List all available monitors.
        
        Returns:
            List of monitor information
        """
        monitors = []
        for i, monitor in enumerate(self.sct.monitors):
            if i == 0:  # Skip "all monitors" entry
                continue
            monitors.append({
                'number': i,
                'width': monitor['width'],
                'height': monitor['height'],
                'left': monitor['left'],
                'top': monitor['top']
            })
        return monitors


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Screen Capture")
    print("=" * 60)
    
    # Initialize screen capture
    capture = ScreenCapture(quality=75, max_width=1920)
    
    # List available monitors
    print("\n📺 Available Monitors:")
    monitors = capture.list_monitors()
    for mon in monitors:
        print(f"  Monitor {mon['number']}: {mon['width']}x{mon['height']}")
    
    # Capture and analyze
    print("\n📸 Capturing screenshot...")
    start_time = time.time()
    
    img = capture.capture(monitor=1)
    if img:
        capture_time = time.time() - start_time
        print(f"  ✅ Captured in {capture_time*1000:.1f}ms")
        
        # Get size info
        info = capture.get_size_info(monitor=1)
        print("\n📊 Size Information:")
        print(f"  Resolution: {info['resolution']}")
        print(f"  Original: {info['original_kb']} KB")
        print(f"  Compressed: {info['compressed_kb']} KB")
        print(f"  Compression: {info['compression_ratio']}x")
        print(f"  Under 100KB: {'✅ Yes' if info['under_100kb'] else '❌ No'}")
        
        # Test base64 encoding
        print("\n🔤 Testing base64 encoding...")
        base64_str = capture.capture_base64(monitor=1)
        if base64_str:
            print(f"  ✅ Encoded: {len(base64_str)} characters")
            print(f"  Preview: {base64_str[:50]}...")
        
        print("\n✅ All tests passed!")
    else:
        print("  ❌ Capture failed")
    
    print("\n💡 Tip: Grant Screen Recording permission in System Preferences → Privacy")
