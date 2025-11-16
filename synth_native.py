"""
🎯 SYNTH MENU BAR - NATIVE macOS with Embedded Text Input
Uses PyObjC to create a dropdown with text field embedded directly
"""

import sys
from pathlib import Path
import subprocess
import threading
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
from src.rag.web_search import WebSearchRAG
from src.rag.local_rag import SynthRAG


class CopyableTextView(NSTextView):
    """Custom NSTextView that properly handles copy/paste in menu bars"""
    
    def acceptsFirstResponder(self):
        """Allow this view to become first responder"""
        return True
    
    def becomeFirstResponder(self):
        """Override to ensure we can become first responder"""
        result = objc.super(CopyableTextView, self).becomeFirstResponder()
        return result
    
    def performKeyEquivalent_(self, event):
        """Handle keyboard shortcuts like Cmd+C, Cmd+V, Cmd+A"""
        # Get the modifier flags and key
        modifierFlags = event.modifierFlags()
        characters = event.charactersIgnoringModifiers()
        
        # Check for Command key
        if modifierFlags & (1 << 20):  # NSCommandKeyMask
            if characters == 'c':
                self.copy_(None)
                return True
            elif characters == 'v':
                self.paste_(None)
                return True
            elif characters == 'x':
                self.cut_(None)
                return True
            elif characters == 'a':
                self.selectAll_(None)
                return True
        
        return objc.super(CopyableTextView, self).performKeyEquivalent_(event)
    
    def validateUserInterfaceItem_(self, item):
        """Validate menu items like Copy, Paste, Select All"""
        action = item.action()
        if action in ('copy:', 'paste:', 'selectAll:', 'cut:'):
            return True
        return objc.super(CopyableTextView, self).validateUserInterfaceItem_(item)
    
    def copy_(self, sender):
        """Explicit copy handler - works with Cmd+C"""
        selectedRange = self.selectedRange()
        if selectedRange.length > 0:
            selectedText = self.string()[selectedRange.location:selectedRange.location + selectedRange.length]
        else:
            selectedText = self.string()
        
        if selectedText:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(selectedText, "public.utf8-plain-text")
        return True
    
    def paste_(self, sender):
        """Explicit paste handler - works with Cmd+V"""
        if not self.isEditable():
            return False
        
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            text = pasteboard.stringForType_("public.utf8-plain-text")
            
            if text:
                # Get current selection
                selectedRange = self.selectedRange()
                
                # Replace selected text or insert at cursor
                if self.shouldChangeTextInRange_replacementString_(selectedRange, text):
                    self.replaceCharactersInRange_withString_(selectedRange, text)
                    
                    # Move cursor to end of pasted text
                    newLocation = selectedRange.location + len(text)
                    self.setSelectedRange_((newLocation, 0))
                    
                    # Notify delegate of change
                    self.didChangeText()
                    return True
        except Exception as e:
            print(f"Paste error: {e}")
            # Fallback to simple insert
            try:
                self.insertText_(text if text else "")
            except:
                pass
        
        return False
    
    def selectAll_(self, sender):
        """Select all text - works with Cmd+A"""
        length = len(self.string())
        self.setSelectedRange_((0, length))
        return True
    
    def cut_(self, sender):
        """Cut text - works with Cmd+X"""
        if not self.isEditable():
            return False
        selectedRange = self.selectedRange()
        if selectedRange.length > 0:
            selectedText = self.string()[selectedRange.location:selectedRange.location + selectedRange.length]
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(selectedText, "public.utf8-plain-text")
            self.delete_(sender)
        return True




