#!/usr/bin/env python3
"""
Trigger System for Project Synth
Combines clipboard + screenshot context and triggers Brain API calls.

Phase 1: Day 5-6
Integrates clipboard monitoring + screen capture into unified context packages.
"""

import json
import base64
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from .clipboard_monitor import ClipboardMonitor
from .screen_capture import ScreenCapture


class ContextPackage:
    """
    Unified context package combining clipboard and screen data.
    """
    
    def __init__(self, 
                 clipboard_content: str,
                 clipboard_metadata: Dict[str, Any],
                 screenshot_base64: Optional[str] = None,
                 screenshot_metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize context package.
        
        Args:
            clipboard_content: Text from clipboard
            clipboard_metadata: Metadata from clipboard monitor
            screenshot_base64: Base64-encoded screenshot (optional)
            screenshot_metadata: Screenshot metadata (optional)
        """
        self.clipboard_content = clipboard_content
        self.clipboard_metadata = clipboard_metadata
        self.screenshot_base64 = screenshot_base64
        self.screenshot_metadata = screenshot_metadata or {}
        self.timestamp = datetime.now().isoformat()
        self.context_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique context ID."""
        import hashlib
        content_hash = hashlib.md5(
            f"{self.timestamp}{self.clipboard_content}".encode()
        ).hexdigest()[:8]
        return f"ctx_{content_hash}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'context_id': self.context_id,
            'timestamp': self.timestamp,
            'clipboard': {
                'content': self.clipboard_content,
                'metadata': self.clipboard_metadata
            },
            'screenshot': {
                'base64': self.screenshot_base64,
                'metadata': self.screenshot_metadata
            } if self.screenshot_base64 else None
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def get_size_kb(self) -> float:
        """
        Calculate total package size in KB.
        
        Returns:
            Size in kilobytes
        """
        json_str = self.to_json(indent=None)
        return len(json_str.encode('utf-8')) / 1024
    
    def __repr__(self) -> str:
        return f"<ContextPackage {self.context_id} at {self.timestamp}>"


class TriggerSystem:
    """
    Main trigger system that coordinates detection and context creation.
    
    Features:
    - Clipboard monitoring with automatic screenshot on trigger
    - Content filtering (skip unwanted content)
    - Context package creation
    - Callback system for downstream processing
    """
    
    def __init__(self, 
                 trigger_callback: Optional[Callable[[ContextPackage], None]] = None,
                 auto_screenshot: bool = True,
                 screenshot_delay: float = 0.1):
        """
        Initialize trigger system.
        
        Args:
            trigger_callback: Function called when context package is ready
                             Signature: callback(context: ContextPackage)
            auto_screenshot: Automatically capture screenshot on clipboard change
            screenshot_delay: Delay before capturing screenshot (seconds)
        """
        self.trigger_callback = trigger_callback
        self.auto_screenshot = auto_screenshot
        self.screenshot_delay = screenshot_delay
        
        # Initialize components
        self.clipboard_monitor = ClipboardMonitor(callback=self._on_clipboard_change)
        self.screen_capture = ScreenCapture()
        
        # Stats
        self.stats = {
            'total_triggers': 0,
            'with_screenshot': 0,
            'avg_package_size_kb': 0,
            'total_size_kb': 0
        }
        
        # Running state
        self.running = False
    
    def _on_clipboard_change(self, data: Dict[str, Any]):
        """
        Handle clipboard change event.
        
        Args:
            data: Clipboard data dict with 'content', 'timestamp', 'type'
        """
        import time
        
        content = data['content']
        metadata = {
            'timestamp': data['timestamp'],
            'type': data['type']
        }
        
        # Optional: Add small delay before screenshot
        if self.auto_screenshot and self.screenshot_delay > 0:
            time.sleep(self.screenshot_delay)
        
        # Capture screenshot if enabled
        screenshot_base64 = None
        screenshot_metadata = None
        
        if self.auto_screenshot:
            try:
                screenshot_base64 = self.screen_capture.capture_base64()
                if screenshot_base64:
                    # Get screenshot size info
                    img_bytes = len(screenshot_base64.encode('utf-8'))
                    screenshot_metadata = {
                        'size_kb': img_bytes / 1024,
                        'encoding': 'base64'
                    }
                    self.stats['with_screenshot'] += 1
            except Exception as e:
                print(f"⚠️  Screenshot capture failed: {e}")
        
        # Create context package
        context = ContextPackage(
            clipboard_content=content,
            clipboard_metadata=metadata,
            screenshot_base64=screenshot_base64,
            screenshot_metadata=screenshot_metadata
        )
        
        # Update stats
        self.stats['total_triggers'] += 1
        package_size = context.get_size_kb()
        self.stats['total_size_kb'] += package_size
        self.stats['avg_package_size_kb'] = (
            self.stats['total_size_kb'] / self.stats['total_triggers']
        )
        
        print(f"\n🎯 Trigger fired: {context.context_id}")
        print(f"   Size: {package_size:.2f} KB")
        print(f"   Has screenshot: {screenshot_base64 is not None}")
        
        # Call downstream callback
        if self.trigger_callback:
            try:
                self.trigger_callback(context)
            except Exception as e:
                print(f"⚠️  Trigger callback error: {e}")
    
    def start(self, poll_interval: float = 0.1):
        """
        Start the trigger system.
        
        Args:
            poll_interval: Clipboard polling interval in seconds
        """
        if self.running:
            print("⚠️  Trigger system already running")
            return
        
        self.running = True
        self.clipboard_monitor.start(poll_interval=poll_interval)
        print(f"✅ Trigger system started (auto_screenshot: {self.auto_screenshot})")
    
    def stop(self):
        """Stop the trigger system."""
        if not self.running:
            print("⚠️  Trigger system not running")
            return
        
        self.running = False
        self.clipboard_monitor.stop()
        print("✅ Trigger system stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get trigger statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            **self.stats
        }
    
    def set_auto_screenshot(self, enabled: bool):
        """
        Enable or disable automatic screenshots.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.auto_screenshot = enabled
        print(f"✅ Auto-screenshot {'enabled' if enabled else 'disabled'}")


def example_trigger_callback(context: ContextPackage):
    """Example callback that prints context information."""
    print(f"\n📦 Context Package Received!")
    print(f"   ID: {context.context_id}")
    print(f"   Timestamp: {context.timestamp}")
    print(f"   Content length: {len(context.clipboard_content)} chars")
    
    if context.screenshot_base64:
        print(f"   Screenshot: {len(context.screenshot_base64)} bytes (base64)")
        print(f"   Screenshot size: {context.screenshot_metadata.get('size_kb', 0):.2f} KB")
    else:
        print(f"   Screenshot: None")
    
    print(f"   Total package size: {context.get_size_kb():.2f} KB")
    
    # Show first 100 chars of content
    preview = context.clipboard_content[:100]
    if len(context.clipboard_content) > 100:
        preview += "..."
    print(f"   Preview: {preview}")


if __name__ == "__main__":
    """Test the trigger system."""
    import time
    
    print("🚀 Starting Trigger System Test")
    print("=" * 60)
    print("This will monitor your clipboard and capture screenshots")
    print("when clipboard content changes.")
    print("")
    print("Try copying:")
    print("  - Regular text")
    print("  - Code snippets")
    print("  - Error messages")
    print("  - URLs")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print("")
    
    # Create trigger system with example callback
    trigger = TriggerSystem(
        trigger_callback=example_trigger_callback,
        auto_screenshot=True,
        screenshot_delay=0.1  # Wait 100ms before screenshot
    )
    
    try:
        trigger.start(poll_interval=0.1)
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping trigger system...")
        trigger.stop()
        
        # Show statistics
        stats = trigger.get_stats()
        print("\n📊 Trigger Statistics:")
        print(f"   Total triggers: {stats['total_triggers']}")
        print(f"   With screenshots: {stats['with_screenshot']}")
        print(f"   Avg package size: {stats['avg_package_size_kb']:.2f} KB")
        print(f"   Total data: {stats['total_size_kb']:.2f} KB")
        
        clipboard_metrics = stats['clipboard_metrics']
        print(f"\n📋 Clipboard Metrics:")
        print(f"   Total changes: {clipboard_metrics['total_changes']}")
        print(f"   Filtered: {clipboard_metrics['filtered_changes']}")
        print(f"   Avg detection: {clipboard_metrics['avg_detection_time_ms']:.2f}ms")
        
        # Success criteria check
        print(f"\n✅ Success Criteria:")
        detection_ok = clipboard_metrics['avg_detection_time_ms'] < 500
        size_ok = stats['avg_package_size_kb'] < 150  # Allow some margin
        
        print(f"   Detection <500ms: {'✅' if detection_ok else '❌'} ({clipboard_metrics['avg_detection_time_ms']:.2f}ms)")
        print(f"   Package <150KB: {'✅' if size_ok else '❌'} ({stats['avg_package_size_kb']:.2f}KB)")
        
        if detection_ok and size_ok:
            print(f"\n🎉 All targets met!")
        else:
            print(f"\n⚠️  Some targets missed - optimization needed")
