"""
🎯 SYNTH MENU BAR - NATIVE macOS with Embedded Text Input
Uses PyObjC to create a dropdown with text field embedded directly
"""

import sys
from pathlib import Path
from AppKit import (NSApplication, NSStatusBar, NSMenu, NSMenuItem, 
                    NSTextField, NSButton, NSView, NSColor, NSFont,
                    NSNotificationCenter, NSUserNotification, NSUserNotificationCenter)
from Foundation import NSObject, NSMakeRect
import objc

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain_client import DeltaBrain
from src.senses.screen_capture import ScreenCapture


class SynthMenuBarNative(NSObject):
    """Native macOS menu bar with embedded text input"""
    
    def init(self):
        self = objc.super(SynthMenuBarNative, self).init()
        if self is None:
            return None
        
        # Initialize AI components
        self.brain = DeltaBrain()
        self.screen_capture = ScreenCapture()
        
        # Create status bar item
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(-1)  # Variable width
        self.statusitem.setTitle_("Synth")
        
        # Create menu
        self.menu = NSMenu.alloc().init()
        
        # Create custom view with text field
        self.create_input_view()
        
        # Add menu items
        self.build_menu()
        
        # Set menu to status item
        self.statusitem.setMenu_(self.menu)
        
        return self
    
    def create_input_view(self):
        """Create custom view with embedded text field and result area"""
        from AppKit import NSTextView, NSScrollView, NSMakeSize, NSBorderlessWindowMask
        
        # Container view - will expand based on content
        self.input_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 400, 100))
        self.input_view.setWantsLayer_(True)
        
        # Text field - highly visible with cursor
        self.text_field = NSTextField.alloc().initWithFrame_(NSMakeRect(15, 60, 300, 30))
        self.text_field.setPlaceholderString_("Ask Synth anything...")
        self.text_field.setTarget_(self)
        self.text_field.setAction_("handleQuery:")
        self.text_field.setEditable_(True)
        self.text_field.setSelectable_(True)
        self.text_field.setBezeled_(True)
        self.text_field.setBezelStyle_(1)  # Square bezel
        self.text_field.setDrawsBackground_(True)

        # Bright colors for visibility
        self.text_field.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.95, 0.95, 0.98, 1.0))
        self.text_field.setTextColor_(NSColor.blackColor())
        self.text_field.setFont_(NSFont.systemFontOfSize_(14))

        # Force cursor to show
        self.text_field.setFocusRingType_(1)  # Show focus ring

        # Ask button
        self.ask_button = NSButton.alloc().initWithFrame_(NSMakeRect(245, 60, 60, 30))
        self.ask_button.setTitle_("Ask")
        self.ask_button.setBezelStyle_(1)
        self.ask_button.setTarget_(self)
        self.ask_button.setAction_("handleQuery:")
        self.ask_button.setKeyEquivalent_("\r")  # Enter key
        
        # Clear button
        self.clear_button = NSButton.alloc().initWithFrame_(NSMakeRect(310, 60, 75, 30))
        self.clear_button.setTitle_("Clear")
        self.clear_button.setBezelStyle_(1)
        self.clear_button.setTarget_(self)
        self.clear_button.setAction_("clearResults:")
        
        # Result text view (scrollable, expandable)
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(15, 15, 370, 40))
        scroll_view.setBorderType_(1)  # Line border
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(2)  # Width sizable
        
        self.result_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 370, 40))
        self.result_view.setEditable_(False)
        self.result_view.setSelectable_(True)
        self.result_view.setRichText_(False)
        self.result_view.setFont_(NSFont.systemFontOfSize_(13))
        
        # Dark background, white text for better contrast
        self.result_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.12, 0.12, 0.14, 1.0))
        try:
            self.result_view.setTextColor_(NSColor.whiteColor())
        except Exception:
            # Fallback for older PyObjC bindings
            self.result_view.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0))
        self.result_view.setString_("")
        
        scroll_view.setDocumentView_(self.result_view)
        
        # Add to view
        self.input_view.addSubview_(self.text_field)
        self.input_view.addSubview_(self.ask_button)
        self.input_view.addSubview_(self.clear_button)
        self.input_view.addSubview_(scroll_view)
        
        # Store scroll view reference
        self.scroll_view = scroll_view
        
        # Initially hide result view
        self.scroll_view.setHidden_(True)
    
    def build_menu(self):
        """Build menu with embedded input view"""
        # Add custom view as menu item
        view_item = NSMenuItem.alloc().init()
        view_item.setView_(self.input_view)
        self.menu.addItem_(view_item)
        
        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())
        
        # Quick screen analysis
        screen_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "📸 Analyze Screen", "quickScreenAnalysis:", ""
        )
        screen_item.setTarget_(self)
        self.menu.addItem_(screen_item)
    
    def clearResults_(self, sender):
        """Clear the result area and reset view"""
        self.result_view.setString_("")
        self.scroll_view.setHidden_(True)
        self.text_field.setStringValue_("")
        # Reset to default height
        self.input_view.setFrame_(NSMakeRect(0, 0, 400, 100))
    
    def handleQuery_(self, sender):
        """Handle query from text field"""
        query = str(self.text_field.stringValue()).strip()
        
        if not query:
            return
        
        # Show result area and loading message
        self.scroll_view.setHidden_(False)
        self.result_view.setString_("🧠 Thinking...")
        self.expand_view_for_content(50)
        
        # Check for screen analysis -- be conservative to avoid accidental triggers
        # Only trigger when user explicitly mentions "on screen" or "analyze screen"
        ql = query.lower()
        screen_triggers = ['on screen', "analyze screen", "screen"]
        if any(trigger in ql for trigger in screen_triggers):
            # Ask for confirmation if it's an ambiguous short query
            # Run screen analysis (non-blocking)
            self.analyze_screen_with_query(query)
        else:
            # Clear text field for regular queries
            self.text_field.setStringValue_("")
            self.process_query(query)
    
    def expand_view_for_content(self, content_height):
        """Expand the view to fit content"""
        from AppKit import NSMakeRect
        
        # Calculate new height (min 100, max 400)
        new_height = min(400, max(100, content_height + 95))
        
        # Resize scroll view
        scroll_height = new_height - 95
        self.scroll_view.setFrame_(NSMakeRect(15, 15, 370, scroll_height))
        
        # Resize container
        frame = self.input_view.frame()
        self.input_view.setFrame_(NSMakeRect(frame.origin.x, frame.origin.y, 400, new_height))
    
    def process_query(self, query):
        """Process regular query and show in dropdown - runs in background"""
        import threading
        
        # Show loading immediately
        self.result_view.setString_("🧠 Thinking...")
        
        def process_in_background():
            try:
                # Get response from Brain (this runs in background)
                result = self.brain.ask(query, mode="fast")
                
                # Update UI safely
                self.safe_update_result(result)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                self.safe_update_result(error_msg)
        
        # Run in background thread so Mac doesn't freeze
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def safe_update_result(self, text):
        """Safely update result view from any thread"""
        # Ensure UI updates happen on the main thread (use performSelectorOnMainThread)
        try:
            # Use performSelectorOnMainThread to safely update UI
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                "updateResultText:", text, False
            )
        except Exception:
            # Fallback: directly set (may work in some environments)
            try:
                self.result_view.setString_(text)
                text_height = len(text) / 2
                self.expand_view_for_content(text_height)
            except Exception:
                # Last resort: ignore UI update failure
                pass

    def updateResultText_(self, text):
        """Update result view on the main thread (selector method - note the trailing underscore)."""
        try:
            self.result_view.setString_(text)
            text_height = len(text) / 2
            self.expand_view_for_content(text_height)
        except Exception:
            pass
    
    def quickScreenAnalysis_(self, sender):
        """Quick screen analysis from menu"""
        self.analyze_screen_with_query("what's on the screen")
    
    def analyze_screen_with_query(self, query):
        """Analyze screen content and show in dropdown - RUNS IN BACKGROUND"""
        import time
        import threading
        
        def capture_and_analyze():
            try:
                # Show countdown - ALL UI updates must go through safe_update_result!
                for i in range(2, 0, -1):
                    self.safe_update_result(f"📸 Capturing screen in {i} seconds...")
                    time.sleep(1)
                
                screenshot_img = self.screen_capture.capture()
                
                if screenshot_img:
                    try:
                        import pytesseract
                        
                        self.safe_update_result("🔍 Reading screen content...")
                        extracted_text = pytesseract.image_to_string(screenshot_img)
                        
                        if extracted_text and len(extracted_text.strip()) > 10:
                            self.safe_update_result("🧠 Analyzing screen content...")
                            
                            full_query = f"{query}\n\nScreen content:\n{extracted_text[:800]}"

                            # Use FAST model for initial, quick response to avoid long blocking
                            # The heavy analysis can be requested separately if user wants deeper review
                            result = self.brain.ask(full_query, mode="fast")
                            
                            # Show full result in dropdown
                            self.safe_update_result(result)
                            
                        else:
                            self.safe_update_result("⚠️ No text detected on screen")
                    except ImportError:
                        self.safe_update_result("❌ OCR not available. Install pytesseract.")
                else:
                    self.safe_update_result("❌ Screenshot failed")
            except Exception as e:
                self.safe_update_result(f"❌ Error: {str(e)}")
        
        # Run EVERYTHING in background thread - no freezing!
        thread = threading.Thread(target=capture_and_analyze)
        thread.daemon = True
        thread.start()
    
    def show_notification(self, title, subtitle, message):
        """Show macOS notification"""
        notification = NSUserNotification.alloc().init()
        notification.setTitle_(title)
        notification.setSubtitle_(subtitle)
        notification.setInformativeText_(message)
        
        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        center.deliverNotification_(notification)


def main():
    """Main entry point"""
    print("🚀 Starting Synth Menu Bar (Native)...")
    
    # Create app
    app = NSApplication.sharedApplication()
    
    # Create menu bar
    synth = SynthMenuBarNative.alloc().init()
    
    # Run app
    app.run()


if __name__ == "__main__":
    main()
