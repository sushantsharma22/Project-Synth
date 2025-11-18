"""
🎯 SYNTH MENU BAR - NATIVE macOS with Embedded Text Input
Uses PyObjC to create a dropdown with text field embedded directly
"""

import warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='PyObjCPointer created')

import sys
from pathlib import Path
import subprocess
import threading
import time
from AppKit import (NSApplication, NSStatusBar, NSMenu, NSMenuItem,
                    NSTextField, NSButton, NSView, NSColor, NSFont,
                    NSNotificationCenter, NSUserNotification, NSUserNotificationCenter,
                    NSTextView, NSScrollView, NSPasteboard, NSApp)
from Foundation import NSObject, NSMakeRect, NSMakeSize
import objc
from typing import Any, cast
from src.brain.tools_gemini import web_search_tavily

# PyObjC objects are dynamically dispatched; cast them to Any for the type
# checker so attribute access (alloc, systemStatusBar, CGColor, etc.) doesn't
# raise static errors in editors like VS Code / Pyright.
NSApplication: Any = NSApplication
NSStatusBar: Any = NSStatusBar
NSMenu: Any = NSMenu
NSMenuItem: Any = NSMenuItem
NSTextField: Any = NSTextField
NSTextView: Any = NSTextView
NSScrollView: Any = NSScrollView
NSButton: Any = NSButton
NSView: Any = NSView
NSColor: Any = NSColor
NSFont: Any = NSFont
NSPasteboard: Any = NSPasteboard
NSApp: Any = NSApp
NSUserNotification: Any = NSUserNotification
NSUserNotificationCenter: Any = NSUserNotificationCenter

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from brain_client import DeltaBrain
from src.senses.screen_capture import ScreenCapture
from src.plugins.plugin_manager import PluginManager
from src.plugins.base_plugin import PluginContext
from src.rag.web_search import WebSearchRAG
from src.rag.local_rag import SynthRAG
from src.ui.chat_manager import ChatManager


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
        text = ""
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


class InputTextView(CopyableTextView):
    """Single-line input view based on CopyableTextView for the search bar.
    This shows a caret inside the menu and handles paste/keyboard properly.
    """
    def insertText_(self, text):
        # Prevent inserting newlines; convert them to spaces
        # Clear placeholder when actual text is inserted
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self._is_placeholder = False
        except Exception:
            pass
        if isinstance(text, str) and '\n' in text:
            text = text.replace('\n', ' ')
        try:
            ret = objc.super(InputTextView, self).insertText_(text)
            # Invoke text change callback if present
            try:
                cb = getattr(self, 'on_text_change_callback', None)
                if cb:
                    cb()
            except Exception:
                pass
            return ret
        except Exception:
            # Fallback - call super on CopyableTextView
            ret = objc.super(CopyableTextView, self).insertText_(text)
            try:
                cb = getattr(self, 'on_text_change_callback', None)
                if cb:
                    cb()
            except Exception:
                pass
            return ret

    def keyDown_(self, event):
        # Called for typing events - clear placeholder if set
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self._is_placeholder = False
        except Exception:
            pass
        # Detect Enter/Return
        try:
            chars = event.characters() if hasattr(event, 'characters') else event.charactersIgnoringModifiers()
        except Exception:
            chars = None
        if chars and (chars == '\r' or chars == '\n'):
            try:
                cb = getattr(self, 'on_enter_callback', None)
                if cb:
                    cb()
                    return None
            except Exception:
                pass
        ret = objc.super(InputTextView, self).keyDown_(event)
        try:
            cb = getattr(self, 'on_text_change_callback', None)
            if cb:
                cb()
        except Exception:
            pass
        return ret

    def setPlaceholder_(self, placeholder):
        # NSTextView doesn't have a native placeholder; we simply use setString_ if it's empty
        try:
            if not self.string() or self.string().strip() == '':
                self.setString_(placeholder)
                # Use a flag to indicate this is placeholder text so it can be cleared on focus
                self._is_placeholder = True
        except Exception:
            pass

    def focusIn_(self, sender):
        # Clear placeholder when focused
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self._is_placeholder = False
        except Exception:
            pass

    def paste_(self, sender):
        # Clear placeholder before pasting
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self._is_placeholder = False
        except Exception:
            pass
        # Call CopyableTextView.paste_ (parent class) for actual paste behavior
        try:
            ret = CopyableTextView.paste_(self, sender)
            try:
                cb = getattr(self, 'on_text_change_callback', None)
                if cb:
                    cb()
            except Exception:
                pass
            return ret
        except Exception:
            return False


