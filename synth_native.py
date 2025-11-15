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


class TextFieldDelegate(NSObject):
    """Delegate to handle Enter key in text field"""
    
    def textView_doCommandBySelector_(self, textView, selector):
        # Handle Enter key (insertNewline:)
        if selector == 'insertNewline:':
            # Call parent's handleQuery method
            if hasattr(self, 'parent'):
                self.parent.handleQuery_(None)
            return True
        return False


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
        
        # Create a delegate for handling keyboard events
        self.text_delegate = TextFieldDelegate.alloc().init()
        self.text_delegate.parent = self
        
        # Container view - starts tall enough for all elements
        self.input_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 400, 150))
        self.input_view.setWantsLayer_(True)
        
        # Result text view FIRST (at top, will expand downward)
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(15, 60, 370, 80))
        scroll_view.setBorderType_(1)  # Line border
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(2)  # Width sizable
        
        self.result_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 370, 80))
        self.result_view.setEditable_(False)
        self.result_view.setSelectable_(True)
        self.result_view.setRichText_(False)
        self.result_view.setFont_(NSFont.systemFontOfSize_(13))
        
        # Enable text selection and copying
        self.result_view.setAllowsUndo_(False)
        try:
            # Enable context menu for copy/paste
            self.result_view.setUsesFontPanel_(False)
            self.result_view.setUsesRuler_(False)
        except:
            pass
        
        # Dark background with BRIGHT white text for excellent contrast
        self.result_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.17, 1.0))
        try:
            # Use bright white for maximum visibility
            self.result_view.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(0.98, 0.98, 1.0, 1.0))
        except Exception:
            # Fallback
            self.result_view.setTextColor_(NSColor.whiteColor())
        self.result_view.setString_("")
        
        scroll_view.setDocumentView_(self.result_view)
        self.scroll_view = scroll_view
        
        # Text input - use NSTextView for better cursor visibility and auto-expanding
        text_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(15, 20, 220, 30))
        text_scroll.setBorderType_(1)  # Line border
        text_scroll.setHasVerticalScroller_(False)
        text_scroll.setHasHorizontalScroller_(False)
        
        self.text_field = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 220, 30))
        self.text_field.setEditable_(True)
        self.text_field.setSelectable_(True)
        self.text_field.setRichText_(False)
        self.text_field.setFont_(NSFont.systemFontOfSize_(13))
        
        # DARK THEME - match the rest of the UI with semi-transparent dark background
        self.text_field.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.22, 0.95))
        self.text_field.setTextColor_(NSColor.whiteColor())
        self.text_field.setInsertionPointColor_(NSColor.whiteColor())  # WHITE cursor for dark theme!
        
        # Enable word wrap for long text
        self.text_field.setHorizontallyResizable_(False)
        self.text_field.setVerticallyResizable_(True)
        try:
            self.text_field.textContainer().setWidthTracksTextView_(True)
            self.text_field.textContainer().setContainerSize_(NSMakeSize(220, 1000))
        except:
            pass
        
        text_scroll.setDocumentView_(self.text_field)
        self.text_scroll = text_scroll
        
        # Set delegate to handle Enter key
        self.text_field.setDelegate_(self.text_delegate)

        # Ask button - ALWAYS VISIBLE at bottom
        self.ask_button = NSButton.alloc().initWithFrame_(NSMakeRect(240, 20, 45, 30))
        self.ask_button.setTitle_("Ask")
        self.ask_button.setBezelStyle_(1)
        self.ask_button.setTarget_(self)
        self.ask_button.setAction_("handleQuery:")
        self.ask_button.setKeyEquivalent_("\r")  # Enter key
        
        # Copy button - Copy output to clipboard
        self.copy_button = NSButton.alloc().initWithFrame_(NSMakeRect(290, 20, 45, 30))
        self.copy_button.setTitle_("Copy")
        self.copy_button.setBezelStyle_(1)
        self.copy_button.setTarget_(self)
        self.copy_button.setAction_("copyResults:")
        
        # Clear button - ALWAYS VISIBLE at bottom
        self.clear_button = NSButton.alloc().initWithFrame_(NSMakeRect(340, 20, 45, 30))
        self.clear_button.setTitle_("Clear")
        self.clear_button.setBezelStyle_(1)
        self.clear_button.setTarget_(self)
        self.clear_button.setAction_("clearResults:")
        
        # Add to view - result area on top, controls at bottom
        self.input_view.addSubview_(scroll_view)
        self.input_view.addSubview_(text_scroll)
        self.input_view.addSubview_(self.ask_button)
        self.input_view.addSubview_(self.copy_button)
        self.input_view.addSubview_(self.clear_button)
        
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
        """Clear the result area and reset view - also clear the text field!"""
        # Clear result area
        self.result_view.setString_("")
        self.scroll_view.setHidden_(True)
        
        # Clear the text field AND make it editable again
        self.text_field.setString_("")
        self.text_field.setEditable_(True)
        
        # Reset to compact height (just controls visible)
        self.input_view.setFrame_(NSMakeRect(0, 0, 400, 60))
        
        # Focus back on text field so user can type immediately
        try:
            self.text_field.window().makeFirstResponder_(self.text_field)
        except:
            pass
    
    def copyResults_(self, sender):
        """Copy the result text to clipboard"""
        from AppKit import NSPasteboard
        
        result_text = str(self.result_view.string())
        if result_text:
            # Get the general pasteboard
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(result_text, "public.utf8-plain-text")
            
            # Show brief notification
            self.show_notification("Copied!", "", "Result copied to clipboard")
    
    def handleQuery_(self, sender):
        """Handle query from text field"""
        query = str(self.text_field.string()).strip()
        
        if not query:
            return
        
        # Show result area and loading message
        self.scroll_view.setHidden_(False)
        self.safe_update_result("🧠 Thinking...")
        self.expand_view_for_content(100)
        
        # Check for screen analysis - KEEP TEXT VISIBLE during analysis
        ql = query.lower()
        screen_triggers = ['on screen', 'analyze screen', 'on my screen', 'from screen', 'email on screen', 'mail on screen']
        if any(trigger in ql for trigger in screen_triggers):
            # Run screen analysis (non-blocking)
            # DON'T clear text field so user can see their query
            self.analyze_screen_with_query(query)
        else:
            # For regular queries, clear text field after reading
            self.text_field.setString_("")
            self.process_query(query)
    
    def expand_view_for_content(self, content_height):
        """Expand the view to fit content - KEEPS CONTROLS AT BOTTOM"""
        from AppKit import NSMakeRect
        
        # Calculate new total height (controls=60, result area grows)
        result_height = min(300, max(80, content_height))
        new_total_height = result_height + 70  # 60 for controls + 10 padding
        
        # Resize scroll view (result area)
        self.scroll_view.setFrame_(NSMakeRect(15, 60, 370, result_height))
        
        # Resize container
        self.input_view.setFrame_(NSMakeRect(0, 0, 400, new_total_height))
    
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
            # Calculate height based on text length (optimized)
            line_count = text.count('\n') + 1
            text_height = max(80, min(300, line_count * 20))
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
                # Show countdown - shorter messages to reduce lag
                for i in range(2, 0, -1):
                    self.safe_update_result(f"📸 Capturing in {i}s...")
                    time.sleep(1)
                
                screenshot_img = self.screen_capture.capture()
                
                if screenshot_img:
                    try:
                        import pytesseract
                        
                        self.safe_update_result("🔍 Reading screen...")
                        extracted_text = pytesseract.image_to_string(screenshot_img)
                        
                        if extracted_text and len(extracted_text.strip()) > 10:
                            self.safe_update_result(f"🧠 Analyzing ({len(extracted_text.split())} words)...")
                            
                            full_query = f"{query}\n\nScreen content:\n{extracted_text[:800]}"

                            # Use FAST model for quick response
                            result = self.brain.ask(full_query, mode="fast")
                            
                            # Show result
                            self.safe_update_result(result)
                            
                        else:
                            self.safe_update_result("⚠️ No text found on screen")
                    except ImportError:
                        self.safe_update_result("❌ OCR not available\n\nInstall: pip install pytesseract")
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
