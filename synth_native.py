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
import atexit
import os
import signal
from AppKit import (NSApplication, NSStatusBar, NSMenu, NSMenuItem,
                    NSTextField, NSButton, NSView, NSColor, NSFont,
                    NSNotificationCenter, NSUserNotification, NSUserNotificationCenter,
                    NSTextView, NSScrollView, NSPasteboard, NSApp, NSBox)
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


# ============================================================================
# SSH TUNNEL MANAGEMENT FOR DELTA BRAIN CONNECTION
# ============================================================================

# Global variable to store SSH tunnel process
ssh_tunnel_process = None
ssh_connection_id = None  # Store SSH username@host for cleanup

def start_ssh_tunnel():
    """
    Start SSH tunnel to Delta Brain in background using credentials from .env
    
    Creates tunnels for all three models:
    - Port 11434: Fast Model (3B)
    - Port 11435: Balanced Model (7B)
    - Port 11436: Smart Model (14B)
    
    Security:
    - Uses credentials from .env file (no hardcoding)
    - Uses sshpass for non-interactive authentication
    - Creates ControlMaster for clean remote cleanup
    """
    global ssh_tunnel_process, ssh_connection_id
    
    # Load credentials from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    ssh_id = os.getenv('SSH_ID')
    ssh_passwd = os.getenv('SSH_PASSWD')
    
    if not ssh_id or not ssh_passwd:
        print("❌ SSH credentials not found in .env file")
        print("   Required: SSH_ID and SSH_PASSWD")
        print("   App will continue with Gemini fallback only")
        return
    
    ssh_connection_id = ssh_id  # Store for cleanup
    
    print("\n" + "="*60)
    print("🔌 STARTING DELTA BRAIN SSH TUNNEL")
    print("="*60)
    print(f"   Using credentials from .env: {ssh_id.split('@')[0]}@***")
    
    # Check if tunnel already exists
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"ssh.*11434.*{ssh_id.split('@')[1]}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("⚠️  SSH tunnel already running (PID: {})".format(result.stdout.strip()))
            print("   Skipping tunnel creation...")
            return
    except Exception:
        pass
    
    # Check if sshpass is installed
    try:
        subprocess.run(["which", "sshpass"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ sshpass not installed - required for automated SSH")
        print("   Install: brew install sshpass")
        print("   App will continue with Gemini fallback only")
        return
    
    # SSH command with sshpass for non-interactive authentication
    # Using ControlMaster for clean remote cleanup
    ssh_command = [
        "sshpass", "-p", ssh_passwd,
        "ssh",
        "-N",  # No remote command
        "-o", "StrictHostKeyChecking=no",  # Auto-accept host key
        "-o", "ServerAliveInterval=30",     # Keep connection alive
        "-o", "ServerAliveCountMax=3",      # Retry 3 times
        "-o", "ControlMaster=auto",         # Enable control socket
        "-o", f"ControlPath=~/.ssh/synth-tunnel-{os.getpid()}",  # Unique socket per app instance
        "-L", "11434:localhost:11434",     # Fast model (3B)
        "-L", "11435:localhost:11435",     # Balanced model (7B)
        "-L", "11436:localhost:11436",     # Smart model (14B)
        ssh_id
    ]
    
    try:
        print("📡 Launching SSH tunnel with sshpass...")
        print(f"   Target: {ssh_id}")
        
        # Start SSH process in background
        ssh_tunnel_process = subprocess.Popen(
            ssh_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group for clean shutdown
        )
        
        print(f"✅ SSH tunnel started (PID: {ssh_tunnel_process.pid})")
        print("   Waiting 3 seconds for connection to establish...")
        
        # Wait for connection to establish
        time.sleep(3)
        
        # Verify tunnel is working by checking ports
        ports_ok = True
        for port in [11434, 11435, 11436]:
            try:
                result = subprocess.run(
                    ["nc", "-z", "localhost", str(port)],
                    capture_output=True,
                    timeout=1
                )
                if result.returncode == 0:
                    print(f"   ✅ Port {port} - Connected")
                else:
                    print(f"   ⚠️  Port {port} - Not responding")
                    ports_ok = False
            except Exception as e:
                print(f"   ⚠️  Port {port} - Check failed: {e}")
                ports_ok = False
        
        if ports_ok:
            print("\n✅ DELTA BRAIN TUNNEL ESTABLISHED")
            print("   Fast (3B):     localhost:11434")
            print("   Balanced (7B): localhost:11435")
            print("   Smart (14B):   localhost:11436")
        else:
            print("\n⚠️  Some ports not responding - tunnel may still be connecting")
            print("   Brain will fall back to Gemini if Delta is unavailable")
        
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Failed to start SSH tunnel: {e}")
        print("   App will continue with Gemini fallback only")
        ssh_tunnel_process = None


def cleanup_tunnel():
    """
    Clean up SSH tunnel on app exit - BOTH on Mac AND Delta
    
    This ensures:
    1. Local SSH process is killed (Mac side) - INCLUDING sshpass parent
    2. Remote control socket is cleaned up (Delta side)
    3. No orphaned processes remain on either system
    """
    global ssh_tunnel_process, ssh_connection_id
    
    if ssh_tunnel_process is None:
        return
    
    print("\n" + "="*60)
    print("🔌 CLEANING UP DELTA BRAIN SSH TUNNEL")
    print("="*60)
    
    # STEP 1: Kill ALL SSH tunnels to Delta (in case sshpass creates orphans)
    try:
        print("📡 Killing all SSH tunnels to Delta (including orphaned processes)...")
        # Use pkill to ensure we get ALL related processes
        subprocess.run(
            ["pkill", "-f", "ssh.*11434.*delta.cs.uwindsor.ca"],
            capture_output=True,
            timeout=5
        )
        print("✅ All SSH tunnel processes killed")
    except subprocess.TimeoutExpired:
        print("⚠️  Process cleanup timed out")
    except Exception as e:
        print(f"⚠️  pkill error: {e}")
    
    # STEP 2: Clean up remote control socket (Delta side)
    if ssh_connection_id:
        try:
            print("📡 Cleaning up remote control socket on Delta...")
            control_path = f"~/.ssh/synth-tunnel-{ssh_tunnel_process.pid}"
            
            # Send exit command through control socket to cleanly close remote end
            subprocess.run(
                ["ssh", "-O", "exit", "-o", f"ControlPath={control_path}", ssh_connection_id],
                capture_output=True,
                timeout=5
            )
            print("✅ Remote control socket cleaned up")
        except subprocess.TimeoutExpired:
            print("⚠️  Remote cleanup timed out (socket may already be closed)")
        except Exception as e:
            print(f"⚠️  Remote cleanup error: {e}")
    
    # STEP 3: Kill local SSH process group (backup cleanup)
    try:
        # Get process group ID
        pgid = os.getpgid(ssh_tunnel_process.pid)
        
        print(f"📡 Terminating process group (PID: {ssh_tunnel_process.pid}, PGID: {pgid})")
        
        # Kill entire process group (handles child processes too)
        os.killpg(pgid, signal.SIGTERM)
        
        # Wait for process to terminate (with timeout)
        try:
            ssh_tunnel_process.wait(timeout=3)
            print("✅ Process group terminated cleanly")
        except subprocess.TimeoutExpired:
            # Force kill if graceful termination fails
            print("⚠️  Graceful termination timed out, forcing...")
            os.killpg(pgid, signal.SIGKILL)
            ssh_tunnel_process.wait()
            print("✅ Process group force-killed")
        
    except ProcessLookupError:
        print("⚠️  Process group already terminated")
    except Exception as e:
        print(f"⚠️  Process group cleanup error: {e}")
    
    # STEP 4: Final verification - ensure no processes remain
    try:
        result = subprocess.run(
            ["pgrep", "-f", "ssh.*11434.*delta.cs.uwindsor.ca"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            remaining_pids = result.stdout.strip().split('\n')
            print(f"⚠️  Found {len(remaining_pids)} remaining processes, force-killing...")
            for pid in remaining_pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"   ✅ Killed PID {pid}")
                except Exception:
                    pass
        else:
            print("✅ No remaining SSH processes found")
    except Exception as e:
        print(f"⚠️  Final verification error: {e}")
    
    # STEP 5: Clean up local control socket file
    try:
        control_path = os.path.expanduser(f"~/.ssh/synth-tunnel-{ssh_tunnel_process.pid}")
        if os.path.exists(control_path):
            os.remove(control_path)
            print("✅ Local control socket file removed")
    except Exception as e:
        print(f"⚠️  Could not remove control socket: {e}")
    
    print("✅ TUNNEL CLEANUP COMPLETE (Mac + Delta)")
    print("="*60 + "\n")
    
    ssh_tunnel_process = None
    ssh_connection_id = None


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
        """Handle keyboard shortcuts for copy/paste/cut/select all"""
        try:
            modifierFlags = event.modifierFlags()
            characters = event.charactersIgnoringModifiers()
            # Command key mask (1 << 20)
            if modifierFlags & (1 << 20):
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
        except Exception as e:
            print(f"Keyboard shortcut error: {e}")
        # Let parent handle other shortcuts
        return objc.super(CopyableTextView, self).performKeyEquivalent_(event)
    
    def validateUserInterfaceItem_(self, item):
        """Validate menu items like Copy, Paste, Select All"""
        action = item.action()
        if action in ('copy:', 'paste:', 'selectAll:', 'cut:'):
            return True
        return objc.super(CopyableTextView, self).validateUserInterfaceItem_(item)
    
    def copy_(self, sender):
        """Handle copy in menu bar context"""
        try:
            selectedRange = self.selectedRange()
            
            # Get selected text or all text
            if selectedRange.length > 0:
                text = self.string()[selectedRange.location:selectedRange.location + selectedRange.length]
            else:
                text = self.string()
            
            if text:
                # Access pasteboard directly
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                
                # Try both type strings for compatibility
                success = pasteboard.setString_forType_(text, "public.utf8-plain-text")
                if not success:
                    pasteboard.setString_forType_(text, "NSStringPboardType")
                
                print(f"✅ Copied {len(text)} chars to clipboard")
                return True
            else:
                print("⚠️ No text to copy")
                return False
                
        except Exception as e:
            print(f"❌ Copy error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def paste_(self, sender):
        """Handle paste in menu bar context - bypasses window responder chain"""
        try:
            # Get pasteboard directly (works in menu bars)
            pasteboard = NSPasteboard.generalPasteboard()
            text = pasteboard.stringForType_("public.utf8-plain-text")
            
            if not text:
                # Try alternate type
                text = pasteboard.stringForType_("NSStringPboardType")
            
            if text:
                # Clear placeholder
                if getattr(self, '_is_placeholder', False):
                    self.setString_("")
                    self._is_placeholder = False
                
                # Insert text at cursor position
                selectedRange = self.selectedRange()
                
                # Use insertText_ which ALWAYS works (even in menus)
                self.insertText_(text)
                
                # Trigger callback
                try:
                    cb = getattr(self, 'on_text_change_callback', None)
                    if cb:
                        cb()
                except:
                    pass
                
                print(f"✅ Pasted {len(text)} chars")
                return True
            else:
                print("⚠️ No text in clipboard")
                return False
                
        except Exception as e:
            print(f"❌ Paste error: {e}")
            import traceback
            traceback.print_exc()
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
    def menuForEvent_(self, event):
        """Show right-click context menu with Copy/Paste/Select All"""
        menu = NSMenu.alloc().init()
        # Copy
        copy_item = menu.addItemWithTitle_action_keyEquivalent_("Copy", "copy:", "")
        copy_item.setTarget_(self)
        # Paste
        paste_item = menu.addItemWithTitle_action_keyEquivalent_("Paste", "paste:", "")
        paste_item.setTarget_(self)
        # Select All
        select_item = menu.addItemWithTitle_action_keyEquivalent_("Select All", "selectAll:", "")
        select_item.setTarget_(self)
        return menu
    """Single-line input view based on CopyableTextView for the search bar.
    This shows a caret inside the menu and handles paste/keyboard properly.
    """
    def insertText_(self, text):
        """Insert text and FORCE cursor to stay visible"""
        # Clear placeholder when actual text is inserted
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self._is_placeholder = False
        except Exception:
            pass
        # Prevent inserting newlines; convert them to spaces
        if isinstance(text, str) and '\n' in text:
            text = text.replace('\n', ' ')
        try:
            # Call parent to insert text
            ret = objc.super(InputTextView, self).insertText_(text)
            # ⭐ CRITICAL: Force cursor to stay visible after text insertion
            try:
                self.updateInsertionPointStateAndRestartTimer_(True)
                self.setNeedsDisplay_(True)
            except:
                pass
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
            # ⭐ Force cursor update in fallback too
            try:
                self.updateInsertionPointStateAndRestartTimer_(True)
                self.setNeedsDisplay_(True)
            except:
                pass
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
        """Simplified paste - let parent class handle it"""
        # Clear placeholder before pasting
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self._is_placeholder = False
        except:
            pass
        # Call parent's paste method (CopyableTextView)
        result = objc.super(InputTextView, self).paste_(sender)
        # Trigger callback
        try:
            cb = getattr(self, 'on_text_change_callback', None)
            if cb:
                cb()
        except:
            pass
        return result


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
        
        # Chat Mode State
        self.chat_mode_active = False
        
        # UI sizing + layout guard rails
        self.default_width = 500
        self.default_result_height = 195
        self.max_result_height = 700  # Increased to 700px for longer conversations
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
        # Border color used for both the result and input containers
        border_color = NSColor.colorWithRed_green_blue_alpha_(0.45, 0.45, 0.50, 0.8)

        # ============ RESULT VIEW (TOP) - Scrollable output ============
        # Use NSBox for border, with scroll_view inside
        border_box = NSBox.alloc().initWithFrame_(NSMakeRect(padding, 130, inner_width, result_view_height))
        border_box.setBoxType_(4)  # NSBoxCustom
        border_box.setBorderType_(1)  # NSLineBorder
        border_box.setBorderWidth_(1.5)
        border_box.setBorderColor_(border_color)
        border_box.setCornerRadius_(10.0)
        border_box.setFillColor_(NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 1.0))

        # Create scroll view INSIDE the border box
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, inner_width, result_view_height))
        scroll_view.setBorderType_(0)  # No border
        scroll_view.setDrawsBackground_(True)
        scroll_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 1.0))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setAutohidesScrollers_(False)
        scroll_view.setScrollerStyle_(1)
        scroll_view.setVerticalScrollElasticity_(1)
        scroll_view.setAutoresizingMask_(2)

        # Result text view - READ-ONLY, scrollable
        self.result_view = CopyableTextView.alloc().initWithFrame_(NSMakeRect(0, 0, inner_width - 20, result_view_height))
        self.result_view.setEditable_(False)
        self.result_view.setSelectable_(True)
        self.result_view.setRichText_(False)
        mono_font = NSFont.monospacedSystemFontOfSize_weight_(12, 0)
        self.result_view.setFont_(mono_font)
        try:
            text_storage = self.result_view.textStorage()
            full_range = (0, text_storage.length())
            text_storage.addAttribute_value_range_("NSFont", mono_font, full_range)
        except:
            pass
        self.result_view.textContainer().setLineFragmentPadding_(2.0)
        self.result_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 1.0))
        self.result_view.setTextColor_(NSColor.whiteColor())
        self.result_view.setAllowsUndo_(False)
        self.result_view.setVerticallyResizable_(True)
        self.result_view.setHorizontallyResizable_(False)
        try:
            self.result_view.setUsesFontPanel_(False)
            self.result_view.setUsesLigatures_(False)
            self.result_view.setImportsGraphics_(False)
            self.result_view.setAutomaticTextReplacementEnabled_(False)
            self.result_view.setAutomaticQuoteSubstitutionEnabled_(False)
        except:
            pass
        try:
            self.result_view.setAutomaticDashSubstitutionEnabled_(False)
            self.result_view.setAutomaticSpellingCorrectionEnabled_(False)
            self.result_view.setGrammarCheckingEnabled_(False)
        except:
            pass
        try:
            self.result_view.textContainer().setWidthTracksTextView_(True)
            self.result_view.textContainer().setContainerSize_(NSMakeSize(inner_width - 20, 10000000))
        except:
            pass
        # Add bottom padding so last line is visible
        self.result_view.setTextContainerInset_(NSMakeSize(5, 15))  # 5px horizontal, 15px bottom padding
        scroll_view.setDocumentView_(self.result_view)
        border_box.setContentView_(scroll_view)
        self.scroll_view = scroll_view
        self.scroll_border_box = border_box

        # ============ INPUT TEXT VIEW (MIDDLE) - Editable, direct view (NO scroll wrapper) ============
        input_container_height = 50
        input_container_y = 65
        input_container = NSView.alloc().initWithFrame_(NSMakeRect(padding, input_container_y, inner_width, input_container_height))
        input_container.setWantsLayer_(True)
        try:
            input_container.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.17, 1.0).CGColor())
            input_container.layer().setBorderWidth_(1.5)
            input_container.layer().setBorderColor_(border_color.CGColor())
            input_container.layer().setCornerRadius_(10.0)
            input_container.layer().setMasksToBounds_(True)
        except:
            pass
        input_padding = 8
        self.input_text_view = InputTextView.alloc().initWithFrame_(NSMakeRect(input_padding, input_padding, inner_width - (input_padding * 2), input_container_height - (input_padding * 2)))
        self.input_text_view.setEditable_(True)
        self.input_text_view.setSelectable_(True)
        self.input_text_view.setRichText_(False)
        self.input_text_view.setFont_(NSFont.fontWithName_size_("Menlo", 13))
        self.input_text_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.15, 0.15, 0.17, 1.0))
        self.input_text_view.setTextColor_(NSColor.whiteColor())
        self.input_text_view.setInsertionPointColor_(NSColor.whiteColor())
        try:
            self.input_text_view.setInsertionPointWidth_(3.0)
        except:
            pass
        self.input_text_view.setDrawsBackground_(True)
        try:
            self.input_text_view.setAutomaticTextReplacementEnabled_(False)
            self.input_text_view.setAutomaticQuoteSubstitutionEnabled_(False)
        except:
            pass
        try:
            self.input_text_view.textContainer().setWidthTracksTextView_(True)
            self.input_text_view.textContainer().setContainerSize_(NSMakeSize(inner_width - 20, 10000000))
            self.input_text_view.textContainer().setLineFragmentPadding_(4.0)
        except:
            pass
        self.input_text_view.setPlaceholder_("Ask Synth anything...")
        self.input_text_view.on_enter_callback = self.handleInputEnter
        input_container.addSubview_(self.input_text_view)
        self.input_container = input_container

        def handleQuery_(self, sender):
            """Handle ASK button - Fast intelligent agent with Live Tools"""
            query = str(self.input_text_view.string()).strip()
            if not query:
                return
            self.scroll_border_box.setHidden_(False)
            self.expand_view_for_content(100)
            self.safe_update_result("💭 Analyzing query...")
            import threading, time, traceback
            def process_in_background():
                from utils.ask_button_logger import get_logger
                logger = get_logger()
                start_time = time.time()
                logger.log_query(query)
                try:
                    clipboard_text = self.get_recent_clipboard_text()
                    if clipboard_text:
                        logger.log_event("CLIPBOARD_CONTEXT", {"length": len(clipboard_text)})
                        self.safe_update_result(f"� Using clipboard ({len(clipboard_text)} chars) | 🤖 Processing...")
                    from src.brain.agent_modes import ask_mode_agent
                    def log_event_callback(event_type, data):
                        logger.log_event(event_type, data)
                    response = ask_mode_agent(
                        query,
                        clipboard_text=None,
                        progress_callback=lambda msg: self.safe_update_result(msg),
                        log_callback=log_event_callback
                    )
                    total_time = time.time() - start_time
                    logger.log_response(response)
                    logger.log_timing("total", total_time)
                    self.safe_update_result(response + f"\n\n⏱️ Completed in {total_time:.1f}s")
                    print(f"✅ Ask mode completed in {total_time:.1f}s")
                except Exception as e:
                    error_msg = str(e)
                    tb = traceback.format_exc()
                    logger.log_error(error_msg, tb)
                    total_time = time.time() - start_time
                    logger.log_timing("total_failed", total_time)
                    friendly_error = f"""❌ Error: {error_msg[:200]}

    Something went wrong. Please try again or rephrase your question.

    Log file: logs/ask_button/ask_session_*.log"""
                    self.safe_update_result(friendly_error)
                    print(f"❌ Error:\n{tb}")
            thread = threading.Thread(target=process_in_background)
            thread.daemon = True
            thread.start()
        
        try:
            self.input_text_view.setAutomaticTextReplacementEnabled_(False)
            self.input_text_view.setAutomaticQuoteSubstitutionEnabled_(False)
        except:
            pass
        
        try:
            # Word wrap for input
            self.input_text_view.textContainer().setWidthTracksTextView_(True)
            self.input_text_view.textContainer().setContainerSize_(NSMakeSize(inner_width - 20, 10000000))  # Match result_view width
            self.input_text_view.textContainer().setLineFragmentPadding_(4.0)  # Balanced spacing
        except:
            pass
        
        # Set placeholder
        self.input_text_view.setPlaceholder_("Ask Synth anything...")
        
        # Set callback for Enter key
        self.input_text_view.on_enter_callback = self.handleInputEnter
        
        # Add input to container
        input_container.addSubview_(self.input_text_view)
        # Ensure input is editable and selectable
        self.input_text_view.setEditable_(True)
        self.input_text_view.setSelectable_(True)
        # Enable standard edit menu and proper text handling
        self.input_text_view.setUsesFontPanel_(True)  # Allow font changes
        self.input_text_view.setRichText_(False)  # Keep plain text
        # ⭐ CRITICAL: Enable automatic menu items for copy/paste
        try:
            self.input_text_view.setAutomaticTextCompletionEnabled_(False)
            self.input_text_view.setAutomaticLinkDetectionEnabled_(False)
        except:
            pass
        # Force acceptsFirstResponder to always return True
        def custom_accepts_first_responder():
            return True
        self.input_text_view.acceptsFirstResponder = custom_accepts_first_responder

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
        self.chat_button.setTitle_("💬 Chat")
        self.chat_button.setBezelStyle_(4)
        self.chat_button.setTarget_(self)
        self.chat_button.setAction_("toggleChatMode:")  # FIXED: Toggle mode, not send message
        self.chat_button.setFont_(NSFont.systemFontOfSize_(11))
        
        # Add all views
        self.input_view.addSubview_(border_box)
        self.input_view.addSubview_(input_container)
        self.input_view.addSubview_(self.ask_button)
        self.input_view.addSubview_(self.agent_button)
        self.input_view.addSubview_(self.screen_button)
        self.input_view.addSubview_(self.copy_button)
        self.input_view.addSubview_(self.clear_button)
        self.input_view.addSubview_(self.chat_button)

        # Hidden by default
        self.scroll_border_box.setHidden_(True)
    
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
                # CRITICAL: Make window key FIRST
                window.makeKeyAndOrderFront_(None)
                # Then make input first responder
                success = window.makeFirstResponder_(self.input_text_view)
                if success:
                    # Move cursor to end
                    try:
                        text_length = len(str(self.input_text_view.string()))
                        self.input_text_view.setSelectedRange_((text_length, 0))
                        print("✅ Input view is first responder")
                    except Exception:
                        pass
                else:
                    print("⚠️ Failed to make input view first responder")
                    # Force it anyway
                    self.input_text_view.becomeFirstResponder()
        except Exception as exc:
            print(f"⚠️ Unable to focus input view: {exc}")

    def reset_to_compact_view(self):
        """Hide result pane and shrink container back to compact height."""
        self.scroll_border_box.setHidden_(True)
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
            self.scroll_border_box.setHidden_(False)
            self.expand_view_for_content(200)
        else:
            self.safe_update_result(f"❌ Plugin '{plugin_name}' not found")
    
    def clearResults_(self, sender):
        """Clear the result area and reset view - but keep input text!"""
        # Clear result area
        self.result_view.setString_("")
        
        # DON'T clear input - let user edit or reuse it!
        # self.input_text_view.setString_("")  # REMOVED - keep text for editing
        self.input_text_view.setEditable_(True)
        
        # RESET CLIPBOARD STATE - user must do Cmd+C again to capture new text
        self.captured_clipboard = None
        self.clipboard_timestamp = None
        
        # Clear chat history
        self.chat_manager.clear()
        
        # Show appropriate message based on mode
        if self.chat_mode_active:
            self.safe_update_result("💬 Chat Mode Active\n\nConversation cleared. Start a new conversation...")
            self.scroll_border_box.setHidden_(False)
            self.expand_view_for_content(100)
        else:
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
        """Handle Enter key in input text view - routes based on chat mode"""
        if self.chat_mode_active:
            # In chat mode: Enter sends message AND CLEARS INPUT
            self.handleChat_(None)
        else:
            # Normal mode: Enter triggers Ask button (input stays for editing)
            self.handleQuery_(None)
    
    
    def toggleChatMode_(self, sender):
        """Toggle Chat Mode ON/OFF - COMPLETE IMPLEMENTATION"""
        self.chat_mode_active = not self.chat_mode_active
        
        if self.chat_mode_active:
            # ═══════ ACTIVATE CHAT MODE ═══════
            # Change button text
            self.chat_button.setTitle_("💬 Chat Mode (ON)")
            
            # Disable other buttons (Ask/Agent/Screen)
            self.ask_button.setEnabled_(False)
            self.agent_button.setEnabled_(False)
            self.screen_button.setEnabled_(False)
            
            # Change background to darker blue tint (chat mode indicator)
            chat_bg_color = NSColor.colorWithRed_green_blue_alpha_(0.15, 0.18, 0.25, 0.98)
            chat_result_bg = NSColor.colorWithRed_green_blue_alpha_(0.15, 0.18, 0.25, 0.95)
            
            self.input_text_view.setBackgroundColor_(chat_bg_color)
            self.result_view.setBackgroundColor_(chat_result_bg)
            
            # Show chat mode message with clear instructions
            welcome_msg = """💬 Chat Mode Active

Ask me anything! I'll remember our conversation.

✨ Features:
• 🔍 Automatic web search for current events & news
• 💭 Conversation memory (last 10 messages for context)
• 📚 Sources cited when using web search
• ⚡ Press Enter to send messages

📝 Tips:
• Ask follow-up questions - I remember what we discussed
• Request latest news/polls/updates for automatic web search
• Click 'Chat Mode (ON)' button to exit chat mode

Ready to chat! What would you like to know?"""
            
            self.safe_update_result(welcome_msg)
            self.scroll_view.setHidden_(False)
            self.expand_view_for_content(250)
            
            print("✅ Chat Mode ACTIVATED - Web search enabled, conversation memory active")
            
        else:
            # ═══════ DEACTIVATE CHAT MODE ═══════
            # Restore button text
            self.chat_button.setTitle_("💬 Chat")
            
            # Re-enable other buttons
            self.ask_button.setEnabled_(True)
            self.agent_button.setEnabled_(True)
            self.screen_button.setEnabled_(True)
            
            # Restore original background colors
            normal_input_bg = NSColor.colorWithRed_green_blue_alpha_(0.15, 0.16, 0.18, 0.98)
            normal_result_bg = NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.12, 0.95)
            
            self.input_text_view.setBackgroundColor_(normal_input_bg)
            self.result_view.setBackgroundColor_(normal_result_bg)
            
            # Show exit message
            exit_msg = """✅ Exited Chat Mode

Returned to normal mode.

💾 Your chat history is preserved until you click Clear.

Use the buttons below for:
• Ask - Simple Q&A
• Agent - Autonomous actions
• Screen - Screen analysis"""
            
            self.safe_update_result(exit_msg)
            self.scroll_view.setHidden_(False)
            self.expand_view_for_content(150)
            
            print("❌ Chat Mode DEACTIVATED - Returned to normal mode")
        
        # Focus input field
        self.prepare_prompt_entry()
    
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
        """Handle CHAT in chat mode - Same as ASK but with conversation memory
        
        CHAT MODE = ASK MODE + CONVERSATION CONTEXT
        - Uses all tools (weather, web search, definitions, etc.)
        - Intelligent routing via ask_mode_agent
        - Remembers previous conversation
        - Logs to logs/chat_button/
        """
        query = str(self.input_text_view.string()).strip()
        
        if not query:
            # Show conversation history if no input
            conversation = self.chat_manager.get_full_conversation()
            self.safe_update_result(conversation)
            self.scroll_border_box.setHidden_(False)
            self.expand_view_for_content(300)
            return
        
        # CHAT MODE: Clear input immediately so user can type next message
        self.input_text_view.setString_("")
        
        # Show result area
        self.scroll_view.setHidden_(False)
        self.expand_view_for_content(100)
        
        # Add user message to history
        from datetime import datetime
        self.chat_manager.add_message('user', query)
        
        # Show immediate progress
        current_time = datetime.now().strftime("%I:%M:%S %p")
        loading_msg = f"💬 Chat Mode\n\n[{current_time}] 👤 You:\n{query}\n\n"
        self.safe_update_result(loading_msg + "💭 Processing...")
        
        import threading
        import time as time_module
        
        def process_chat():
            from datetime import datetime
            import json
            import os
            import traceback
            
            # Create chat log directory
            log_dir = "logs/chat_button"
            os.makedirs(log_dir, exist_ok=True)
            
            # Create session log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"chat_session_{timestamp}.log")
            
            def log_event(event: str, data: dict):
                """Log events to file"""
                try:
                    with open(log_file, 'a') as f:
                        entry = {
                            "timestamp": datetime.now().isoformat(),
                            "event": event,
                            "data": data
                        }
                        f.write(json.dumps(entry) + "\n")
                except Exception as e:
                    print(f"⚠️ Logging error: {e}")
            
            try:
                # Log session start
                log_event("SESSION_START", {"timestamp": datetime.now().isoformat()})
                log_event("QUERY", {"query": query})
                
                # Get conversation context (last 10 messages for efficiency)
                context = self.chat_manager.get_context(last_n=10)
                log_event("CONVERSATION_CONTEXT", {"length": len(context)})
                
                # Import ask_mode_agent function
                from src.brain.agent_modes import ask_mode_agent
                
                # Use ask_mode_agent with ORIGINAL query for routing
                # Context is stored in chat history, not needed for tool selection
                print(f"💬 Chat mode - routing with original query: {query}")
                
                # Progress callback
                def progress_cb(msg):
                    self.safe_update_result(loading_msg + msg)
                    print(f"📊 {msg}")
                
                # Logging callback
                def log_cb(event, data):
                    log_event(event, data)
                    if event == "TOOL_SELECTED":
                        print(f"🔧 Tool: {data.get('tool_name', 'unknown')}")
                
                response = ask_mode_agent(
                    query,  # Use ORIGINAL query for proper tool routing!
                    None,  # No clipboard for chat mode
                    progress_cb,
                    log_cb
                )
                
                # Clean up response
                response = response.strip()
                if response.startswith("🤖"):
                    response = response[1:].strip()
                
                # Add assistant response to history
                self.chat_manager.add_message('assistant', response)
                log_event("RESPONSE", {
                    "response_length": len(response),
                    "response_preview": response[:200]
                })
                
                # Build conversation display (last 20 messages)
                conversation_display = "💬 Chat Mode\n\n"
                
                messages_to_show = self.chat_manager.messages[-20:] if len(self.chat_manager.messages) > 20 else self.chat_manager.messages
                
                if len(self.chat_manager.messages) > 20:
                    conversation_display += f"(Showing last 20 of {len(self.chat_manager.messages)} messages)\n\n"
                
                # Build conversation
                for msg in messages_to_show:
                    time_str = msg.timestamp.strftime("%I:%M:%S %p")
                    if msg.role == 'user':
                        conversation_display += f"[{time_str}] 👤 You:\n{msg.content}\n\n"
                    else:
                        conversation_display += f"[{time_str}] 🤖 Synth:\n{msg.content}\n\n"
                
                # Display
                self.safe_update_result(conversation_display)
                
                # Log timing
                log_event("TIMING", {"stage": "total", "message": "Chat completed"})
                
                # Single scroll to bottom after display
                time_module.sleep(0.05)
                try:
                    self.performSelectorOnMainThread_withObject_waitUntilDone_(
                        "forceScrollToBottom:", None, False
                    )
                except:
                    pass
                
            except Exception as e:
                error_msg = f"❌ Chat Error: {str(e)[:200]}\n\nPlease try again."
                
                try:
                    current_conversation = self.chat_manager.get_full_conversation()
                    error_msg = current_conversation + "\n\n" + error_msg
                except:
                    pass
                
                self.safe_update_result(error_msg)
                print(f"❌ Full error:\n{traceback.format_exc()}")
                
                # Log error
                log_event("ERROR", {"error": str(e), "traceback": traceback.format_exc()})
        
        # Run in background
        thread = threading.Thread(target=process_chat)
        thread.daemon = True
        thread.start()
    
    def handleQuery_(self, sender):
        """Handle ASK button - Fast intelligent agent with Live Tools
        
        NEW STREAMLINED IMPLEMENTATION:
        - Uses ask_mode_agent with ASK_TOOLS (12 safe, read-only tools)
        - Intelligent tool selection based on query keywords
        - Fast: 1-5 seconds for Live Tools, 5-15s for web search
        - Full logging to logs/ask_button/ask_session_TIMESTAMP.log
        """
        query = str(self.input_text_view.string()).strip()
        if not query:
            return

        # DON'T clear input - let user see and edit it!
        # self.input_text_view.setString_("")  # REMOVED - keep text for editing

        # Show result area
        self.scroll_border_box.setHidden_(False)
        self.expand_view_for_content(100)

        # Show loading immediately
        self.safe_update_result("💭 Analyzing query...")

        import threading
        import time
        import traceback

        def process_in_background():
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Initialize Logger
            # ═══════════════════════════════════════════════════════════
            from utils.ask_button_logger import get_logger
            logger = get_logger()

            start_time = time.time()
            logger.log_query(query)

            try:
                # ═══════════════════════════════════════════════════════════
                # STEP 2: Get Context (clipboard if available)
                # ═══════════════════════════════════════════════════════════
                clipboard_text = self.get_recent_clipboard_text()

                if clipboard_text:
                    logger.log_event("CLIPBOARD_CONTEXT", {"length": len(clipboard_text)})
                    self.safe_update_result(f"� Using clipboard ({len(clipboard_text)} chars) | 🤖 Processing...")

                # ═══════════════════════════════════════════════════════════
                # STEP 3: Execute Agent (replaces all routing logic)
                # ═══════════════════════════════════════════════════════════
                from src.brain.agent_modes import ask_mode_agent

                # Define log callback for detailed events
                def log_event_callback(event_type, data):
                    logger.log_event(event_type, data)

                response = ask_mode_agent(
                    query,
                    clipboard_text=None,  # ASK MODE = NO MEMORY!
                    progress_callback=lambda msg: self.safe_update_result(msg),
                    log_callback=log_event_callback  # NEW: Detailed logging!
                )

                # ═══════════════════════════════════════════════════════════
                # STEP 4: Log Success
                # ═══════════════════════════════════════════════════════════
                total_time = time.time() - start_time

                logger.log_response(response)
                logger.log_timing("total", total_time)

                # ═══════════════════════════════════════════════════════════
                # STEP 5: Update UI
                # ═══════════════════════════════════════════════════════════
                self.safe_update_result(response + f"\n\n⏱️ Completed in {total_time:.1f}s")
                print(f"✅ Ask mode completed in {total_time:.1f}s")

            except Exception as e:
                # ═══════════════════════════════════════════════════════════
                # STEP 6: Error Handling (preserve logging)
                # ═══════════════════════════════════════════════════════════
                error_msg = str(e)
                tb = traceback.format_exc()
                logger.log_error(error_msg, tb)

                total_time = time.time() - start_time
                logger.log_timing("total_failed", total_time)

                friendly_error = f"""❌ Error: {error_msg[:200]}

Something went wrong. Please try again or rephrase your question.

Log file: logs/ask_button/ask_session_*.log"""

                self.safe_update_result(friendly_error)
                print(f"❌ Error:\n{tb}")

        # Run in background thread so Mac doesn't freeze
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def handleAgentQuery_(self, sender):
        """Handle AGENT button - Full autonomous mode with all 41 tools"""
        query = str(self.input_text_view.string()).strip()

        if not query:
            return

        # DON'T clear input - let user see and edit it!
        # self.input_text_view.setString_("")  # REMOVED - keep text for editing

        # Show result area
        self.scroll_border_box.setHidden_(False)
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
        self.scroll_border_box.setHidden_(False)
        self.scroll_border_box.setFrame_(NSMakeRect(10, 65, 480, result_height))
        
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
            # ⭐ FORCE MONOSPACE FONT AFTER TEXT UPDATE ⭐
            mono_font = NSFont.monospacedSystemFontOfSize_weight_(12, 0)
            try:
                text_storage = self.result_view.textStorage()
                full_range = (0, text_storage.length())
                text_storage.addAttribute_value_range_("NSFont", mono_font, full_range)
            except:
                pass
            # Calculate height based on text length (optimized for longer content)
            line_count = text.count('\n') + 1
            # Allow more room for longer text, max 700px for scrolling
            text_height = max(80, min(700, line_count * 18 + 40))
            self.expand_view_for_content(text_height)
            # CRITICAL: Force immediate layout calculation BEFORE scrolling
            # This prevents the "lag" where scroll happens before height calculation
            self.result_view.layoutManager().ensureLayoutForTextContainer_(self.result_view.textContainer())
            # FORCE scroll to bottom after text update - scroll PAST the end
            text_length = len(str(self.result_view.string()))
            if text_length > 0:
                # Scroll past the end to ensure we're at the very bottom
                self.result_view.scrollRangeToVisible_((text_length + 100, 0))
        except Exception:
            pass
    
    def scrollToBottom_(self, _):
        """Scroll result view to bottom (for chat mode)"""
        try:
            # Force layout calculation first
            self.result_view.layoutManager().ensureLayoutForTextContainer_(self.result_view.textContainer())

            # Enhanced: Scroll past the very end with extra 200 char buffer
            text_length = len(str(self.result_view.string()))
            if text_length > 0:
                self.result_view.scrollRangeToVisible_((text_length + 200, 0))

                # Also scroll to visible point at the absolute bottom
                try:
                    layout_manager = self.result_view.layoutManager()
                    text_container = self.result_view.textContainer()
                    glyph_range = layout_manager.glyphRangeForTextContainer_(text_container)
                    rect = layout_manager.boundingRectForGlyphRange_inTextContainer_(glyph_range, text_container)
                    self.result_view.scrollPoint_((0, rect.size.height))  # Scroll to max height
                except Exception:
                    pass
        except Exception:
            pass
    
    def forceScrollToBottom_(self, _):
        """FORCE scroll to bottom with scrollbar flash"""
        try:
            # Force layout calculation BEFORE scrolling
            self.result_view.layoutManager().ensureLayoutForTextContainer_(self.result_view.textContainer())
            
            # Get text length
            text_length = len(str(self.result_view.string()))
            if text_length > 0:
                # Scroll past very end to ensure absolute bottom
                self.result_view.scrollRangeToVisible_((text_length + 100, 0))
                
                # Flash scrollers to make them visible
                try:
                    self.scroll_view.flashScrollers()
                except:
                    pass
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
    
    def applicationWillTerminate_(self, notification):
        """Called when the app is about to quit - ensure tunnel cleanup"""
        print("\n⚠️  Application terminating - Cleaning up SSH tunnel...")
        cleanup_tunnel()
    
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


