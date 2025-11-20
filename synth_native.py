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
import re
import signal
from AppKit import (NSApplication, NSStatusBar, NSMenu, NSMenuItem,
                    NSTextField, NSButton, NSView, NSColor, NSFont,
                    NSNotificationCenter, NSUserNotification, NSUserNotificationCenter,
                    NSTextView, NSScrollView, NSPasteboard, NSApp, NSBox, NSPanel,
                    NSWindowStyleMaskBorderless, NSWindowStyleMaskNonactivatingPanel,
                    NSBackingStoreBuffered, NSStatusWindowLevel)
from Foundation import NSObject, NSMakeRect, NSMakeSize, NSPoint
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
NSPanel: Any = NSPanel
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
control_socket_path = None  # Full path to the ssh ControlPath socket

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
    # Use an absolute control socket path (avoid ~ expansion problems)
    global control_socket_path
    control_socket_path = os.path.expanduser(f"~/.ssh/synth-tunnel-{os.getpid()}")
    
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
        "-o", f"ControlPath={control_socket_path}",  # Unique socket per app instance (absolute path)
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
        print("   Waiting for connection to establish and verifying forwarded ports...")

        # Wait / retry for ports to become available (tunnel may be up before remote services)
        ports_ok = False
        max_attempts = 12  # up to ~12 * 0.5s = 6s total wait
        for attempt in range(max_attempts):
            all_ok = True
            for port in [11434, 11435, 11436]:
                try:
                    result = subprocess.run(
                        ["nc", "-z", "localhost", str(port)],
                        capture_output=True,
                        timeout=1
                    )
                    if result.returncode != 0:
                        all_ok = False
                        break
                except Exception:
                    all_ok = False
                    break

            if all_ok:
                ports_ok = True
                break

            # short backoff and retry
            time.sleep(0.5)

        # Report final status
        if ports_ok:
            print("\n✅ DELTA BRAIN TUNNEL ESTABLISHED")
            print("   Fast (3B):     localhost:11434")
            print("   Balanced (7B): localhost:11435")
            print("   Smart (14B):   localhost:11436")
        else:
            print("\n⚠️  Ports not responding after wait - tunnel is running but remote services may be down")
            print("   Brain may fall back to Gemini until Delta becomes available")
        
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
    
    # If we have no reference to the SSH process but a control socket exists,
    # still attempt cleanup (covers edge cases where start detected an
    # existing tunnel or start failed to retain the Popen handle).
    global control_socket_path
    if ssh_tunnel_process is None and not control_socket_path:
        return
    
    print("\n" + "="*60)
    print("🔌 CLEANING UP DELTA BRAIN SSH TUNNEL")
    print("="*60)
    
    # STEP 1: Kill ALL SSH tunnels to Delta (in case sshpass creates orphans)
    try:
        print("📡 Killing all SSH tunnels related to this connection (including orphaned processes)...")
        # Prefer using the actual host from SSH_ID when available
        host_part = None
        try:
            if ssh_connection_id and '@' in ssh_connection_id:
                host_part = ssh_connection_id.split('@')[1]
        except:
            host_part = None

        if host_part:
            pkill_pattern = f"ssh.*11434.*{host_part}"
        else:
            pkill_pattern = "ssh.*11434"

        # Use pkill to ensure we get ALL related processes
        subprocess.run(
            ["pkill", "-f", pkill_pattern],
            capture_output=True,
            timeout=5
        )
        print("✅ pkill executed (if any matching SSH processes existed)")
    except subprocess.TimeoutExpired:
        print("⚠️  Process cleanup timed out")
    except Exception as e:
        print(f"⚠️  pkill error: {e}")
    
    # STEP 2: Clean up remote control socket (Delta side)
    if ssh_connection_id:
        try:
            print("📡 Cleaning up remote control socket (if present) using ssh -O exit...")
            # Use the same control socket path we created (absolute path)
            if control_socket_path:
                control_path_arg = control_socket_path
            else:
                # Fallback to previous behavior (may be incorrect if PIDs differ)
                control_path_arg = os.path.expanduser(f"~/.ssh/synth-tunnel-{ssh_tunnel_process.pid if ssh_tunnel_process else 'unknown'}")

            subprocess.run(
                ["ssh", "-O", "exit", "-o", f"ControlPath={control_path_arg}", ssh_connection_id],
                capture_output=True,
                timeout=5
            )
            print("✅ Remote control socket cleaned up (ssh -O exit attempted)")
        except subprocess.TimeoutExpired:
            print("⚠️  Remote cleanup timed out (socket may already be closed)")
        except Exception as e:
            print(f"⚠️  Remote cleanup error: {e}")
    
    # STEP 3: Kill local SSH process group (backup cleanup)
    try:
        # If we have a live Popen handle, try to terminate its process group
        if ssh_tunnel_process:
            pgid = os.getpgid(ssh_tunnel_process.pid)
            print(f"📡 Terminating process group (PID: {ssh_tunnel_process.pid}, PGID: {pgid})")
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
        else:
            print("ℹ️ No local Popen handle; pkill/ssh -O exit were used as best-effort cleanup")

    except ProcessLookupError:
        print("⚠️  Process group already terminated")
    except Exception as e:
        print(f"⚠️  Process group cleanup error: {e}")
    
    # STEP 4: Final verification - ensure no processes remain
    try:
        # Final verification - try to find any remaining ssh processes matching our host
        if ssh_connection_id and '@' in ssh_connection_id:
            host_part = ssh_connection_id.split('@')[1]
            pgrep_pattern = f"ssh.*11434.*{host_part}"
        else:
            pgrep_pattern = "ssh.*11434"

        result = subprocess.run(
            ["pgrep", "-f", pgrep_pattern],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            remaining_pids = [p for p in result.stdout.strip().split('\n') if p.strip()]
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
        # Remove the exact control socket path we created earlier if present
        if control_socket_path:
            control_path = control_socket_path
        else:
            control_path = os.path.expanduser(f"~/.ssh/synth-tunnel-{ssh_tunnel_process.pid if ssh_tunnel_process else 'unknown'}")

        if control_path and os.path.exists(control_path):
            os.remove(control_path)
            print("✅ Local control socket file removed")
    except Exception as e:
        print(f"⚠️  Could not remove control socket: {e}")
    
    print("✅ TUNNEL CLEANUP COMPLETE (Mac + Delta)")
    print("="*60 + "\n")
    
    ssh_tunnel_process = None
    ssh_connection_id = None
    control_socket_path = None


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
            if characters:
                try:
                    characters = characters.lower()
                except:
                    pass
            # Command key mask (1 << 20)
            if modifierFlags & (1 << 20):
                if characters == 'c':
                    # Prefer copying from the window first responder if it's not this view
                    try:
                        w = self.window()
                        if w:
                            fr = w.firstResponder()
                            if fr is not None and fr is not self and hasattr(fr, 'copy_'):
                                try:
                                    fr.copy_(None)
                                    return True
                                except:
                                    pass
                    except Exception:
                        pass
                    # Fallback: copy from this view
                    try:
                        self.copy_(None)
                        return True
                    except:
                        pass
                elif characters == 'v':
                    # If this view is editable, paste here; otherwise try forwarding to window first responder
                    try:
                        if getattr(self, 'isEditable') and self.isEditable():
                            self.paste_(None)
                            return True
                        else:
                            w = self.window()
                            if w:
                                fr = w.firstResponder()
                                if fr and hasattr(fr, 'paste_'):
                                    try:
                                        fr.paste_(None)
                                        return True
                                    except:
                                        pass
                    except Exception:
                        pass
                elif characters == 'x':
                    try:
                        if getattr(self, 'isEditable') and self.isEditable():
                            self.cut_(None)
                            return True
                    except:
                        pass
                elif characters == 'a':
                    # Forward selectAll to first responder if possible
                    try:
                        w = self.window()
                        if w:
                            fr = w.firstResponder()
                            if fr is not None and fr is not self and hasattr(fr, 'selectAll_'):
                                try:
                                    fr.selectAll_(None)
                                    return True
                                except:
                                    pass
                    except Exception:
                        pass
                    try:
                        self.selectAll_(None)
                        return True
                    except:
                        pass
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
        """Copy selected text (or full text) to the general pasteboard."""
        try:
            selectedRange = self.selectedRange()
            text = ""
            try:
                if selectedRange and selectedRange.length > 0:
                    s = str(self.string())
                    text = s[selectedRange.location:selectedRange.location + selectedRange.length]
                else:
                    text = str(self.string())
            except Exception:
                text = str(self.string())

            if not text:
                return False

            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.clearContents()
            pasteboard.setString_forType_(text, "public.utf8-plain-text")

            return True
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
                    self.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))
                    self._is_placeholder = False
                
                # Insert text at cursor position
                selectedRange = self.selectedRange()
                
                # Use insertText_ which inserts into the view
                self.insertText_(text)
                
                # Trigger callback
                try:
                    cb = getattr(self, 'on_text_change_callback', None)
                    if cb:
                        cb()
                except:
                    pass
                
                # pasted into view (silent)
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
        try:
            length = len(self.string())
            self.setSelectedRange_((0, length))
            # selection updated
            self.setNeedsDisplay_(True)
            return True
        except Exception as e:
            print(f"⚠️ selectAll_ error: {e}")
            return False
    
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
        """Insert text and make it visible"""
        # Clear placeholder when actual text is inserted
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))
                self._is_placeholder = False
        except Exception:
            pass
        
        # Prevent inserting newlines; convert them to spaces
        if isinstance(text, str) and '\n' in text:
            text = text.replace('\n', ' ')
        
        # Manual text insertion (parent class doesn't work in menu bar)
        current_text = str(self.string())
        selected_range = self.selectedRange()
        
        # Build new text
        before = current_text[:selected_range.location]
        after = current_text[selected_range.location + selected_range.length:]
        new_text = before + text + after
        
        # Set new text
        self.setString_(new_text)
        
        # Move cursor to end of inserted text
        new_position = selected_range.location + len(text)
        self.setSelectedRange_((new_position, 0))
        
        # Force display update
        self.setNeedsDisplay_(True)
        
        # Invoke text change callback if present
        try:
            cb = getattr(self, 'on_text_change_callback', None)
            if cb:
                cb()
        except Exception:
            pass

    def keyDown_(self, event):
        """Handle key press events"""
        # Clear placeholder when typing
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))
                self._is_placeholder = False
        except Exception:
            pass
        
        # Get key character
        try:
            chars = event.characters() if hasattr(event, 'characters') else event.charactersIgnoringModifiers()
        except Exception:
            chars = None
        
        # Handle Enter/Return
        if chars and (chars == '\r' or chars == '\n'):
            try:
                cb = getattr(self, 'on_enter_callback', None)
                if cb:
                    cb()
                    return None
            except Exception:
                pass
        
        # Call parent to handle normal typing
        objc.super(InputTextView, self).keyDown_(event)
        
        # Trigger callback
        try:
            cb = getattr(self, 'on_text_change_callback', None)
            if cb:
                cb()
        except Exception:
            pass

    def setPlaceholder_(self, placeholder):
        # NSTextView doesn't have a native placeholder; we simply use setString_ if it's empty
        try:
            if not self.string() or self.string().strip() == '':
                self.setString_(placeholder)
                # Set placeholder color (lighter gray)
                self.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(0.5, 0.5, 0.55, 0.7))
                # Use a flag to indicate this is placeholder text so it can be cleared on focus
                self._is_placeholder = True
        except Exception:
            pass

    def focusIn_(self, sender):
        # Clear placeholder when focused
        try:
            if getattr(self, '_is_placeholder', False):
                self.setString_("")
                self.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))
                self._is_placeholder = False
        except Exception:
            pass



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
        if characters:
            try:
                characters = characters.lower()
            except:
                pass

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