class CopyableTextField(NSTextField):
    """Custom NSTextField that handles first responder, caret visibility and keyboard shortcuts inside menu items."""
    def acceptsFirstResponder(self):
        return True

    def becomeFirstResponder(self):
        try:
            return objc.super(CopyableTextField, self).becomeFirstResponder()
        except Exception:
            return False

    def performKeyEquivalent_(self, event):
        """Handle common command key equivalents: copy/paste/cut/select all."""
        modifierFlags = event.modifierFlags()
        characters = event.charactersIgnoringModifiers()

        # 1<<20 is the NSCommandKeyMask in older headers, use it consistently
        if modifierFlags & (1 << 20):
            if characters == 'c':
                # Call the standard copy action (forward to editor if needed)
                try:
                    self.copy_(None)
                except Exception:
                    pass
                return True
            elif characters == 'v':
                try:
                    self.paste_(None)
                except Exception:
                    pass
                return True
            elif characters == 'x':
                try:
                    self.cut_(None)
                except Exception:
                    pass
                return True
            elif characters == 'a':
                try:
                    self.selectAll_(None)
                except Exception:
                    pass
                return True
        return objc.super(CopyableTextField, self).performKeyEquivalent_(event)

    def validateUserInterfaceItem_(self, item):
        action = item.action()
        if action in ('copy:', 'paste:', 'selectAll:', 'cut:'):
            return True
        return objc.super(CopyableTextField, self).validateUserInterfaceItem_(item)