def signal_handler(signum, frame):
    """Handle termination signals (SIGTERM, SIGINT) to ensure cleanup"""
    print(f"\n⚠️  Received signal {signum} - Cleaning up before exit...")
    cleanup_tunnel()
    sys.exit(0)


def main():
    """Main entry point"""
    print("🚀 Starting Synth Menu Bar (Native)...")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: Register Signal Handlers (CRITICAL for menu bar apps!)
    # ═══════════════════════════════════════════════════════════
    # These catch Cmd+Q, kill, and Ctrl+C to ensure cleanup
    signal.signal(signal.SIGTERM, signal_handler)  # Cmd+Q, kill
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    atexit.register(cleanup_tunnel)                # Python exit (backup)
    print("✅ Signal handlers registered (tunnel will auto-close on ANY exit)\n")
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Start SSH Tunnel to Delta Brain
    # ═══════════════════════════════════════════════════════════
    print("🔌 Initializing Delta Brain Connection...")
    start_ssh_tunnel()
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Configure Application
    # ═══════════════════════════════════════════════════════════
    # Config - show Gemini fallback status
    from dotenv import load_dotenv
    load_dotenv()
    import os
    fb = os.getenv('GEMINI_FALLBACK_MODELS') or '(default)'
    free_only = os.getenv('GEMINI_FREE_TIER_ONLY', 'true')
    print(f"🔧 Gemini fallback models: {fb}")
    print(f"🔧 Gemini free-tier-only set: {free_only}")

    # ═══════════════════════════════════════════════════════════
    # STEP 4: Create and Run Application
    # ═══════════════════════════════════════════════════════════
    # Create app
    app = NSApplication.sharedApplication()
    
    # Create menu bar
    synth = getattr(SynthMenuBarNative, 'alloc')().init()
    
    # Register synth as app delegate to receive applicationWillTerminate_
    app.setDelegate_(synth)
    
    # Run app
    print("\n✅ Application ready - SSH tunnel active")
    print("   Press Cmd+Q or Ctrl+C to quit (tunnel will auto-close)")
    print("="*60 + "\n")
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n⚠️  Keyboard interrupt - Cleaning up...")
        cleanup_tunnel()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        cleanup_tunnel()
        raise


if __name__ == "__main__":
    main()