class SynthPanel(NSPanel):
    """Custom NSPanel that acts as a pinned popover window (like Spotlight/Siri)"""
    
    def init(self):
        """Initialize the panel with custom configuration"""
        # Define style mask: borderless + non-activating panel
        style_mask = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        
        # Create panel with compact default size (500x190)
        content_rect = NSMakeRect(0, 0, 500, 190)
        self = objc.super(SynthPanel, self).initWithContentRect_styleMask_backing_defer_(
            content_rect,
            style_mask,
            NSBackingStoreBuffered,
            False
        )
        
        if self is None:
            return None
        
        # Set window level to appear over full-screen apps (like Spotlight)
        self.setLevel_(NSStatusWindowLevel)
        
        # Glassmorphism: semi-transparent background with blur (more opaque)
        bg_color = NSColor.colorWithRed_green_blue_alpha_(0.12, 0.12, 0.15, 0.92)  # More opaque
        self.setBackgroundColor_(bg_color)
        self.setOpaque_(False)  # Allow transparency
        
        # Add blur effect (vibrancy)
        try:
            from AppKit import NSVisualEffectView, NSVisualEffectBlendingModeBehindWindow, NSVisualEffectMaterialHUDWindow
            effect_view = NSVisualEffectView.alloc().initWithFrame_(content_rect)
            effect_view.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            effect_view.setMaterial_(NSVisualEffectMaterialHUDWindow)
            effect_view.setState_(1)  # Active
            self.setContentView_(effect_view)
        except:
            pass
        
        # Add rounded corners and subtle shadow with proper clipping
        try:
            self.contentView().setWantsLayer_(True)
            self.contentView().layer().setCornerRadius_(20.0)  # More rounded edges
            self.contentView().layer().setMasksToBounds_(True)  # Clip to rounded corners
            self.contentView().layer().setShadowColor_(NSColor.blackColor().CGColor())
            self.contentView().layer().setShadowOpacity_(0.5)
            self.contentView().layer().setShadowOffset_(NSMakeSize(0, -4))
            self.contentView().layer().setShadowRadius_(12.0)
            # Add blue border
            self.contentView().layer().setBorderWidth_(1.5)  # Thinner border
            self.contentView().layer().setBorderColor_(NSColor.colorWithRed_green_blue_alpha_(0.3, 0.6, 1.0, 0.5).CGColor())  # More subtle
        except:
            pass
        
        # Don't hide on deactivate - we'll handle closing manually
        self.setHidesOnDeactivate_(False)
        
        # Make panel movable by dragging anywhere
        self.setMovableByWindowBackground_(True)
        
        # Allow panel to become key window (for keyboard input)
        self.setAcceptsMouseMovedEvents_(True)
        
        return self
    
    def canBecomeKeyWindow(self):
        """Allow panel to become key window for keyboard input"""
        return True
    
    def canBecomeMainWindow(self):
        """Allow panel to become main window"""
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
        
        # Initialize Chat Manager
        self.chat_manager = ChatManager(max_history=50)
        print("💬 Chat manager initialized")
        
        # Chat Mode State
        self.chat_mode_active = False
        
        # Event monitor for click-outside-to-close
        self.click_monitor = None
        
        # UI sizing + layout guard rails
        self.default_width = 500
        self.default_result_height = 195
        self.max_result_height = 700  # Increased to 700px for longer conversations
        self.compact_height = 190  # Compact height for 6 buttons (2 rows)
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
        
        # Create status bar item and set its button target/action (more reliable)
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(-1)  # Variable width
        # Use the NSStatusItem's button when available (preferred on modern macOS)
        try:
            btn = self.statusitem.button()
            if btn is not None:
                btn.setTitle_("Synth")
                btn.setAction_("togglePanel:")
                btn.setTarget_(self)
            else:
                # Fallback: set on statusitem itself
                self.statusitem.setTitle_("Synth")
                self.statusitem.setAction_("togglePanel:")
                self.statusitem.setTarget_(self)
        except Exception:
            # Best-effort fallback
            try:
                self.statusitem.setTitle_("Synth")
                self.statusitem.setAction_("togglePanel:")
                self.statusitem.setTarget_(self)
            except:
                pass
        
        # Create custom panel (replaces NSMenu)
        self.panel = SynthPanel.alloc().init()
        
        # Create custom view with text field
        self.create_input_view()
        
        # Set content view
        self.panel.setContentView_(self.input_view)

        # Store original compact size for reset
        self.original_compact_height = 190
        # Flag to suppress background updates during UI transitions
        self._suppress_bg_updates = False
        
        # Ensure outer panel has rounded corners so the glassmorphed background
        # appears rounded at the window level (round both contentView and its
        # superview/theme frame). Keep panel non-opaque so transparency shows.
        try:
            self.panel.setOpaque_(False)
            # Round content view (clips inner content)
            cv = self.panel.contentView()
            if cv is not None:
                try:
                    cv.setWantsLayer_(True)
                except Exception as e:
                    print(f"⚠️ Failed to set wantsLayer on contentView: {e}")
                try:
                    cv.layer().setCornerRadius_(20.0)
                    cv.layer().setMasksToBounds_(True)
                except Exception:
                    try:
                        l = cv.layer()
                        setattr(l, 'cornerRadius', 20.0)
                        setattr(l, 'masksToBounds', True)
                    except:
                        print("⚠️ Failed to set layer attributes on contentView theme layer")

            # Also round the containing theme frame / superview so the
            # outermost window edges are rounded (this fixes the sharp outer
            # corners visible in the screenshot).
            try:
                theme_view = None
                if cv is not None:
                    try:
                        theme_view = cv.superview()
                    except:
                        theme_view = None
                if theme_view is None:
                    try:
                        theme_view = self.panel.contentView().superview()
                    except:
                        theme_view = None

                if theme_view is not None:
                    try:
                        theme_view.setWantsLayer_(True)
                    except Exception as e:
                        print(f"⚠️ Failed to set wantsLayer on theme_view: {e}")
                    try:
                        # Do NOT maskToBounds on the theme frame so shadows can draw
                        theme_view.layer().setCornerRadius_(20.0)
                        try:
                            theme_view.layer().setMasksToBounds_(False)
                        except Exception:
                            try:
                                setattr(theme_view.layer(), 'masksToBounds', False)
                            except Exception as e:
                                print(f"⚠️ Failed to set masksToBounds on theme_view.layer: {e}")
                    except Exception:
                        try:
                            l2 = theme_view.layer()
                            setattr(l2, 'cornerRadius', 20.0)
                            setattr(l2, 'masksToBounds', False)
                        except Exception as e:
                            print(f"⚠️ Failed to set fallback layer attributes on theme_view: {e}")
            except Exception:
                pass

            # Restore a semi-transparent background (do NOT make fully clear)
            # so the panel keeps its glassmorphic look but shows rounded edges.
            try:
                self.panel.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.12, 0.12, 0.15, 0.92))
            except Exception as e:
                print(f"⚠️ Failed to set panel background color: {e}")

            # Ensure the panel remains movable by dragging its background
            try:
                self.panel.setMovableByWindowBackground_(True)
            except Exception as e:
                print(f"⚠️ Failed to make panel movable by background: {e}")
        except Exception as e:
            print(f"⚠️ Error during panel rounding/background setup: {e}")
        
        # Action already attached to status item/button above
        
        # Create Edit menu for Copy/Paste support (CRITICAL for text editing)
        self.create_edit_menu()
        
        return self
    
    def create_input_view(self):
        """Create custom view with embedded text field and result area"""

        # Container view - compact initial size (2 rows of buttons)
        self.input_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, self.default_width, 190))
        self.input_view.setWantsLayer_(True)
        
        # Glassmorphism background
        try:
            self.input_view.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
        except:
            pass

        # Layout constants - better spacing
        padding = 16
        inner_width = self.default_width - (padding * 2)  # 468 for default_width 500
        result_view_height = self.default_result_height
        
        # Glassmorphism border color - subtle and elegant
        border_color = NSColor.colorWithRed_green_blue_alpha_(0.3, 0.3, 0.35, 0.4)

        # ============ RESULT VIEW (TOP) - Scrollable output ============
        # Use NSBox for border, with scroll_view inside
        border_box = NSBox.alloc().initWithFrame_(NSMakeRect(padding, 132, inner_width, result_view_height))
        border_box.setBoxType_(4)  # NSBoxCustom
        border_box.setBorderType_(1)  # NSLineBorder
        border_box.setBorderWidth_(0.5)  # Very thin border
        border_box.setBorderColor_(border_color)
        border_box.setCornerRadius_(18.0)  # More rounded
        border_box.setFillColor_(NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.94))  # More opaque

        # Create scroll view INSIDE the border box
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, inner_width, result_view_height))
        scroll_view.setBorderType_(0)  # No border
        scroll_view.setDrawsBackground_(True)
        scroll_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.88))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setAutohidesScrollers_(True)  # Auto-hide scrollers
        scroll_view.setScrollerStyle_(1)  # Overlay style
        scroll_view.setVerticalScrollElasticity_(1)
        scroll_view.setAutoresizingMask_(2)

        # Result text view - READ-ONLY, scrollable
        self.result_view = CopyableTextView.alloc().initWithFrame_(NSMakeRect(0, 0, inner_width - 20, result_view_height))
        self.result_view.setEditable_(False)
        self.result_view.setSelectable_(True)
        self.result_view.setRichText_(False)
        mono_font = NSFont.systemFontOfSize_(13)  # System font
        self.result_view.setFont_(mono_font)
        try:
            text_storage = self.result_view.textStorage()
            full_range = (0, text_storage.length())
            text_storage.addAttribute_value_range_("NSFont", mono_font, full_range)
        except:
            pass
        self.result_view.textContainer().setLineFragmentPadding_(8.0)
        self.result_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.88))
        self.result_view.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))  # Bright white
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

        # ============ INPUT TEXT VIEW (MIDDLE) - Editable WITH SCROLL ============
        input_container_height = 46
        input_container_y = 78  # Between button rows
        self.input_container = NSView.alloc().initWithFrame_(NSMakeRect(padding, input_container_y, inner_width, input_container_height))
        self.input_container.setWantsLayer_(True)
        try:
            # Glassmorphism input - black, not blue
            self.input_container.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.94).CGColor())  # More opaque
            self.input_container.layer().setBorderWidth_(1.0)  # More visible border
            self.input_container.layer().setBorderColor_(border_color.CGColor())
            self.input_container.layer().setCornerRadius_(12.0)  # Properly rounded
            self.input_container.layer().setMasksToBounds_(True)
        except:
            pass
        
        # Create scroll view for input (allows horizontal scrolling for long text)
        input_padding = 2
        input_scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(input_padding, input_padding, inner_width - (input_padding * 2), input_container_height - (input_padding * 2)))
        input_scroll_view.setBorderType_(0)  # No border
        input_scroll_view.setDrawsBackground_(False)
        input_scroll_view.setHasVerticalScroller_(False)  # No vertical scroll
        input_scroll_view.setHasHorizontalScroller_(True)  # Horizontal scroll
        input_scroll_view.setAutohidesScrollers_(True)
        input_scroll_view.setScrollerStyle_(1)  # Overlay style
        input_scroll_view.setHorizontalScrollElasticity_(1)
        
        # Input text view inside scroll view - horizontal layout with center-left cursor
        self.input_text_view = InputTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 10000, input_container_height - 10))
        self.input_text_view.setEditable_(True)
        self.input_text_view.setSelectable_(True)
        self.input_text_view.setRichText_(False)
        self.input_text_view.setFont_(NSFont.systemFontOfSize_(14))
        self.input_text_view.setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.88))  # Less transparent
        self.input_text_view.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))
        self.input_text_view.setInsertionPointColor_(NSColor.colorWithRed_green_blue_alpha_(0.3, 0.7, 1.0, 1.0))  # Bright blue cursor
        try:
            self.input_text_view.setInsertionPointWidth_(2.5)
        except:
            pass
        self.input_text_view.setDrawsBackground_(True)
        self.input_text_view.setVerticallyResizable_(False)  # No vertical resize
        self.input_text_view.setHorizontallyResizable_(True)  # Horizontal resize
        # Center cursor vertically by adjusting textContainerInset
        self.input_text_view.setTextContainerInset_(NSMakeSize(12, 11))  # 12px left padding, 11px top padding for vertical centering
        
        # Store references for focus handling
        self.placeholder_text = "Ask Synth"
        self.showing_placeholder = True
        
        # Store border color for focus effect
        self.default_border_color = border_color
        self.focus_border_color = NSColor.colorWithRed_green_blue_alpha_(0.3, 0.7, 1.0, 0.9)  # Bright blue border on focus
        try:
            self.input_text_view.setAutomaticTextReplacementEnabled_(False)
            self.input_text_view.setAutomaticQuoteSubstitutionEnabled_(False)
        except:
            pass
        try:
            # Horizontal scroll setup - text goes in one line
            self.input_text_view.textContainer().setWidthTracksTextView_(False)
            self.input_text_view.textContainer().setHeightTracksTextView_(True)
            self.input_text_view.textContainer().setContainerSize_(NSMakeSize(10000000, input_container_height - 10))
        except:
            pass
        self.input_text_view.setPlaceholder_("Ask Synth")
        self.input_text_view.on_enter_callback = self.handleInputEnter
        
        # Add text view to scroll view
        input_scroll_view.setDocumentView_(self.input_text_view)
        
        # Add scroll view to container
        self.input_container.addSubview_(input_scroll_view)
        self.input_scroll_view = input_scroll_view

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
        
        # Ensure input is editable and selectable
        self.input_text_view.setEditable_(True)
        self.input_text_view.setSelectable_(True)
        # Avoid using field editor behavior inside menu panel (can interfere with rendering)
        try:
            self.input_text_view.setFieldEditor_(True)
        except:
            # If not available, ignore
            pass
        self.input_text_view.setRichText_(False)  # Keep plain text
        # Enable standard edit operations
        try:
            self.input_text_view.setUsesFontPanel_(False)
            self.input_text_view.setAutomaticTextCompletionEnabled_(False)
            self.input_text_view.setAutomaticLinkDetectionEnabled_(False)
            self.input_text_view.setAutomaticQuoteSubstitutionEnabled_(False)
            self.input_text_view.setAutomaticDashSubstitutionEnabled_(False)
        except:
            pass

        # ============ 5 BUTTONS (ROW 1) ============
        btn_spacing = 8  # Better gap between buttons
        btn_count = 5
        btn_width = int((inner_width - (btn_spacing * (btn_count - 1))) / btn_count)
        btn_y = 40  # Top row of buttons
        btn_height = 30  # Taller buttons
        
        # Create styled buttons matching macOS style - no borders, hover effects only
        def create_styled_button(frame, title, is_blue=False):
            btn = NSButton.alloc().initWithFrame_(frame)
            btn.setTitle_(title)
            btn.setBezelStyle_(4)
            btn.setFont_(NSFont.systemFontOfSize_weight_(13, 0.5))
            btn.setWantsLayer_(True)
            try:
                btn.layer().setCornerRadius_(8.0)  # Rounded corners
                btn.layer().setBorderWidth_(0)  # No border
                if is_blue:
                    # Blue button with solid background
                    btn.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.25, 0.55, 1.0, 0.85).CGColor())
                else:
                    # Regular buttons with subtle gray background (macOS style)
                    btn.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.22, 0.6).CGColor())
            except:
                pass
            return btn
        
        # Button 1: Ask (BLUE)
        self.ask_button = create_styled_button(NSMakeRect(padding, btn_y, btn_width, btn_height), "Ask", is_blue=True)
        self.ask_button.setTarget_(self)
        self.ask_button.setAction_("handleQuery:")
        
        # Button 2: Agent
        self.agent_button = create_styled_button(NSMakeRect(padding + (btn_width + btn_spacing) * 1, btn_y, btn_width, btn_height), "🤖 Agent", is_blue=False)
        self.agent_button.setTarget_(self)
        self.agent_button.setAction_("handleAgentQuery:")
        
        # Button 3: Screen
        self.screen_button = create_styled_button(NSMakeRect(padding + (btn_width + btn_spacing) * 2, btn_y, btn_width, btn_height), "📸 Screen", is_blue=False)
        self.screen_button.setTarget_(self)
        self.screen_button.setAction_("handleScreen:")
        
        # Button 4: Copy
        self.copy_button = create_styled_button(NSMakeRect(padding + (btn_width + btn_spacing) * 3, btn_y, btn_width, btn_height), "Copy", is_blue=False)
        self.copy_button.setTarget_(self)
        self.copy_button.setAction_("copyResults:")
        
        # Button 5: Clear
        self.clear_button = create_styled_button(NSMakeRect(padding + (btn_width + btn_spacing) * 4, btn_y, btn_width, btn_height), "Clear", is_blue=False)
        self.clear_button.setTarget_(self)
        self.clear_button.setAction_("clearResults:")

        # ============ BUTTON 6 (ROW 2) - CHAT ============
        chat_btn_y = 6  # Bottom row
        self.chat_button = create_styled_button(NSMakeRect(padding, chat_btn_y, inner_width, btn_height), "💬 Chat", is_blue=False)
        self.chat_button.setTarget_(self)
        self.chat_button.setAction_("toggleChatMode:")
        
        # Add all views
        self.input_view.addSubview_(border_box)
        self.input_view.addSubview_(self.input_container)
        self.input_view.addSubview_(self.ask_button)
        self.input_view.addSubview_(self.agent_button)
        self.input_view.addSubview_(self.screen_button)
        self.input_view.addSubview_(self.copy_button)
        self.input_view.addSubview_(self.clear_button)
        self.input_view.addSubview_(self.chat_button)

        # Show output window by default with welcome message
        self.scroll_border_box.setHidden_(False)
        self.safe_update_result("✨ Welcome to Synth\n\nAsk me anything!")
    
    def create_edit_menu(self):
        """Create Edit menu for Copy/Paste keyboard shortcuts (CRITICAL for panel text editing)"""
        # Get main menu
        main_menu = NSApp.mainMenu()
        if main_menu is None:
            main_menu = NSMenu.alloc().init()
            NSApp.setMainMenu_(main_menu)
        
        # Check if Edit menu already exists
        for i in range(main_menu.numberOfItems()):
            item = main_menu.itemAtIndex_(i)
            if item and item.submenu() and item.submenu().title() == "Edit":
                print("✅ Edit menu already exists")
                return
        
        # Create Edit menu
        edit_menu = NSMenu.alloc().init()
        edit_menu.setTitle_("Edit")
        edit_menu.setAutoenablesItems_(True)
        
        # Add standard edit menu items
        edit_menu.addItemWithTitle_action_keyEquivalent_("Undo", "undo:", "z")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Redo", "redo:", "Z")
        edit_menu.addItem_(NSMenuItem.separatorItem())
        edit_menu.addItemWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Copy", "copy:", "c")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Delete", "delete:", "")
        edit_menu.addItemWithTitle_action_keyEquivalent_("Select All", "selectAll:", "a")
        
        # Add Edit menu to main menu
        edit_item = NSMenuItem.alloc().init()
        edit_item.setSubmenu_(edit_menu)
        main_menu.addItem_(edit_item)
        
        print("✅ Edit menu created with full copy/paste support")
    
    def togglePanel_(self, sender):
        """Toggle panel visibility and ALWAYS position it under the status item (like Spotlight)"""
        if self.panel.isVisible():
            # Close via centralized helper (restores original size/position)
            try:
                self.close_panel()
            except Exception:
                try:
                    self.panel.orderOut_(None)
                except:
                    pass
        else:
            # Restore original frame if available before showing
            try:
                opf = getattr(self, 'original_panel_frame', None)
                if opf and len(opf) >= 4:
                    self.panel.setFrame_display_(NSMakeRect(opf[0], opf[1], opf[2], opf[3]), True)
                    try:
                        self.relayout_for_width()
                    except Exception:
                        pass
            except Exception:
                pass

            # Position under status item and show
            try:
                self.position_panel_under_status_item()
            except Exception:
                pass

            NSApp.activateIgnoringOtherApps_(True)
            self.panel.makeKeyAndOrderFront_(None)
            try:
                self.prepare_prompt_entry()
            except Exception:
                pass
            self.start_click_monitor()
    
    def position_panel_under_status_item(self):
        """Position panel centered under the status item - called EVERY time panel opens or expands"""
        try:
            # Get status item button
            button = self.statusitem.button()
            if button:
                button_window = button.window()
                
                if button_window:
                    button_frame = button_window.frame()
                    
                    # Get current panel size (may have changed due to content)
                    panel_frame = self.panel.frame()
                    panel_width = panel_frame.size.width
                    panel_height = panel_frame.size.height
                    button_width = button_frame.size.width
                    
                    # Calculate position: centered under button
                    x = button_frame.origin.x - (panel_width / 2) + (button_width / 2)
                    y = button_frame.origin.y - panel_height - 8  # 8px gap below button
                    
                    # CRITICAL: ALWAYS update position (ignore where user dragged it)
                    self.panel.setFrameOrigin_(NSPoint(x, y))
                    # NOTE: suppress noisy reposition messages to the output/result view
                    return
        except Exception as e:
            print(f"⚠️ Error positioning panel: {e}")
        
        # Fallback: center on screen near top
        try:
            screen = NSApp.mainScreen()
            if screen:
                screen_frame = screen.visibleFrame()
                panel_frame = self.panel.frame()
                x = (screen_frame.size.width - panel_frame.size.width) / 2
                y = screen_frame.origin.y + screen_frame.size.height - panel_frame.size.height - 60
                self.panel.setFrameOrigin_(NSPoint(x, y))
                # Suppress fallback reposition message
        except Exception as e:
            print(f"❌ Failed to position panel: {e}")

    def is_panel_on_any_screen(self):
        """Return True if the panel overlaps any visible screen area.

        Used to avoid forcibly repositioning a panel the user dragged onto another area.
        """
        try:
            from AppKit import NSScreen
            screens = NSScreen.screens()
            panel_frame = self.panel.frame()
            for s in screens:
                sf = s.visibleFrame()
                # Check for rectangle overlap
                if not (
                    (panel_frame.origin.x + panel_frame.size.width) < sf.origin.x or
                    (panel_frame.origin.x) > (sf.origin.x + sf.size.width) or
                    (panel_frame.origin.y + panel_frame.size.height) < sf.origin.y or
                    (panel_frame.origin.y) > (sf.origin.y + sf.size.height)
                ):
                    return True
            return False
        except Exception:
            # If anything fails, conservatively return True so we don't jump the panel
            return True
    
    def start_click_monitor(self):
        """Start monitoring for clicks outside the panel"""
        from AppKit import NSEvent, NSEventMaskLeftMouseDown, NSEventMaskRightMouseDown
        
        # Remove existing monitor if any
        self.stop_click_monitor()
        
        def click_handler(event):
            """Handle mouse clicks - close panel if click is outside"""
            try:
                # Get click location in screen coordinates
                click_location = NSEvent.mouseLocation()
                
                # Get panel frame
                panel_frame = self.panel.frame()
                
                # Check if click is inside panel
                if not (panel_frame.origin.x <= click_location.x <= panel_frame.origin.x + panel_frame.size.width and
                        panel_frame.origin.y <= click_location.y <= panel_frame.origin.y + panel_frame.size.height):
                    # Click is outside panel - close it via helper so size resets
                    try:
                        self.close_panel()
                    except Exception:
                        try:
                            self.panel.orderOut_(None)
                        except:
                            pass
            except Exception as e:
                print(f"⚠️ Click monitor error: {e}")
            
            # Return event so it's processed normally
            return event
        
        # Monitor left and right mouse clicks globally
        self.click_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown,
            click_handler
        )
    
    def stop_click_monitor(self):
        """Stop monitoring for clicks outside the panel"""
        if self.click_monitor:
            from AppKit import NSEvent
            NSEvent.removeMonitor_(self.click_monitor)
            self.click_monitor = None

    # Panel visibility is now handled by togglePanel: method
    # No need for menuWillOpen_/menuDidClose_ delegates

    def prepare_prompt_entry(self):
        """Focus the text field on the main thread."""
        try:
            self.performSelectorOnMainThread_withObject_waitUntilDone_(
                "focusTextField:", None, False
            )
        except Exception as exc:
            print(f"⚠️ Unable to schedule prompt focus: {exc}")

    def focusTextField_(self, _):
        """Selector helper that safely focuses the input text view and handles placeholder."""
        try:
            window = self.input_text_view.window()
            if window is not None:
                # CRITICAL: Make window key FIRST
                window.makeKeyAndOrderFront_(None)
                # Then make input first responder
                success = window.makeFirstResponder_(self.input_text_view)
                if success:
                    # Clear placeholder when focused
                    if self.showing_placeholder:
                        self.input_text_view.setString_("")
                        self.input_text_view.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.95))
                        self.showing_placeholder = False
                    
                    # Blue border on focus
                    try:
                        self.input_container.layer().setBorderColor_(self.focus_border_color.CGColor())
                        self.input_container.layer().setBorderWidth_(1.5)
                    except:
                        pass
                    
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
        """Hide result pane and shrink container back to compact height with welcome message."""
        # Store current top-left position before resize
        panel_frame = self.panel.frame()
        original_top = panel_frame.origin.y + panel_frame.size.height
        
        # Hide result area and reset to compact size
        self.scroll_border_box.setHidden_(True)
        self.current_result_height = 0
        self.input_view.setFrame_(NSMakeRect(0, 0, self.default_width, self.original_compact_height))
        
        # Resize panel to compact size, keeping top-left anchored
        new_y = original_top - self.original_compact_height
        panel_frame.origin.y = new_y
        panel_frame.size.height = self.original_compact_height
        self.panel.setFrame_display_(panel_frame, True)
        
        # Show welcome message
        self.scroll_border_box.setHidden_(False)
        self.safe_update_result("✨ Welcome to Synth\n\nAsk me anything!")
        self.expand_view_for_content(100)
        
        # Restore placeholder if input is empty
        if not str(self.input_text_view.string()).strip():
            self.input_text_view.setString_(self.placeholder_text)
            self.input_text_view.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(0.5, 0.5, 0.55, 0.6))  # Gray placeholder
            self.showing_placeholder = True
    
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
        """Clear the result area and reset to original welcome state"""
        # Clear input text
        self.input_text_view.setString_("")
        self.input_text_view.setEditable_(True)
        
        # RESET CLIPBOARD STATE - user must do Cmd+C again to capture new text
        self.captured_clipboard = None
        self.clipboard_timestamp = None
        
        # Clear chat history
        self.chat_manager.clear()
        
        # Show appropriate message based on mode
        if self.chat_mode_active:
            # In chat mode, just clear conversation but keep expanded
            self.safe_update_result("💬 Chat Mode Active\n\nConversation cleared. Start a new conversation...")
            self.scroll_border_box.setHidden_(False)
            self.expand_view_for_content(100)
        else:
            # Normal mode: return to original compact welcome state
            print("🔄 Cleared: Returning to welcome screen")
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
            # Normal mode: Enter triggers Ask button AND CLEARS INPUT
            self.handleQuery_(None)
            # Clear input after sending
            self.input_text_view.setString_("")
    
    
    def toggleChatMode_(self, sender):
        """Toggle Chat Mode ON/OFF - COMPLETE IMPLEMENTATION"""
        # Suppress background responses briefly while UI transitions
        try:
            self._suppress_bg_updates = True
            threading.Timer(0.8, lambda: setattr(self, '_suppress_bg_updates', False)).start()
        except Exception:
            pass

        self.chat_mode_active = not self.chat_mode_active
        
        if self.chat_mode_active:
            # ═══════ ACTIVATE CHAT MODE ═══════
            # Change button text
            self.chat_button.setTitle_("💬 Chat Mode (ON)")
            
            # Disable other buttons (Ask/Agent/Screen)
            self.ask_button.setEnabled_(False)
            self.agent_button.setEnabled_(False)
            self.screen_button.setEnabled_(False)
            
            # Keep black background in chat mode - no blue tint
            # Just slightly less transparent for better readability
            chat_bg_color = NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.92)
            chat_result_bg = NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.92)
            
            self.input_text_view.setBackgroundColor_(chat_bg_color)
            self.result_view.setBackgroundColor_(chat_result_bg)
            
            # Update container background too
            try:
                self.input_container.layer().setBackgroundColor_(chat_bg_color.CGColor())
            except:
                pass
            
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
            
            # Restore original background colors - black, not blue
            normal_input_bg = NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.88)
            normal_result_bg = NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.10, 0.88)
            
            self.input_text_view.setBackgroundColor_(normal_input_bg)
            self.result_view.setBackgroundColor_(normal_result_bg)
            
            # Restore container background too
            try:
                self.input_container.layer().setBackgroundColor_(normal_input_bg.CGColor())
            except:
                pass
            
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
        
        # Clear input text after Enter (show in output window instead)
        if query:
            self.input_text_view.setString_("")
        
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

        # Clear input text after Enter (show in output window instead)
        self.input_text_view.setString_("")

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

        # Clear input text after Enter (show in output window instead)
        self.input_text_view.setString_("")

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
        """Expand the view to fit content - grows DOWNWARD from top-left anchor"""
        # Calculate new total height with guard rails
        result_height = min(self.max_result_height, max(100, content_height))
        new_total_height = result_height + 142  # Account for input + buttons (2 rows)
        self.current_result_height = result_height
        
        # Store current top-left position
        panel_frame = self.panel.frame()
        original_top = panel_frame.origin.y + panel_frame.size.height
        
        # Resize scroll view (result area)
        self.scroll_border_box.setHidden_(False)
        self.scroll_border_box.setFrame_(NSMakeRect(16, 132, 468, result_height))
        
        # Resize container
        self.input_view.setFrame_(NSMakeRect(0, 0, self.default_width, new_total_height))
        
        # Resize panel window - keep top-left position fixed, grow downward
        new_y = original_top - new_total_height
        panel_frame.origin.y = new_y
        panel_frame.size.height = new_total_height
        self.panel.setFrame_display_(panel_frame, True)
    
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
        
        """

        # Ensure input is editable and selectable
        self.input_text_view.setEditable_(True)
        self.input_text_view.setSelectable_(True)
        # Avoid using field editor behavior inside menu panel (can interfere with rendering)
        try:
            self.input_text_view.setFieldEditor_(False)
        except:
            # If not available, ignore
            pass
        def process_in_background():
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

        # Run in background thread
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
    
    def safe_update_result(self, text):
        """Safely update result view from any thread"""
        # Ensure UI updates happen on the main thread (use performSelectorOnMainThread)
        # Filter noisy messages that shouldn't appear in the result box
        try:
            if isinstance(text, str) and 'Panel repositioned' in text:
                return
        except Exception:
            pass
        # Suppress background updates during quick UI transitions (allow main thread updates)
        try:
            if getattr(self, '_suppress_bg_updates', False) and threading.current_thread().name != 'MainThread':
                return
        except Exception:
            pass
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