class SynthMenuBarNative(NSObject):
    """Native macOS menu bar with embedded text input"""
    
    def init(self):
        self = objc.super(SynthMenuBarNative, self).init()
        if self is None:
            return None
        
        # Initialize AI components
        self.brain = DeltaBrain()
        self.screen_capture = ScreenCapture()
        self.web_search = WebSearchRAG()  # Web search (renamed from rag)
        self.rag = SynthRAG()  # Local vector RAG with Qdrant
        
        print(f"🧠 Brain: Connected")
        print(f"🌐 Web Search: Ready") 
        print(f"💾 Local RAG: {self.rag.get_stats()['status']}")
        
        # Initialize Plugin Manager
        print("🔌 Loading plugins...")
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_all_plugins()
        print(f"✅ Loaded {len(self.plugin_manager.plugins)} plugins")
        
        # Clipboard state tracking - stores clipboard text captured by user
        self.captured_clipboard = None  # Text user copied with Cmd+C
        self.clipboard_timestamp = None  # When it was captured
        self.start_clipboard_monitor()  # Monitor for Cmd+C events
        
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
        
        # Text input field - NEW PILL-SHAPED SEARCH BAR (fixes copy/paste)
        self.text_field = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 30, 480, 30))
        self.text_field.setWantsLayer_(True)
        self.text_field.setFocusRingType_(1)  # Use blue focus ring
        
        # CRITICAL: Enable editing and selection for copy/paste
        self.text_field.setEditable_(True)
        self.text_field.setSelectable_(True)
        
        # Style to look modern and pill-shaped
        self.text_field.setBezeled_(False)
        self.text_field.setDrawsBackground_(True)
        self.text_field.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.18, 0.8))
        self.text_field.setTextColor_(NSColor.whiteColor())
        self.text_field.setFont_(NSFont.systemFontOfSize_(15))
        self.text_field.setPlaceholderString_("Search or Ask Synth...")
        
        # Rounded "pill" shape
        self.text_field.layer().setCornerRadius_(15.0)
        
        # Blue border
        self.text_field.layer().setBorderWidth_(2.0)
        self.text_field.layer().setBorderColor_(NSColor.colorWithRed_green_blue_alpha_(0.2, 0.4, 0.8, 0.7).CGColor())
        
        # Set Enter key action
        self.text_field.setTarget_(self)
        self.text_field.setAction_("handleQuery:")

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
        self.input_view.addSubview_(self.text_field)
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
        self.text_field.setStringValue_("")
        self.text_field.setEditable_(True)
        
        # RESET CLIPBOARD STATE - user must do Cmd+C again to capture new text
        self.captured_clipboard = None
        self.clipboard_timestamp = None
        print("🔄 Clipboard state reset - press Cmd+C to capture new text")
        
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
    
    def start_clipboard_monitor(self):
        """Monitor clipboard for Cmd+C events - captures text when user copies"""
        import time
        
        def monitor_clipboard():
            pasteboard = NSPasteboard.generalPasteboard()
            last_change_count = pasteboard.changeCount()
            
            while True:
                try:
                    current_change_count = pasteboard.changeCount()
                    
                    # Clipboard changed - user did Cmd+C!
                    if current_change_count != last_change_count:
                        last_change_count = current_change_count
                        
                        # Get clipboard text
                        clipboard_text = pasteboard.stringForType_("public.utf8-plain-text")
                        
                        if clipboard_text and len(clipboard_text) > 20:
                            # Capture this text - user intentionally copied it
                            self.captured_clipboard = clipboard_text
                            self.clipboard_timestamp = time.time()
                            print(f"📋 Captured clipboard: {len(clipboard_text)} chars")
                    
                    time.sleep(0.5)  # Check every 500ms
                except Exception as e:
                    print(f"Clipboard monitor error: {e}")
                    time.sleep(1)
        
        # Start monitor in background
        monitor_thread = threading.Thread(target=monitor_clipboard, daemon=True)
        monitor_thread.start()
        print("👀 Clipboard monitor started")

    
    def capture_selected_text(self):
        """
        Capture currently selected text from the active application.
        Uses improved AppleScript to get selected text.
        
        Returns:
            str: Selected text from active app, or clipboard text as fallback
        """
        try:
            # Save current clipboard content first
            pasteboard = NSPasteboard.generalPasteboard()
            original_clipboard = pasteboard.stringForType_("public.utf8-plain-text")
            
            # METHOD 1: Try to get selected text using improved AppleScript
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                -- Don't copy if we're the active app
                if frontApp is not "Python" and frontApp is not "Synth" then
                    keystroke "c" using command down
                    delay 0.15
                end if
            end tell
            
            -- Get clipboard content
            set clipboardContent to the clipboard as text
            return clipboardContent
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0 and result.stdout.strip():
                selected_text = result.stdout.strip()
                # Only return if it's different from original clipboard (means new text was selected)
                if selected_text and selected_text != original_clipboard:
                    print(f"✅ Captured selected text: {len(selected_text)} chars")
                    return selected_text
            
            # METHOD 2: Fallback - just read current clipboard
            clipboard_text = pasteboard.stringForType_("public.utf8-plain-text")
            if clipboard_text:
                print(f"📋 Using clipboard text: {len(clipboard_text)} chars")
                return clipboard_text
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Error capturing text: {e}")
            # Final fallback - just read clipboard
            try:
                pasteboard = NSPasteboard.generalPasteboard()
                clipboard_text = pasteboard.stringForType_("public.utf8-plain-text")
                return clipboard_text if clipboard_text else ""
            except:
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
        """Handle query from text field - NOW USES AGENTIC EXECUTION"""
        query = str(self.text_field.stringValue()).strip()
        
        if not query:
            return
        
        # Clear input immediately
        self.text_field.setStringValue_("")
        
        # Show result area
        self.scroll_view.setHidden_(False)
        self.expand_view_for_content(100)
        
        # Show loading immediately
        self.result_view.setString_("🤖 Agent thinking...")
        
        import threading
        
        def process_in_background():
            try:
                # Get selected text if user captured it with Cmd+C
                selected_text = self.captured_clipboard if (self.captured_clipboard and len(self.captured_clipboard) > 20) else None
                
                if selected_text:
                    self.safe_update_result(f"📋 Using captured text ({len(selected_text)} chars)\n🤖 Agent processing...")
                else:
                    self.safe_update_result("🤖 Agent processing query...")
                
                # EXECUTE AGENTIC TASK - this is the new agent logic!
                result = self.brain.execute_agentic_task(query, selected_text)
                
                # Display result
                self.safe_update_result(result)
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
                self.safe_update_result(error_msg)
        
        # Run in background thread so Mac doesn't freeze
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def expand_view_for_content(self, content_height):
        """Expand the view to fit content"""
        
        # Calculate new total height
        result_height = min(240, max(80, content_height))
        new_total_height = result_height + 70
        
        # Resize scroll view (result area)
        self.scroll_view.setFrame_(NSMakeRect(10, 65, 480, result_height))
        
        # Resize container
        self.input_view.setFrame_(NSMakeRect(0, 0, 500, new_total_height))
    
    def needs_web_search(self, query: str) -> bool:
        """
        Determine if a query needs web search (RAG)
        
        Returns True for:
        - Current events, news, elections
        - "What is", "Who is", "When did", "Explain"
        - Recent/latest information
        - Technical concepts, acronyms, standards
        """
        query_lower = query.lower()
        
        # Keywords that ALWAYS trigger web search
        search_keywords = [
            'latest', 'recent', 'current', 'news', 'today', 'yesterday',
            'election', 'politics', 'score', 'weather', 'stock',
            'what is', 'who is', 'when did', 'where is', 'how to',
            'tell me about', 'information about', 'details about',
            'research', 'find', 'search', 'explain', 'define',
            'what are', 'what does', 'why is', 'why did'
        ]
        
        # Check if any keyword is in the query
        for keyword in search_keywords:
            if keyword in query_lower:
                return True
        
        # Check for technical indicators: acronyms, standards, year+technical term
        # e.g., "ML-KEM", "FIPS 203", "2024 NIST"
        words = query.split()
        for word in words:
            # Detect acronyms (2-10 caps letters with optional hyphens/numbers)
            if len(word) >= 2 and any(c.isupper() for c in word) and any(c in word for c in ['-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
                return True
        
        # Long specific questions likely need research
        if len(query.split()) >= 8 and '?' in query:
            return True
            
        return False
    
    def process_query(self, query):
        """Process query from Ask button - ALWAYS checks clipboard for highlighted text"""
        import threading
        
        # Show loading immediately
        self.result_view.setString_("🧠 Thinking...")
        
        def process_in_background():
            try:
                # ASK BUTTON = Use CAPTURED clipboard (from Cmd+C monitoring)
                # Check if user has captured clipboard text (by pressing Cmd+C)
                if self.captured_clipboard and len(self.captured_clipboard) > 20:
                    # User did Cmd+C and we have captured text - use it!
                    clipboard_text = self.captured_clipboard
                    self.safe_update_result(f"📋 Using captured text ({len(clipboard_text)} chars)\n🧠 Analyzing...")
                    
                    enhanced_query = f"""QUESTION: {query}

HIGHLIGHTED TEXT:
{clipboard_text[:4000]}

CRITICAL INSTRUCTIONS:
- Answer ONLY based on the highlighted text above
- Do NOT add external knowledge or explanations beyond what's written
- Keep your answer focused and concise (200-300 words max)
- If the text doesn't contain the answer, say so
- Answer in ENGLISH ONLY

ANSWER:"""
                    
                    result = self.brain.ask(enhanced_query, mode="balanced", max_tokens=400)
                    self.safe_update_result(result)
                    return
                
                # No captured clipboard - continue with normal flow (web search/plugins)
                # Check if query needs web search (RAG)
                if self.needs_web_search(query):
                    self.safe_update_result("🔍 Searching web for latest information...")
                    
                    # Perform web search
                    search_results = self.web_search.search(query, include_news=True)
                    
                    if search_results['sources_count'] > 0:
                        from datetime import datetime
                        current_date = datetime.now().strftime("%B %d, %Y")
                        
                        # Create enhanced prompt with web context
                        enhanced_query = f"""DATE: {current_date}

QUESTION: {query}

WEB SOURCES:
{search_results['context']}

Answer the question using the web sources above. Be accurate and cite key facts.

ANSWER:"""

                        self.safe_update_result(f"✅ Found {search_results['sources_count']} sources. Analyzing...\n\n🧠 Generating answer...")
                        
                        # Send to Brain with web context
                        result = self.brain.ask(enhanced_query, mode="balanced")
                        
                        # Add sources at the end
                        sources_text = "\n\n📚 Sources:\n"
                        for i, res in enumerate(search_results['results'][:5], 1):
                            sources_text += f"{i}. {res.title}\n   {res.source}\n"
                        
                        self.safe_update_result(result + sources_text)
                        return
                    else:
                        # No web results, fall through to plugins/Brain
                        self.safe_update_result("⚠️ No web results found. Using AI knowledge...\n\n")
                
                # STEP 2: Try plugins - use query as clipboard_text
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
                    # STEP 3: No plugin matched, use Brain directly
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
        Process query with clipboard text context.
        NOW WITH RAG: Extracts key terms from BOTH query AND clipboard, searches web!
        
        Args:
            query: User's question/request
            selected_text: Text from clipboard
        """
        import threading
        import re
        
        def process_in_background():
            try:
                # STEP 1: Extract terms to search from BOTH query AND clipboard
                query_lower = query.lower()
                
                # A. Extract specific terms from query (e.g., "what is FIPS 203")
                query_terms_to_search = []
                
                # Pattern: "what is X", "explain X", "define X"
                what_is_match = re.search(r'what\s+is\s+([A-Z0-9\s\-]+?)(?:\?|$|in)', query, re.IGNORECASE)
                if what_is_match:
                    query_terms_to_search.append(what_is_match.group(1).strip())
                
                explain_match = re.search(r'explain\s+([A-Z0-9\s\-]+?)(?:\?|$|in)', query, re.IGNORECASE)
                if explain_match:
                    query_terms_to_search.append(explain_match.group(1).strip())
                
                # B. Extract technical terms from clipboard
                # Pattern 1: All-caps acronyms (BAKE, NIST, ML-KEM)
                acronym_pattern = r'\b[A-Z][A-Z0-9\-]{2,15}\b'
                clipboard_acronyms = list(set(re.findall(acronym_pattern, selected_text)))
                
                # Pattern 2: CAPS + numbers (FIPS 203, ISO 27001)
                caps_num_pattern = r'\b[A-Z]+\s+\d{2,5}\b'
                clipboard_standards = list(set(re.findall(caps_num_pattern, selected_text)))
                
                # Combine all technical terms
                all_technical_terms = query_terms_to_search + clipboard_acronyms + clipboard_standards
                all_technical_terms = list(set([t.strip() for t in all_technical_terms if len(t.strip()) > 1]))
                
                # DON'T add clipboard to RAG - causes pollution
                # We'll use clipboard directly in context instead
                
                # STEP 2: Query RAG for relevant context (from previous knowledge only)
                self.safe_update_result("💾 Searching local knowledge base...")
                rag_result = self.rag.query(query, top_k=3, min_score=0.5)
                
                # Add web search results to RAG too
                self.safe_update_result("🌐 Searching web for additional context...")
                
                # STEP 3: ALWAYS search web if we have technical terms OR explanatory query
                needs_web = (all_technical_terms and len(all_technical_terms) > 0) or \
                           any(word in query_lower for word in ['explain', 'what', 'define', 'meaning', 'describe'])
                
                if needs_web:
                    # FORCE web search for better context
                    terms_preview = ', '.join(all_technical_terms[:5]) if all_technical_terms else query
                    self.safe_update_result(f"🔍 Key terms: {terms_preview}\n🌐 Searching web for latest info...")
                    
                    # Build search terms: prioritize extracted terms
                    all_search_results = []
                    terms_to_search = []
                    
                    # Add query terms first
                    if query_terms_to_search:
                        terms_to_search.extend(query_terms_to_search[:2])
                    
                    # Add clipboard acronyms/standards
                    if clipboard_acronyms:
                        terms_to_search.extend(clipboard_acronyms[:2])
                    if clipboard_standards:
                        terms_to_search.extend(clipboard_standards[:2])
                    
                    # If still empty, use technical terms
                    if not terms_to_search and all_technical_terms:
                        terms_to_search = all_technical_terms[:3]
                    
                    # If STILL empty, use query itself
                    if not terms_to_search:
                        terms_to_search = [query]
                    
                    # Search for each term
                    for term in terms_to_search[:4]:  # Limit to 4 searches
                        try:
                            # Search with context keywords
                            search_query = f"{term} cryptography" if any(word in selected_text.lower() for word in ['crypto', 'security', 'key']) else term
                            search_results = self.web_search.search(search_query, include_news=False)
                            
                            if search_results['sources_count'] > 0:
                                all_search_results.extend(search_results['results'][:2])
                                self.safe_update_result(f"🔍 Searching: {term}\n✓ Found {search_results['sources_count']} sources...")
                        except Exception as e:
                            print(f"Search failed for {term}: {e}")
                    
                    # Build comprehensive context
                    from datetime import datetime
                    current_date = datetime.now().strftime("%B %d, %Y")
                    
                    # Add web results to RAG for future reference
                    if all_search_results:
                        self.rag.add_web_results(all_search_results, query)
                    
                    web_context = ""
                    if all_search_results:
                        web_context = "\n\nWEB SEARCH RESULTS:\n"
                        for i, res in enumerate(all_search_results[:6], 1):
                            web_context += f"{i}. {res.title}\n   {res.snippet[:200]}...\n   Source: {res.source}\n\n"
                    
                    # Build RAG context
                    rag_context = ""
                    if rag_result['has_context']:
                        rag_context = "\n\nKNOWLEDGE BASE:\n"
                        for i, source in enumerate(rag_result['sources'], 1):
                            rag_context += f"[{i}] {source['text'][:200]}... (score: {source['score']:.2f})\n\n"
                    
                    # Create COMPREHENSIVE prompt with RAG + Web + Clipboard
                    enhanced_prompt = f"""CURRENT DATE: {current_date}

QUESTION: {query}

CONTEXT FROM USER'S SELECTED TEXT:
{selected_text[:2500]}
{rag_context}
{web_context}

INSTRUCTIONS:
- Answer the user's question clearly and directly in ENGLISH ONLY
- Use information from ALL sources: selected text, knowledge base, and web search results
- If defining technical terms ({', '.join(all_technical_terms[:3])}), provide clear explanations
- Be comprehensive and complete - aim for 300-500 words
- If using web sources, briefly cite them
- Focus on accuracy and relevance
- DO NOT mix languages - answer entirely in English

ANSWER:"""

                    sources_found = len(all_search_results) + len(rag_result['sources'])
                    self.safe_update_result(f"✅ Found {sources_found} total sources (RAG: {len(rag_result['sources'])}, Web: {len(all_search_results)})\n🧠 Generating comprehensive answer...")
                    
                    # Increase max_tokens for comprehensive answer
                    result = self.brain.ask(enhanced_prompt, mode="balanced", max_tokens=800)
                    
                    # Add sources
                    if all_search_results:
                        sources_text = "\n\n📚 Sources:\n"
                        for i, res in enumerate(all_search_results[:6], 1):
                            sources_text += f"{i}. {res.title} ({res.source})\n"
                        result += sources_text
                    
                    self.safe_update_result(result)
                else:
                    # Simple context query - no web search needed
                    enhanced_prompt = f"""QUESTION: {query}

SELECTED TEXT:
{selected_text[:4000]}

Please answer the question about the selected text above. Be clear, detailed, and accurate. Answer in ENGLISH ONLY.

ANSWER:"""

                    self.safe_update_result("🧠 Analyzing with AI...")
                    result = self.brain.ask(enhanced_prompt, mode="balanced", max_tokens=600)
                    self.safe_update_result(result)
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
                self.safe_update_result(error_msg)
        
        # Run in background thread
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
        """Analyze screen content - ALWAYS captures entire screen, no clipboard"""
        import time
        import threading
        
        def capture_and_analyze():
            try:
                # Screen button = capture ENTIRE screen, NOT clipboard
                # Ask button = use clipboard
                
                # Check if query needs web search BEFORE screen capture
                needs_search = self.needs_web_search(query)
                
                if needs_search:
                    # User wants web search, not screen analysis
                    self.safe_update_result("🔍 This looks like a research question. Searching web instead of screen...")
                    time.sleep(1)
                    
                    # Perform web search
                    search_results = self.web_search.search(query, include_news=True)
                    
                    if search_results['sources_count'] > 0:
                        from datetime import datetime
                        current_date = datetime.now().strftime("%B %d, %Y")
                        
                        # Create enhanced prompt with web context
                        enhanced_query = f"""CURRENT DATE: {current_date}

USER QUESTION: {query}

{search_results['context']}

IMPORTANT: Provide a comprehensive answer based ONLY on the web search results above. Be specific, accurate, and cite key facts."""

                        self.safe_update_result(f"✅ Found {search_results['sources_count']} sources. Analyzing...\n\n🧠 Generating answer...")
                        
                        # Send to Brain with web context
                        result = self.brain.ask(enhanced_query, mode="balanced")
                        
                        # Add sources at the end
                        sources_text = "\n\n📚 Sources:\n"
                        for i, res in enumerate(search_results['results'][:5], 1):
                            sources_text += f"{i}. {res.title} ({res.source})\n"
                        
                        self.safe_update_result(result + sources_text)
                        return
                    else:
                        self.safe_update_result("⚠️ No web results. Analyzing screen instead...\n\n")
                
                # Continue with screen analysis
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
                            
                            # SCREEN ANALYSIS PROMPT
                            full_query = f"""USER REQUEST: "{query}"

SCREEN CONTENT:
{extracted_text[:6000]}

Instructions:
1. The user wants help with what's VISIBLE on their screen
2. If they ask to "explain" or "summarize": Focus on the screen content
3. If they ask to "draft reply": Use names/context from screen
4. Answer their request using the screen content as primary source
5. Keep it natural and helpful
6. Answer in ENGLISH ONLY - no other languages

Respond directly to their request:"""

                            result = self.brain.ask(full_query, mode="balanced", max_tokens=800)
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