# Note: Removed CompatNSTextField wrapper class - it was blocking becomeFirstResponder calls
# Now using CopyableTextField directly with native NSTextField methods (stringValue/setStringValue_)


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
        
        # Initialize Chat Manager
        self.chat_manager = ChatManager(max_history=50)
        print("💬 Chat manager initialized")
        
        # UI sizing + layout guard rails
        self.default_width = 500
        self.default_result_height = 195
        self.max_result_height = 600  # Increased from 240 to allow scrolling for long content
        self.compact_height = 160  # Increased to fit 6 buttons (2 rows)
        self.current_result_height = self.default_result_height
        self.menu_open = False
        # fallback hook for text change callback when textfield doesn't support attribute writes
        self._text_change_cb = None
        self._enter_cb = None
        
        # Clipboard state tracking - stores clipboard text captured by user
        self.captured_clipboard = None  # Text user copied with Cmd+C
        self.clipboard_timestamp = None  # When it was captured
        self.clipboard_min_chars = 5  # Allow shorter snippets to flow through
        self.clipboard_max_age = 300   # Seconds before clipboard text expires
        self.start_clipboard_monitor()  # Monitor for Cmd+C events
        
        # Create status bar item
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(-1)  # Variable width
        self.statusitem.setTitle_("Synth")
        
        # Create menu
        self.menu = NSMenu.alloc().init()
        self.menu.setDelegate_(self)
        
        # Create custom view with text field
        self.create_input_view()
        
        # Add menu items
        self.build_menu()
        
        # Default to compact view until a result is shown
        self.reset_to_compact_view()
        
        # Set menu to status item
        self.statusitem.setMenu_(self.menu)
        
        return self
    
    def create_input_view(self):
        """Create custom view with embedded text field and result area"""

        # Container view
        self.input_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, self.default_width, 310))
        self.input_view.setWantsLayer_(True)

        # Layout constants
        padding = 10
        inner_width = self.default_width - (padding * 2)  # 480 for default_width 500
        result_view_height = self.default_result_height

        # ============ RESULT VIEW (TOP) - Scrollable output ============
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(padding, 115, inner_width, result_view_height))
        scroll_view.setBorderType_(1)  # Line border
        scroll_view.setDrawsBackground_(True)
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setAutohidesScrollers_(True)
        scroll_view.setAutoresizingMask_(2)

        # Result text view - READ-ONLY, scrollable
        self.result_view = CopyableTextView.alloc().initWithFrame_(NSMakeRect(0, 0, inner_width - 20, result_view_height))
        self.result_view.setEditable_(False)
        self.result_view.setSelectable_(True)
        self.result_view.setRichText_(False)
        self.result_view.setFont_(NSFont.systemFontOfSize_(13))
        self.result_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 0.95))
        self.result_view.setTextColor_(NSColor.whiteColor())
        self.result_view.setAllowsUndo_(False)
        try:
            self.result_view.setAutomaticTextReplacementEnabled_(False)
            self.result_view.setAutomaticQuoteSubstitutionEnabled_(False)
            self.result_view.setAutomaticDashSubstitutionEnabled_(False)
            self.result_view.setAutomaticSpellingCorrectionEnabled_(False)
        except:
            pass
        try:
            # Word wrap
            self.result_view.textContainer().setWidthTracksTextView_(True)
            self.result_view.textContainer().setContainerSize_(NSMakeSize(inner_width - 20, 10000000))
            self.result_view.textContainer().setLineFragmentPadding_(8.0)
        except:
            pass
        scroll_view.setDocumentView_(self.result_view)
        self.scroll_view = scroll_view

        # ============ INPUT TEXT VIEW (MIDDLE) - Editable, scrollable, with cursor! ============
        input_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(padding, 60, inner_width, 50))
        input_scroll.setBorderType_(1)  # Line border
        input_scroll.setDrawsBackground_(True)
        input_scroll.setHasVerticalScroller_(True)
        input_scroll.setHasHorizontalScroller_(False)
        input_scroll.setAutohidesScrollers_(True)
        
        # INPUT TEXT VIEW - This is the key fix! NSTextView instead of NSTextField
        self.input_text_view = InputTextView.alloc().initWithFrame_(NSMakeRect(0, 0, inner_width - 20, 50))
        self.input_text_view.setEditable_(True)
        self.input_text_view.setSelectable_(True)
        self.input_text_view.setRichText_(False)
        self.input_text_view.setFont_(NSFont.systemFontOfSize_(14))
        self.input_text_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.18, 0.98))
        self.input_text_view.setTextColor_(NSColor.whiteColor())
        self.input_text_view.setInsertionPointColor_(NSColor.whiteColor())  # White cursor!
        try:
            self.input_text_view.setAutomaticTextReplacementEnabled_(False)
            self.input_text_view.setAutomaticQuoteSubstitutionEnabled_(False)
        except:
            pass
        try:
            # Word wrap for input
            self.input_text_view.textContainer().setWidthTracksTextView_(True)
            self.input_text_view.textContainer().setContainerSize_(NSMakeSize(inner_width - 20, 10000000))
            self.input_text_view.textContainer().setLineFragmentPadding_(8.0)
        except:
            pass
        
        # Set placeholder
        self.input_text_view.setPlaceholder_("Ask Synth anything...")
        
        # Set callback for Enter key
        self.input_text_view.on_enter_callback = self.handleInputEnter
        
        input_scroll.setDocumentView_(self.input_text_view)
        self.input_scroll = input_scroll

        # ============ 5 BUTTONS (ROW 1) ============
        btn_spacing = 6
        btn_count = 5
        btn_width = int((inner_width - (btn_spacing * (btn_count - 1))) / btn_count)
        btn_y = 32
        
        # Button 1: Ask
        self.ask_button = NSButton.alloc().initWithFrame_(NSMakeRect(padding, btn_y, btn_width, 22))
        self.ask_button.setTitle_("Ask")
        self.ask_button.setBezelStyle_(4)
        self.ask_button.setTarget_(self)
        self.ask_button.setAction_("handleQuery:")
        self.ask_button.setFont_(NSFont.systemFontOfSize_(11))
        
        # Button 2: Agent
        self.agent_button = NSButton.alloc().initWithFrame_(NSMakeRect(padding + (btn_width + btn_spacing) * 1, btn_y, btn_width, 22))
        self.agent_button.setTitle_("🤖 Agent")
        self.agent_button.setBezelStyle_(4)
        self.agent_button.setTarget_(self)
        self.agent_button.setAction_("handleAgentQuery:")
        self.agent_button.setFont_(NSFont.systemFontOfSize_(11))
        
        # Button 3: Screen
        self.screen_button = NSButton.alloc().initWithFrame_(NSMakeRect(padding + (btn_width + btn_spacing) * 2, btn_y, btn_width, 22))
        self.screen_button.setTitle_("📸 Screen")
        self.screen_button.setBezelStyle_(4)
        self.screen_button.setTarget_(self)
        self.screen_button.setAction_("handleScreen:")
        self.screen_button.setFont_(NSFont.systemFontOfSize_(11))
        
        # Button 4: Copy
        self.copy_button = NSButton.alloc().initWithFrame_(NSMakeRect(padding + (btn_width + btn_spacing) * 3, btn_y, btn_width, 22))
        self.copy_button.setTitle_("Copy")
        self.copy_button.setBezelStyle_(4)
        self.copy_button.setTarget_(self)
        self.copy_button.setAction_("copyResults:")
        self.copy_button.setFont_(NSFont.systemFontOfSize_(11))
        
        # Button 5: Clear
        self.clear_button = NSButton.alloc().initWithFrame_(NSMakeRect(padding + (btn_width + btn_spacing) * 4, btn_y, btn_width, 22))
        self.clear_button.setTitle_("Clear")
        self.clear_button.setBezelStyle_(4)
        self.clear_button.setFont_(NSFont.systemFontOfSize_(11))
        self.clear_button.setTarget_(self)
        self.clear_button.setAction_("clearResults:")

        # ============ BUTTON 6 (ROW 2) - CHAT ============
        chat_btn_y = 6
        self.chat_button = NSButton.alloc().initWithFrame_(NSMakeRect(padding, chat_btn_y, inner_width, 22))
        self.chat_button.setTitle_("💬 Chat (with context memory)")
        self.chat_button.setBezelStyle_(4)
        self.chat_button.setTarget_(self)
        self.chat_button.setAction_("handleChat:")
        self.chat_button.setFont_(NSFont.systemFontOfSize_(11))
        
        # Add all views
        self.input_view.addSubview_(scroll_view)
        self.input_view.addSubview_(input_scroll)
        self.input_view.addSubview_(self.ask_button)
        self.input_view.addSubview_(self.agent_button)
        self.input_view.addSubview_(self.screen_button)
        self.input_view.addSubview_(self.copy_button)
        self.input_view.addSubview_(self.clear_button)
        self.input_view.addSubview_(self.chat_button)
        
        # Hidden by default
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

    def menuWillOpen_(self, menu):
        """Ensure layout is compact and prompt focused when the menu opens."""
        self.menu_open = True
        self.prepare_prompt_entry()

    def menuDidClose_(self, menu):
        """Normalize layout when the menu closes so it doesn't reopen huge."""
        self.menu_open = False
        if not str(self.result_view.string()).strip():
            self.reset_to_compact_view()

    def prepare_prompt_entry(self):
        """Shrink layout if empty and focus the text field on the main thread."""
        if not str(self.result_view.string()).strip():
            self.reset_to_compact_view()
        try:
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                "focusTextField:", None, False
            )
        except Exception as exc:
            print(f"⚠️ Unable to schedule prompt focus: {exc}")

    def focusTextField_(self, _):
        """Selector helper that safely focuses the input text view."""
        try:
            window = self.input_text_view.window()
            if window is not None:
                window.makeFirstResponder_(self.input_text_view)
                # Set cursor to end
                try:
                    text_length = len(str(self.input_text_view.string()))
                    self.input_text_view.setSelectedRange_((text_length, 0))
                except Exception:
                    pass
        except Exception as exc:
            print(f"⚠️ Unable to focus input view: {exc}")

    def reset_to_compact_view(self):
        """Hide result pane and shrink container back to compact height."""
        self.scroll_view.setHidden_(True)
        self.current_result_height = 0
        self.input_view.setFrame_(NSMakeRect(0, 0, self.default_width, self.compact_height))
    
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
        """Clear the result area and reset view - also clear the input!"""
        # Clear result area
        self.result_view.setString_("")
        
        # Clear the input text view
        self.input_text_view.setString_("")
        self.input_text_view.setEditable_(True)
        
        # RESET CLIPBOARD STATE - user must do Cmd+C again to capture new text
        self.captured_clipboard = None
        self.clipboard_timestamp = None
        
        # Clear chat history
        self.chat_manager.clear()
        
        print("🔄 Cleared: Clipboard, Results, and Chat History")
        self.reset_to_compact_view()
        
        # Focus back on input so user can type immediately
        self.prepare_prompt_entry()
    
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

                        normalized = clipboard_text.strip() if clipboard_text else ""
                        if normalized and len(normalized) >= self.clipboard_min_chars:
                            # Capture this text - user intentionally copied it
                            self.captured_clipboard = normalized
                            self.clipboard_timestamp = time.time()
                            print(f"📋 Captured clipboard: {len(normalized)} chars")
                    
                    time.sleep(0.5)  # Check every 500ms
                except Exception as e:
                    print(f"Clipboard monitor error: {e}")
                    time.sleep(1)
        
        # Start monitor in background
        monitor_thread = threading.Thread(target=monitor_clipboard, daemon=True)
        monitor_thread.start()
        print("👀 Clipboard monitor started")

    def get_recent_clipboard_text(self):
        """Return recently captured clipboard text that still meets freshness rules."""
        if not self.captured_clipboard:
            return self._read_live_clipboard_fallback()
        text = self.captured_clipboard.strip()
        if len(text) < self.clipboard_min_chars:
            return self._read_live_clipboard_fallback()
        if self.clipboard_timestamp is None:
            return text
        age = time.time() - self.clipboard_timestamp
        if age > self.clipboard_max_age:
            return self._read_live_clipboard_fallback()
        return text

    def _read_live_clipboard_fallback(self):
        """Look directly at the pasteboard in case monitor missed the copy event."""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            live_text = pasteboard.stringForType_("public.utf8-plain-text")
            if live_text:
                normalized = live_text.strip()
                if len(normalized) >= self.clipboard_min_chars:
                    self.captured_clipboard = normalized
                    self.clipboard_timestamp = time.time()
                    print(f"📋 Live clipboard fallback: {len(normalized)} chars")
                    return normalized
        except Exception as exc:
            print(f"⚠️ Live clipboard fallback failed: {exc}")
        return None

    
    def capture_selected_text(self):
        """
        Capture currently selected text from the active application.
        Uses improved AppleScript to get selected text.
        
        Returns:
            str: Selected text from active app, or clipboard text as fallback
        """
        original_clipboard = None
        saved_pasteboard_items = None
        try:
            # Save current clipboard content first (we'll restore it before returning)
            pasteboard = NSPasteboard.generalPasteboard()
            original_clipboard = pasteboard.stringForType_("public.utf8-plain-text")
            # Try to backup all pasteboard types so we can faithfully restore them
            try:
                saved_pasteboard_items = {}
                types = pasteboard.types() or []
                for t in types:
                    try:
                        data = pasteboard.dataForType_(t)
                        if data:
                            saved_pasteboard_items[t] = data
                            continue
                    except Exception:
                        pass
                    try:
                        s = pasteboard.stringForType_(t)
                        if s is not None:
                            saved_pasteboard_items[t] = s
                    except Exception:
                        pass
                if not saved_pasteboard_items:
                    saved_pasteboard_items = None
            except Exception:
                saved_pasteboard_items = None
            
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
                    # Restore the original clipboard so we don't surprise the user
                    try:
                        pasteboard = NSPasteboard.generalPasteboard()
                        pasteboard.clearContents()
                        if saved_pasteboard_items:
                            # Restore all types we captured
                            for k, v in saved_pasteboard_items.items():
                                try:
                                    if isinstance(v, str):
                                        pasteboard.setString_forType_(v, k)
                                    else:
                                        pasteboard.setData_forType_(v, k)
                                except Exception:
                                    # Fall back to plaintext for safety
                                    if original_clipboard:
                                        pasteboard.setString_forType_(original_clipboard, "public.utf8-plain-text")
                                        break
                        elif original_clipboard:
                            pasteboard.setString_forType_(original_clipboard, "public.utf8-plain-text")
                    except Exception as exc:
                        print(f"⚠️ Failed to restore original clipboard: {exc}")
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
        finally:
            # Always restore original clipboard if it was changed by the AppleScript
            try:
                pasteboard = NSPasteboard.generalPasteboard()
                current = pasteboard.stringForType_("public.utf8-plain-text")
                if saved_pasteboard_items:
                    # If we have a backup of items, ensure they are still set; otherwise restore
                    pass  # We restore already in the try-block above
                else:
                    if original_clipboard is None and current is not None:
                        # If we previously had nothing, clear the clipboard
                        pasteboard.clearContents()
                    elif original_clipboard is not None and current != original_clipboard:
                        pasteboard.clearContents()
                        pasteboard.setString_forType_(original_clipboard, "public.utf8-plain-text")
            except Exception:
                # Non-fatal; continue
                pass
    
    def handleInputEnter(self):
        """Handle Enter key in input text view - triggers Ask button"""
        self.handleQuery_(None)
    
    def handleScreen_(self, sender):
        """Handle Screen button"""
        query = str(self.input_text_view.string()).strip()
        
        if not query:
            # If no query, just do screen analysis
            self.analyze_screen_with_query("What's on the screen?")
        else:
            # Use the query WITH screen capture automatically
            self.analyze_screen_with_query(query)
    
    def handleChat_(self, sender):
        """Handle CHAT button - Conversational AI with context memory"""
        query = str(self.input_text_view.string()).strip()
        
        if not query:
            # Show conversation history if no input
            conversation = self.chat_manager.get_full_conversation()
            self.safe_update_result(conversation)
            self.scroll_view.setHidden_(False)
            self.expand_view_for_content(300)
            return
        
        # Clear input
        self.input_text_view.setString_("")
        
        # Show result area
        self.scroll_view.setHidden_(False)
        self.expand_view_for_content(100)
        
        # Add user message to history
        self.chat_manager.add_message('user', query)
        
        # Show loading
        self.result_view.setString_("💬 Chat mode - thinking with full context...")
        
        import threading
        
        def process_chat():
            try:
                # Get conversation context (last 10 messages)
                context = self.chat_manager.get_context(last_n=10)
                
                # Build prompt with context
                from datetime import datetime
                current_time = datetime.now().strftime("%I:%M %p")
                
                prompt = f"""You are Synth, a helpful AI assistant. Current time: {current_time}

{context}

👤 User:
{query}

🤖 Assistant:
Respond naturally and conversationally. Remember the context from earlier messages."""
                
                # Use general_chat for conversational response
                from src.brain.tools_gemini import general_chat
                response = general_chat(prompt)
                
                # Add assistant response to history
                self.chat_manager.add_message('assistant', response)
                
                # Show full conversation
                full_chat = self.chat_manager.get_full_conversation()
                self.safe_update_result(full_chat)
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Chat Error: {str(e)}\n\n{traceback.format_exc()}"
                self.safe_update_result(error_msg)
        
        # Run in background
        thread = threading.Thread(target=process_chat)
        thread.daemon = True
        thread.start()
    
    def handleQuery_(self, sender):
        """Handle ASK button - Simple Q&A with decision router"""
        query = str(self.input_text_view.string()).strip()

        if not query:
            return

        # Clear input immediately
        self.input_text_view.setString_("")

        # Show result area
        self.scroll_view.setHidden_(False)
        self.expand_view_for_content(100)

        # Show loading immediately
        self.result_view.setString_("🤖 Autonomous agent thinking...")

        import threading, re

        def process_in_background():
            try:
                # Check if this is explain/paraphrase and we have captured clipboard
                query_lower = query.lower()
                clipboard_commands = {'explain', 'paraphrase', 'rephrase', 'rewrite', 'summarize', 'show', 'what did i copy'}

                if any(cmd in query_lower for cmd in clipboard_commands):
                    clipboard_text = self.get_recent_clipboard_text()
                    if clipboard_text:
                        print(f"🎯 Using captured clipboard for '{query}': {len(clipboard_text)} chars")

                        # Show clipboard - just echo it back
                        if any(word in query_lower for word in ['show', 'what did i copy', 'clipboard']):
                            result = f"📋 You copied:\n\n{clipboard_text}"
                            self.safe_update_result(result)
                            return

                        # Determine target term (like 'qiskit') for focused explanation
                        def extract_target_sentence(clip_text, token):
                            sents = re.split(r'(?<=[\.\?!])\s+', clip_text)
                            for s in sents:
                                if token.lower() in s.lower():
                                    return s.strip()
                            return None

                        target_term = None
                        m = re.search(r'explain\s+([A-Za-z0-9_\-+.]+)', query_lower)
                        if m:
                            target_term = m.group(1)
                        else:
                            tokens = [re.sub(r'["(),.]', '', t) for t in re.split(r"\s+", query_lower) if len(t) > 2]
                            for t in tokens:
                                if t in clipboard_text.lower():
                                    target_term = t
                                    break

                        if target_term:
                            extracted = extract_target_sentence(clipboard_text, target_term)
                            if extracted:
                                selected_for_explain = extracted
                            else:
                                selected_for_explain = clipboard_text
                        else:
                            selected_for_explain = clipboard_text

                        # Use Decision Router to pick the tool
                        from src.brain.decision_router import decide_tool
                        decision = decide_tool(query, selected_for_explain if selected_for_explain else None)
                        # DEBUG: Decision router returned
                        action = decision.get('action')

                        pass
                        if action == 'local':
                            # Use simplified agent for local actions
                            from src.brain.agent_simple import execute_autonomous as simple_execute
                            result = simple_execute(query)
                            print(f"Model used: LOCAL_AGENT")
                            self.safe_update_result(result)
                            return

                        if action == 'web':
                            # Use callable web search function from tools_gemini (plain function)
                            result = web_search_tavily(query)
                            print(f"Model used: WebSearch (Tavily)")
                            self.safe_update_result(result)
                            return

                        if action == 'llm':
                            # Decide which LLM tool to call
                            tool_key = decision.get('tool')
                            pass
                            if tool_key == 'llm_explain' and selected_for_explain:
                                from src.brain.tools_gemini import explain_text
                                pass
                                from src.brain.tools_gemini import LAST_USED_MODEL
                                # If we found a target term like 'Qiskit' or 'BAKE', pass it so the model focuses on
                                # that term within the provided sentence/clip instead of summarizing the entire paragraph.
                                explanation = explain_text(selected_for_explain, focus_term=target_term)
                                pass
                                print(f"Model used: {LAST_USED_MODEL}")
                                # Do NOT display the model name in the UI; only log it for debugging
                                self.safe_update_result(explanation)
                                pass
                                return
                            if tool_key == 'llm_paraphrase' and selected_for_explain:
                                from src.brain.tools_gemini import paraphrase_text
                                from src.brain.tools_gemini import LAST_USED_MODEL
                                paraphrased = paraphrase_text(selected_for_explain)
                                print(f"Model used: {LAST_USED_MODEL}")
                                self.safe_update_result(paraphrased)
                                return
                            # Default to general chat
                            from src.brain.tools_gemini import general_chat
                            from src.brain.tools_gemini import LAST_USED_MODEL
                            result = general_chat(query)
                            print(f"Model used: {LAST_USED_MODEL}")
                            self.safe_update_result(result)
                            return
                        
                        # Paraphrase/rewrite
                        elif any(word in query_lower for word in ['paraphrase', 'rephrase', 'rewrite']):
                            from src.brain.tools_gemini import paraphrase_text
                            result = paraphrase_text(selected_for_explain)
                            self.safe_update_result(result)
                            return
                        
                        # Summarize
                        elif 'summarize' in query_lower:
                            # Use Gemini for summary
                            from src.brain.tools_gemini import general_chat
                            summary_prompt = f"Summarize this in 2-3 sentences:\n\n{clipboard_text}"
                            result = general_chat(summary_prompt)
                            self.safe_update_result(result)
                            return
                        
                        else:
                            # Let agent handle it
                            result = self.brain.execute_command(query)
                            self.safe_update_result(result)
                            return
                    else:
                        # No clipboard - guide user
                        self.safe_update_result("📋 Please copy some text with Cmd+C first, then ask me to explain/paraphrase it.")
                        return
                
                # AUTONOMOUS AGENT - decides which tools to use
                result = self.brain.execute_command(query)
                
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
    
    def handleAgentQuery_(self, sender):
        """Handle AGENT button - Full autonomous mode with all 41 tools"""
        query = str(self.input_text_view.string()).strip()

        if not query:
            return

        # Clear input immediately
        self.input_text_view.setString_("")

        # Show result area
        self.scroll_view.setHidden_(False)
        self.expand_view_for_content(100)

        # Show loading immediately
        self.result_view.setString_("🤖 Autonomous Agent Mode - Using all 41 tools...\n\nAnalyzing your request...")

        import threading

        def process_in_background():
            try:
                # Use the autonomous agent directly with execute_autonomous
                from src.brain.agent_core import execute_autonomous
                
                self.safe_update_result("🤖 Agent thinking...\n\nUsing: File operations, App control, System monitoring, AI processing, Web search...")
                
                # Execute with autonomous agent (uses LangGraph to pick tools)
                result = execute_autonomous(query, max_retries=2, timeout=90)
                
                # Display result
                self.safe_update_result(result)
                
            except Exception as e:
                import traceback
                error_msg = f"❌ Agent Error: {str(e)}\n\n{traceback.format_exc()}"
                self.safe_update_result(error_msg)
        
        # Run in background thread so Mac doesn't freeze
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def expand_view_for_content(self, content_height):
        """Expand the view to fit content"""
        # Calculate new total height with guard rails
        result_height = min(self.max_result_height, max(80, content_height))
        new_total_height = result_height + 70
        self.current_result_height = result_height
        
        # Resize scroll view (result area)
        self.scroll_view.setHidden_(False)
        self.scroll_view.setFrame_(NSMakeRect(10, 65, 480, result_height))
        
        # Resize container
        self.input_view.setFrame_(NSMakeRect(0, 0, self.default_width, new_total_height))
    
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
                clipboard_text = self.get_recent_clipboard_text()
                if clipboard_text:
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
                    try:
                        from src.brain.tools_gemini import LAST_USED_MODEL
                        print(f"Model used (Ask button): {LAST_USED_MODEL}")
                    except Exception:
                        pass
                    self.safe_update_result(result)
                    return
                elif self.captured_clipboard and not clipboard_text:
                    # Clipboard exists but expired/too short - guide user silently
                    print("⚠️ Captured clipboard text is stale or too short. Waiting for a fresh Cmd+C event.")
                
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
                        try:
                            from src.brain.tools_gemini import LAST_USED_MODEL
                            print(f"Model used (Web RAG): {LAST_USED_MODEL}")
                        except Exception:
                            pass
                        try:
                            from src.brain.tools_gemini import LAST_USED_MODEL
                            print(f"Model used (Web RAG): {LAST_USED_MODEL}")
                        except Exception:
                            pass
                        
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
                    try:
                        from src.brain.tools_gemini import LAST_USED_MODEL
                        print(f"Model used (Fallback): {LAST_USED_MODEL}")
                    except Exception:
                        pass
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
                    # FORCE web search for better context - show brief preview
                    if all_technical_terms:
                        terms_preview = ', '.join(all_technical_terms[:5])
                    else:
                        # Show first 7-8 words of query
                        words = query.split()[:8]
                        terms_preview = ' '.join(words) + ('...' if len(query.split()) > 8 else '')
                    self.safe_update_result(f"🔍 Searching: {terms_preview}...")
                    
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
                                # Just show brief update, not full details
                                term_preview = term[:30] + '...' if len(term) > 30 else term
                                self.safe_update_result(f"🔍 {term_preview}")
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
                    try:
                        from src.brain.tools_gemini import LAST_USED_MODEL
                        print(f"Model used (RAG+Web comprehensive): {LAST_USED_MODEL}")
                    except Exception:
                        pass
                    try:
                        from src.brain.tools_gemini import LAST_USED_MODEL
                        print(f"Model used (RAG+Web): {LAST_USED_MODEL}")
                    except Exception:
                        pass
                    
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
                    try:
                        from src.brain.tools_gemini import LAST_USED_MODEL
                        print(f"Model used (Simple context): {LAST_USED_MODEL}")
                    except Exception:
                        pass
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
            # Calculate height based on text length (optimized for longer content)
            line_count = text.count('\n') + 1
            # Allow more room for longer text, max 600px for scrolling
            text_height = max(80, min(600, line_count * 18 + 40))
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


# Tell the type checker to treat SynthMenuBarNative like Any, so we don't get
# 'alloc' missing attribute errors. This keeps runtime behavior intact.
# (Don't assign the class to Any - use getattr on the class instead when calling dynamic Objective-C alloc/init.)


def main():
    """Main entry point"""
    print("🚀 Starting Synth Menu Bar (Native)...")
    
    # Config - show Gemini fallback status
    from dotenv import load_dotenv
    load_dotenv()
    import os
    fb = os.getenv('GEMINI_FALLBACK_MODELS') or '(default)'
    free_only = os.getenv('GEMINI_FREE_TIER_ONLY', 'true')
    print(f"🔧 Gemini fallback models: {fb}")
    print(f"🔧 Gemini free-tier-only set: {free_only}")

    # Create app
    app = NSApplication.sharedApplication()
    
    # Create menu bar
    synth = getattr(SynthMenuBarNative, 'alloc')().init()
    
    # Run app
    app.run()


if __name__ == "__main__":
    main()
