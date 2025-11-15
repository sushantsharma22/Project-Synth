"""
Project Synth - Clipboard Monitor

Monitors clipboard changes using macOS NSPasteboard for proactive detection.

Phase 1: Senses - Detection System
Target: <500ms detection delay
"""

import time
import threading
from typing import Callable, Optional
from AppKit import NSPasteboard


class ClipboardMonitor:
    """
    Monitors macOS clipboard for changes using NSPasteboard.
    
    Features:
    - Event-driven detection
    - <500ms delay target
    - Content type detection
    - Privacy filtering
    """
    
    def __init__(self, callback: Optional[Callable] = None, interval: float = 0.3):
        """
        Initialize clipboard monitor.
        
        Args:
            callback: Function to call when clipboard changes
            interval: Polling interval in seconds (default: 0.3s = 300ms)
        """
        self.callback = callback
        self.interval = interval
        self.pasteboard = NSPasteboard.generalPasteboard()
        self.last_change_count = self.pasteboard.changeCount()
        self.last_content = ""
        self.running = False
        self.thread = None
        
    def start(self):
        """Start monitoring clipboard in background thread."""
        if self.running:
            print("⚠️ Clipboard monitor already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("👀 Clipboard monitoring started")
        
    def stop(self):
        """Stop monitoring clipboard."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("🛑 Clipboard monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop running in background thread."""
        while self.running:
            try:
                current_count = self.pasteboard.changeCount()
                
                if current_count != self.last_change_count:
                    # Clipboard changed!
                    detection_time = time.time()
                    content = self._get_clipboard_content()
                    
                    if content and content != self.last_content:
                        self.last_content = content
                        self.last_change_count = current_count
                        
                        # Apply privacy filter
                        if not self._is_sensitive(content):
                            if self.callback:
                                self.callback({
                                    'content': content,
                                    'timestamp': detection_time,
                                    'type': self._detect_content_type(content)
                                })
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"❌ Clipboard monitor error: {e}")
                time.sleep(self.interval)
    
    def _get_clipboard_content(self) -> Optional[str]:
        """Get current clipboard content as string."""
        try:
            content = self.pasteboard.stringForType_("public.utf8-plain-text")
            return content if content else None
        except Exception as e:
            print(f"⚠️ Could not read clipboard: {e}")
            return None
    
    def _detect_content_type(self, content: str) -> str:
        """Detect type of clipboard content."""
        content_lower = content.lower().strip()
        
        # URL detection
        if content_lower.startswith(('http://', 'https://', 'www.')):
            return 'url'
        
        # Code detection (simple heuristic)
        if any(keyword in content for keyword in ['def ', 'class ', 'import ', 'function', 'const ', 'let ', 'var ']):
            return 'code'
        
        # Error detection
        if any(error in content for error in ['Error:', 'Exception:', 'Traceback', 'at line']):
            return 'error'
        
        # File path detection
        if content.startswith('/') or '\\' in content:
            return 'path'
        
        return 'text'
    
    def _is_sensitive(self, content: str) -> bool:
        """
        Check if content appears to be sensitive (password, API key, etc.).
        
        Returns:
            True if content should be filtered out
        """
        content_lower = content.lower()
        
        # Common sensitive patterns
        sensitive_keywords = [
            'password', 'passwd', 'api_key', 'apikey', 'secret', 
            'token', 'private_key', 'credentials', 'auth_token',
            'access_token', 'bearer', 'ssh-rsa'
        ]
        
        for keyword in sensitive_keywords:
            if keyword in content_lower:
                print(f"🔒 Filtered sensitive content (matched: {keyword})")
                return True
        
        # Very long strings might be tokens
        if len(content) > 200 and ' ' not in content:
            print("🔒 Filtered potential token (long string without spaces)")
            return True
            
        return False


# Example usage and testing
if __name__ == "__main__":
    def on_clipboard_change(data):
        """Callback for clipboard changes."""
        print("\n📋 Clipboard changed!")
        print(f"  Type: {data['type']}")
        print(f"  Content: {data['content'][:100]}...")
        print(f"  Time: {time.time() - data['timestamp']:.3f}s ago")
    
    # Create and start monitor
    monitor = ClipboardMonitor(callback=on_clipboard_change)
    
    print("🧪 Testing Clipboard Monitor")
    print("=" * 60)
    print("Copy some text to test detection...")
    print("Press Ctrl+C to stop")
    
    try:
        monitor.start()
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        monitor.stop()
        print("✅ Test complete!")
