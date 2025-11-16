"""
🎯 SYNTH MENU BAR - NATIVE macOS with Embedded Text Input
Uses PyObjC to create a dropdown with text field embedded directly
"""

import sys
from pathlib import Path
from AppKit import (NSApplication, NSStatusBar, NSMenu, NSMenuItem, 
                    NSTextField, NSButton, NSView, NSColor, NSFont,
                    NSNotificationCenter, NSUserNotification, NSUserNotificationCenter,
                    NSTextView, NSScrollView, NSPasteboard, NSApp)
from Foundation import NSObject, NSMakeRect, NSMakeSize
import objc

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain_client import DeltaBrain
from src.senses.screen_capture import ScreenCapture
from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext


class CopyableTextView(NSTextView):
    """Custom NSTextView that properly handles copy/paste in menu bars"""
    
    def acceptsFirstResponder(self):
        """Allow this view to become first responder"""
        return True
    
    def copy_(self, sender):
        """Explicit copy handler"""
        selectedRange = self.selectedRange()
        if selectedRange.length > 0:
            selectedText = self.string()[selectedRange.location:selectedRange.location + selectedRange.length]
        else:
            selectedText = self.string()
        
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setString_forType_(selectedText, "public.utf8-plain-text")
        return True
    
    def paste_(self, sender):
        """Explicit paste handler"""
        pasteboard = NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_("public.utf8-plain-text")
        if text and self.isEditable():
            self.insertText_(text)
        return True
    
    def selectAll_(self, sender):
        """Select all text"""
        self.setSelectedRange_((0, len(self.string())))
        return True


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
        
        # Initialize Plugin Manager
        print("🔌 Loading plugins...")
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_all_plugins()
        print(f"✅ Loaded {len(self.plugin_manager.plugins)} plugins")
        
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
        
        # Create a delegate for handling keyboard events
        self.text_delegate = TextFieldDelegate.alloc().init()
        self.text_delegate.parent = self
        
        # Container view - MORE COMPACT!
        self.input_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 500, 270))
        self.input_view.setWantsLayer_(True)
        
        # Result text view at TOP - NOW WITH CopyableTextView class!
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 65, 480, 195))
        scroll_view.setBorderType_(0)
        scroll_view.setDrawsBackground_(False)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(2)
        
        # USE CUSTOM CopyableTextView INSTEAD OF NSTextView!
        self.result_view = CopyableTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 465, 195))
        self.result_view.setEditable_(False)
        self.result_view.setSelectable_(True)
        self.result_view.setRichText_(False)
        self.result_view.setFont_(NSFont.systemFontOfSize_(12))
        
        # GLASSMORPHISM - Apple-style semi-transparent with better visibility
        self.result_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 0.70))
        self.result_view.setTextColor_(NSColor.whiteColor())
        
        # Rounded corners
        try:
            self.result_view.setWantsLayer_(True)
            self.result_view.layer().setCornerRadius_(12.0)
            self.result_view.layer().setMasksToBounds_(True)
        except:
            pass
        
        # Enable copy operations - CRITICAL SETTINGS
        self.result_view.setAllowsUndo_(False)
        
        # Disable substitutions that interfere with copy/paste
        try:
            self.result_view.setAutomaticTextReplacementEnabled_(False)
            self.result_view.setAutomaticQuoteSubstitutionEnabled_(False)
            self.result_view.setAutomaticDashSubstitutionEnabled_(False)
            self.result_view.setAutomaticSpellingCorrectionEnabled_(False)
        except:
            pass
        
        # Text container settings
        try:
            self.result_view.setUsesFindBar_(True)
            self.result_view.setImportsGraphics_(False)
            self.result_view.setUsesFontPanel_(False)
            self.result_view.setUsesRuler_(False)
            
            # Word wrap and padding
            self.result_view.textContainer().setWidthTracksTextView_(True)
            self.result_view.textContainer().setContainerSize_(NSMakeSize(465, 10000))
            self.result_view.textContainer().setLineFragmentPadding_(10.0)
        except:
            pass
        
        scroll_view.setDocumentView_(self.result_view)
        self.scroll_view = scroll_view
        
        # Text input ABOVE buttons now! - ALSO USE CopyableTextView!
        text_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 30, 480, 30))
        text_scroll.setBorderType_(0)
        text_scroll.setDrawsBackground_(False)
        text_scroll.setHasVerticalScroller_(False)
        text_scroll.setHasHorizontalScroller_(False)
        
        # USE CUSTOM CopyableTextView FOR INPUT TOO!
        self.text_field = CopyableTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 480, 30))
        self.text_field.setEditable_(True)
        self.text_field.setSelectable_(True)
        self.text_field.setRichText_(False)
        self.text_field.setFont_(NSFont.systemFontOfSize_(15))  # Bigger font
        
        # LIGHTER background for BRIGHT CURSOR visibility!
        self.text_field.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.25, 0.25, 0.27, 0.60))
        self.text_field.setTextColor_(NSColor.whiteColor())
        
        # BRIGHT CYAN/BLUE CURSOR - VERY VISIBLE!
        self.text_field.setInsertionPointColor_(NSColor.colorWithRed_green_blue_alpha_(0.3, 0.8, 1.0, 1.0))
        
        # CRITICAL: Enable copy/paste functionality!
        self.text_field.setAllowsUndo_(True)
        self.text_field.setUsesFindBar_(True)
        
        # Disable auto-substitutions (they interfere with copy/paste)
        try:
            self.text_field.setAutomaticTextReplacementEnabled_(False)
            self.text_field.setAutomaticQuoteSubstitutionEnabled_(False)
            self.text_field.setAutomaticDashSubstitutionEnabled_(False)
            self.text_field.setAutomaticSpellingCorrectionEnabled_(False)
        except:
            pass
        
        # Rounded corners!
        try:
            self.text_field.setWantsLayer_(True)
            self.text_field.layer().setCornerRadius_(10.0)
            self.text_field.layer().setMasksToBounds_(True)
        except:
            pass
        
        # Better text handling
        self.text_field.setHorizontallyResizable_(False)
        self.text_field.setVerticallyResizable_(True)
        try:
            self.text_field.textContainer().setWidthTracksTextView_(True)
            self.text_field.textContainer().setContainerSize_(NSMakeSize(480, 1000))
            self.text_field.textContainer().setLineFragmentPadding_(10.0)
        except:
            pass
        
        text_scroll.setDocumentView_(self.text_field)
        self.text_scroll = text_scroll
        
        # Set delegate to handle Enter key
        self.text_field.setDelegate_(self.text_delegate)

        # 4 BUTTONS BELOW TEXT INPUT - PROPERLY ALIGNED!
        # Ask button - BLUE accent color to stand out!
        self.ask_button = NSButton.alloc().initWithFrame_(NSMakeRect(10, 5, 115, 20))
        self.ask_button.setTitle_("Ask")
        self.ask_button.setBezelStyle_(1)
        self.ask_button.setTarget_(self)
        self.ask_button.setAction_("handleQuery:")
        self.ask_button.setKeyEquivalent_("\r")
        self.ask_button.setFont_(NSFont.systemFontOfSize_(12))
        # Blue accent color for Ask button
        try:
            self.ask_button.setBezelStyle_(4)  # Rounded rect
        except:
            pass
        
        # Screen button - checkbox toggle
        self.screen_button = NSButton.alloc().initWithFrame_(NSMakeRect(130, 5, 115, 20))
        self.screen_button.setTitle_("📸 Screen")
        self.screen_button.setButtonType_(3)  # Checkbox
        self.screen_button.setBezelStyle_(1)
        self.screen_button.setState_(0)
        self.screen_button.setFont_(NSFont.systemFontOfSize_(12))
        
        # Copy button - same style as Clear
        self.copy_button = NSButton.alloc().initWithFrame_(NSMakeRect(250, 5, 115, 20))
        self.copy_button.setTitle_("Copy")
        self.copy_button.setBezelStyle_(1)
        self.copy_button.setTarget_(self)
        self.copy_button.setAction_("copyResults:")
        self.copy_button.setFont_(NSFont.systemFontOfSize_(12))
        
        # Clear button
        self.clear_button = NSButton.alloc().initWithFrame_(NSMakeRect(370, 5, 115, 20))
        self.clear_button.setTitle_("Clear")
        self.clear_button.setBezelStyle_(1)
        self.clear_button.setFont_(NSFont.systemFontOfSize_(12))
        self.clear_button.setTarget_(self)
        self.clear_button.setAction_("clearResults:")
        
        # Add to view
        self.input_view.addSubview_(scroll_view)
        self.input_view.addSubview_(text_scroll)
        self.input_view.addSubview_(self.ask_button)
        self.input_view.addSubview_(self.screen_button)
        self.input_view.addSubview_(self.copy_button)
        self.input_view.addSubview_(self.clear_button)
        
        # Initially hide result view
        self.scroll_view.setHidden_(True)
    
    def build_menu(self):
        """Build menu with embedded input view and settings"""
        # Add custom view as menu item
        view_item = NSMenuItem.alloc().init()
        view_item.setView_(self.input_view)
        self.menu.addItem_(view_item)
        
        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())
        
        # Settings submenu (3 dots equivalent) - WITH ACTIONS
        settings_menu = NSMenu.alloc().init()
        settings_menu.setTitle_("Settings")
        
        # Plugin features with CORRECT names matching actual plugin metadata
        email_item = settings_menu.addItemWithTitle_action_keyEquivalent_("📧 Email Plugin", "showPluginInfo:", "")
        email_item.setTarget_(self)
        email_item.setRepresentedObject_("email_plugin")
        
        file_item = settings_menu.addItemWithTitle_action_keyEquivalent_("📁 File Manager", "showPluginInfo:", "")
        file_item.setTarget_(self)
        file_item.setRepresentedObject_("file_management_plugin")
        
        web_item = settings_menu.addItemWithTitle_action_keyEquivalent_("🔍 Web Search", "showPluginInfo:", "")
        web_item.setTarget_(self)
        web_item.setRepresentedObject_("web_search_plugin")
        
        code_item = settings_menu.addItemWithTitle_action_keyEquivalent_("📊 Code Analyzer", "showPluginInfo:", "")
        code_item.setTarget_(self)
        code_item.setRepresentedObject_("code_doc_plugin")
        
        security_item = settings_menu.addItemWithTitle_action_keyEquivalent_("🔐 Security Tools", "showPluginInfo:", "")
        security_item.setTarget_(self)
        security_item.setRepresentedObject_("security_plugin")
        
        calc_item = settings_menu.addItemWithTitle_action_keyEquivalent_("🧮 Calculator", "showPluginInfo:", "")
        calc_item.setTarget_(self)
        calc_item.setRepresentedObject_("math_plugin")
        
        cal_item = settings_menu.addItemWithTitle_action_keyEquivalent_("📅 Calendar", "showPluginInfo:", "")
        cal_item.setTarget_(self)
        cal_item.setRepresentedObject_("calendar_plugin")
        
        git_item = settings_menu.addItemWithTitle_action_keyEquivalent_("💻 Git Helper", "showPluginInfo:", "")
        git_item.setTarget_(self)
        git_item.setRepresentedObject_("git_plugin")
        
        settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "⚙️ Plugins & Settings", None, ""
        )
        settings_item.setSubmenu_(settings_menu)
        self.menu.addItem_(settings_item)
        
        # Separator
        self.menu.addItem_(NSMenuItem.separatorItem())
        
        # Quick screen analysis
        screen_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "📸 Quick Screen Analysis", "quickScreenAnalysis:", ""
        )
        screen_item.setTarget_(self)
        self.menu.addItem_(screen_item)
    
    def showPluginInfo_(self, sender):
        """Execute plugin action when clicked"""
        plugin_name = sender.representedObject()
        
        # Get plugin from manager
        plugin = self.plugin_manager.plugins.get(plugin_name)
        
        if plugin:
            # Show plugin info
            info = f"""🔌 {plugin.metadata.name} v{plugin.metadata.version}

{plugin.metadata.description}

Author: {plugin.metadata.author}
Status: {"✅ Enabled" if plugin.enabled else "❌ Disabled"}

Type your request in the text field above and click Ask to use this plugin!
The plugin will automatically activate when relevant to your query."""
            
            self.safe_update_result(info)
            self.scroll_view.setHidden_(False)
            self.expand_view_for_content(200)
        else:
            self.safe_update_result(f"❌ Plugin '{plugin_name}' not found")
    
    def clearResults_(self, sender):
        """Clear the result area and reset view - also clear the text field!"""
        # Clear result area
        self.result_view.setString_("")
        self.scroll_view.setHidden_(True)
        
        # Clear the text field AND make it editable again
        self.text_field.setString_("")
        self.text_field.setEditable_(True)
        
        # Reset to compact height
        self.input_view.setFrame_(NSMakeRect(0, 0, 500, 60))
        
        # Focus back on text field so user can type immediately
        try:
            # Make the text field first responder when menu opens
            NSApp.keyWindow().makeFirstResponder_(self.text_field)
        except:
            pass
    
    def copyResults_(self, sender):
        """Copy the result text to clipboard - Enhanced version"""
        result_text = str(self.result_view.string())
        if result_text:
            # Get the general pasteboard
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(result_text, "public.utf8-plain-text")
            
            # Show brief notification
            self.show_notification("Copied!", "", "Result copied to clipboard")
            
            # Also update button text temporarily
            self.copy_button.setTitle_("✓ Copied!")
            
            # Reset button text after 1 second
            import threading
            def reset_button():
                import time
                time.sleep(1)
                try:
                    self.performSelectorOnMainThread_withObject_waitUntilDone_(
                        "resetCopyButton:", None, False
                    )
                except:
                    pass
            
            thread = threading.Thread(target=reset_button)
            thread.daemon = True
            thread.start()
    
    def resetCopyButton_(self, sender):
        """Reset copy button text"""
        self.copy_button.setTitle_("Copy")
    
    def capture_selected_text(self):
        """
        Capture currently selected text from anywhere on macOS.
        Preserves clipboard content before and after.
        
        Returns:
            str: Selected text, or empty string if nothing selected
        """
        import subprocess
        
        # Save current clipboard content
        pasteboard = NSPasteboard.generalPasteboard()
        saved_clipboard = pasteboard.stringForType_("public.utf8-plain-text")
        
        try:
            # Use AppleScript to copy selected text (Cmd+C)
            applescript = '''
            tell application "System Events"
                keystroke "c" using {command down}
            end tell
            '''
            
            # Execute AppleScript
            subprocess.run(['osascript', '-e', applescript], 
                          capture_output=True, 
                          timeout=1)
            
            # Small delay to allow clipboard to update
            import time
            time.sleep(0.1)
            
            # Get the newly copied text
            selected_text = pasteboard.stringForType_("public.utf8-plain-text")
            
            # Restore original clipboard if it was different
            if saved_clipboard and saved_clipboard != selected_text:
                pasteboard.clearContents()
                pasteboard.setString_forType_(saved_clipboard, "public.utf8-plain-text")
            
            # Return empty string if nothing was selected (clipboard unchanged)
            if selected_text == saved_clipboard:
                return ""
            
            return selected_text if selected_text else ""
            
        except Exception as e:
            # Restore clipboard on error
            if saved_clipboard:
                pasteboard.clearContents()
                pasteboard.setString_forType_(saved_clipboard, "public.utf8-plain-text")
            print(f"⚠️ Error capturing selected text: {e}")
            return ""
    
    def screenWithQuery_(self, sender):
        """Auto-capture screen + use query - ONE CLICK!"""
        query = str(self.text_field.string()).strip()
        
        if not query:
            # If no query, just do screen analysis
            self.analyze_screen_with_query("What's on the screen?")
        else:
            # Use the query WITH screen capture automatically
            self.analyze_screen_with_query(query)
    
    def handleQuery_(self, sender):
        """Handle query from text field - WITH AUTO TEXT SELECTION CAPTURE!"""
        query = str(self.text_field.string()).strip()
        
        if not query:
            return
        
        # Show result area and loading message
        self.scroll_view.setHidden_(False)
        self.safe_update_result("📋 Capturing selected text...")
        self.expand_view_for_content(100)
        
        # CAPTURE SELECTED TEXT FROM ANYWHERE ON SCREEN
        selected_text = self.capture_selected_text()
        
        # Check if Screen checkbox is ON
        screen_enabled = self.screen_button.state() == 1
        
        if screen_enabled:
            # User wants screen capture WITH this query
            self.analyze_screen_with_query(query)
        else:
            # Regular query - include selected text if available
            self.text_field.setString_("")
            
            if selected_text:
                # Combine query with selected text
                combined_query = f"{query}\n\n📋 SELECTED TEXT:\n{selected_text}"
                self.safe_update_result(f"🧠 Processing with selected text ({len(selected_text)} chars)...")
                self.process_query_with_context(query, selected_text)
            else:
                # No selected text, process normally
                self.process_query(query)
    
    def expand_view_for_content(self, content_height):
        """Expand the view to fit content"""
        
        # Calculate new total height
        result_height = min(240, max(80, content_height))
        new_total_height = result_height + 70
        
        # Resize scroll view (result area)
        self.scroll_view.setFrame_(NSMakeRect(10, 65, 480, result_height))
        
        # Resize container
        self.input_view.setFrame_(NSMakeRect(0, 0, 500, new_total_height))
    
    def process_query(self, query):
        """Process query - TRY PLUGINS FIRST, then Brain fallback"""
        import threading
        
        # Show loading immediately
        self.result_view.setString_("🧠 Thinking...")
        
        def process_in_background():
            try:
                # STEP 1: Try plugins first - use query as clipboard_text
                from src.plugins.base_plugin import PluginContext
                
                context = PluginContext(
                    clipboard_text=query,  # Treat query as clipboard text
                    content_type="text"
                )
                
                # Get plugin suggestions
                suggestions = self.plugin_manager.get_suggestions(context)
                
                if suggestions:
                    # EXECUTE TOP PLUGIN SUGGESTION
                    top = suggestions[0]
                    self.safe_update_result(f"🔌 {top.title}\n\n{top.description}")
                    
                    # Handle different action types
                    if top.action_type == 'open_url':
                        # Open URL in browser
                        import webbrowser
                        url = top.action_params.get('url')
                        if url:
                            webbrowser.open(url)
                            self.safe_update_result(f"✅ {top.title}\n\n{top.description}\n\n🌐 Opening in browser...")
                        else:
                            self.safe_update_result(f"❌ No URL found in plugin action")
                    
                    elif top.action_type == 'draft_email':
                        # Show email draft
                        draft = top.action_params.get('draft', 'No draft available')
                        self.safe_update_result(f"📧 {top.title}\n\n{draft}")
                    
                    else:
                        # Generic action - just show description
                        result = top.action_params.get('message', top.description)
                        self.safe_update_result(f"✅ {top.title}\n\n{result}")
                
                else:
                    # STEP 2: No plugin matched, use Brain
                    result = self.brain.ask(query, mode="balanced")
                    self.safe_update_result(result)
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
                self.safe_update_result(error_msg)
        
        # Run in background thread so Mac doesn't freeze
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def process_query_with_context(self, query, selected_text):
        """
        Process query with selected text context.
        Combines user question with selected text for better AI responses.
        
        Args:
            query: User's question/request
            selected_text: Text that was selected on screen
        """
        import threading
        
        # Show loading immediately
        self.result_view.setString_("🧠 Analyzing with selected text...")
        
        def process_in_background():
            try:
                # Create enhanced prompt with selected text
                enhanced_prompt = f"""USER QUESTION: {query}

SELECTED TEXT CONTEXT:
{selected_text[:5000]}

Please answer the user's question based on the selected text above. If the question relates to the selected text, use it as context. If not, answer normally but acknowledge what text was selected."""

                # Send to Brain with enhanced context
                result = self.brain.ask(enhanced_prompt, mode="balanced")
                self.safe_update_result(result)
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
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
                            
                            # GENERAL-PURPOSE AI PROMPT - Works for ANY query
                            full_query = f"""USER REQUEST: "{query}"

SCREEN CONTENT:
{extracted_text[:6000]}

Instructions:
1. Read the screen content carefully
2. Understand what the user wants to do based on their request
3. If drafting email/reply: Use EXACT names from screen, write from user's perspective
4. If asking questions: Answer based on BOTH screen content AND your knowledge
5. If analyzing: Provide specific insights from what you see
6. For current/recent events: Use your knowledge up to 2024
7. Be natural, helpful, and context-aware

Respond directly to their request. No templates or placeholders!"""

                            # Use BALANCED model for better understanding
                            result = self.brain.ask(full_query, mode="balanced")
                            
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
