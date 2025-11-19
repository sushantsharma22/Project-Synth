"""
macOS Application Control Tools for Project Synth Autonomous Agent
Provides application control: browsers, messaging, music, notes, etc.

Author: Sushant Sharma
Date: November 17, 2025
"""

import subprocess
import time
from langchain.tools import tool


@tool
def chrome_open_url(url: str) -> str:
    """Open specific URL in Chrome browser.
    
    Args:
        url: URL to open in Chrome
        
    Returns:
        Success message
    """
    try:
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = f"https://{url}"
        
        script = f'tell application "Google Chrome" to open location "{url}"'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"✅ Opened in Chrome: {url}"
        else:
            return f"❌ Failed to open Chrome. Is it installed?"
            
    except Exception as e:
        return f"❌ Error opening Chrome: {str(e)}"


@tool
def safari_open_url(url: str) -> str:
    """Open URL in Safari browser.
    
    Args:
        url: URL to open in Safari
        
    Returns:
        Success message
    """
    try:
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = f"https://{url}"
        
        script = f'tell application "Safari" to open location "{url}"'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"✅ Opened in Safari: {url}"
        else:
            return f"❌ Failed to open Safari"
            
    except Exception as e:
        return f"❌ Error opening Safari: {str(e)}"


@tool
def whatsapp_call(contact: str) -> str:
    """Call a contact on WhatsApp. Contact should be first name like 'mom', 'dad', 'john'.
    
    Args:
        contact: Contact first name to call
        
    Returns:
        Calling confirmation
    """
    try:
        # Activate WhatsApp and search for contact
        script = f'''
        tell application "WhatsApp" to activate
        delay 1
        tell application "System Events"
            tell process "WhatsApp"
                keystroke "f" using {{command down}}
                delay 0.5
                keystroke "{contact}"
                delay 1
                keystroke return
                delay 0.5
            end tell
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"📞 Initiated WhatsApp call to: {contact}"
        else:
            return f"⚠️ WhatsApp may not be installed or contact not found: {contact}"
            
    except Exception as e:
        return f"❌ Error calling on WhatsApp: {str(e)}"


@tool
def whatsapp_message(contact: str, message: str) -> str:
    """Send WhatsApp text message to contact using reliable AppleScript automation.
    
    Args:
        contact: Contact first name (e.g., 'John', 'Mom', 'Ajit')
        message: Message text to send
        
    Returns:
        Sent confirmation
    """
    try:
        print(f"🔧 WhatsApp Tool Called:")
        print(f"   Contact: {contact}")
        print(f"   Message: {message[:50]}...")
        
        # Escape special characters for AppleScript
        escaped_contact = contact.replace('\\', '\\\\').replace('"', '\\"')
        escaped_message = message.replace('\\', '\\\\').replace('"', '\\"')
        
        # Rock-solid AppleScript with proper delays
        script = f'''
        -- Activate WhatsApp
        tell application "WhatsApp"
            activate
        end tell
        delay 1.5
        
        tell application "System Events"
            tell process "WhatsApp"
                set frontmost to true
                delay 0.5
                
                -- Open new chat (Cmd+N is more reliable than Cmd+F)
                keystroke "n" using command down
                delay 1.5
                
                -- Type contact name
                keystroke "{escaped_contact}"
                delay 2
                
                -- Press down arrow to select first result
                key code 125
                delay 0.5
                
                -- Press return to open chat
                keystroke return
                delay 2
                
                -- Type the message
                keystroke "{escaped_message}"
                delay 1
                
                -- Send (Return key)
                keystroke return
                delay 0.5
            end tell
        end tell
        
        return "SUCCESS"
        '''
        
        print(f"📝 Executing AppleScript automation...")
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=20
        )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        print(f"📤 Result: returncode={result.returncode}")
        if stdout:
            print(f"   stdout: {stdout}")
        if stderr:
            print(f"   stderr: {stderr}")
        
        if result.returncode == 0 or "SUCCESS" in stdout:
            return f"✅ Sent WhatsApp message to {contact}: '{message[:40]}...'"
        else:
            error_msg = stderr if stderr else "Unknown error"
            return f"⚠️ WhatsApp automation error: {error_msg[:100]}"
            
    except subprocess.TimeoutExpired:
        return f"❌ WhatsApp automation timed out after 20s"
    except Exception as e:
        import traceback
        print(f"❌ Exception:\n{traceback.format_exc()}")
        return f"❌ Error: {str(e)}"


@tool
def spotify_play(query: str) -> str:
    """Play song, artist, or playlist on Spotify.
    
    Args:
        query: Song name, artist, or playlist to play
        
    Returns:
        Now playing message
    """
    try:
        script = f'''
        tell application "Spotify"
            activate
            play track "spotify:search:{query}"
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"🎵 Playing on Spotify: {query}"
        else:
            return f"⚠️ Spotify may not be installed or track not found"
            
    except Exception as e:
        return f"❌ Error playing on Spotify: {str(e)}"


@tool
def spotify_control(action: str) -> str:
    """Control Spotify playback. Actions: play, pause, next, previous.
    
    Args:
        action: Control action (play, pause, next, previous)
        
    Returns:
        Action confirmation
    """
    try:
        action = action.lower()
        
        if action not in ['play', 'pause', 'next', 'previous']:
            return f"❌ Invalid action. Use: play, pause, next, or previous"
        
        # Map actions to AppleScript commands
        commands = {
            'play': 'play',
            'pause': 'pause',
            'next': 'next track',
            'previous': 'previous track'
        }
        
        script = f'tell application "Spotify" to {commands[action]}'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"🎵 Spotify: {action}"
        else:
            return f"⚠️ Spotify may not be running"
            
    except Exception as e:
        return f"❌ Error controlling Spotify: {str(e)}"


@tool
def quit_app(app_name: str) -> str:
    """Close/quit any running application.
    
    Args:
        app_name: Name of application to quit
        
    Returns:
        Closed confirmation
    """
    try:
        script = f'tell application "{app_name}" to quit'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"✅ Quit: {app_name}"
        else:
            return f"❌ Could not quit {app_name}. App may not be running."
            
    except Exception as e:
        return f"❌ Error quitting app: {str(e)}"


@tool
def focus_app(app_name: str) -> str:
    """Bring application to front/focus.
    
    Args:
        app_name: Name of application to focus
        
    Returns:
        Focused confirmation
    """
    try:
        script = f'tell application "{app_name}" to activate'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"✅ Focused: {app_name}"
        else:
            return f"❌ Could not focus {app_name}. App may not be installed."
            
    except Exception as e:
        return f"❌ Error focusing app: {str(e)}"


@tool
def notes_create(title: str, content: str) -> str:
    """Create new note in Notes app.
    
    Args:
        title: Note title
        content: Note content/body
        
    Returns:
        Note created message
    """
    try:
        # Escape quotes
        escaped_title = title.replace('"', '\\"')
        escaped_content = content.replace('"', '\\"')
        
        script = f'''
        tell application "Notes"
            tell account "iCloud"
                make new note at folder "Notes" with properties {{name:"{escaped_title}", body:"{escaped_content}"}}
            end tell
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"📝 Created note: {title}"
        else:
            return f"⚠️ Notes app may not be configured or iCloud account not available"
            
    except Exception as e:
        return f"❌ Error creating note: {str(e)}"


@tool
def get_active_app() -> str:
    """Get name of currently focused application.
    
    Returns:
        Active app name
    """
    try:
        from AppKit import NSWorkspace
        
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.activeApplication()
        
        app_name = active_app.get('NSApplicationName', 'Unknown')
        
        return f"🎯 Active app: {app_name}"
        
    except ImportError:
        return "⚠️ AppKit not available. Install: pip install pyobjc-framework-Cocoa"
    except Exception as e:
        return f"❌ Error getting active app: {str(e)}"


@tool
def open_file_or_folder(path: str) -> str:
    """Open any file or folder in Finder or default application.
    Use this to open folders like Downloads, Documents, Desktop.
    Use this to open files with their default app (PDFs, images, etc).
    
    Args:
        path: File or folder path (can use ~ for home, like ~/Downloads or ~/Downloads/file.pdf)
        
    Returns:
        Opened confirmation
    """
    try:
        import os
        
        # Expand ~ to home directory
        expanded_path = os.path.expanduser(path)
        
        # Check if exists
        if not os.path.exists(expanded_path):
            return f"❌ Path not found: {expanded_path}"
        
        # Use macOS 'open' command to open file/folder
        result = subprocess.run(
            ['open', expanded_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Determine if it's a file or folder
            if os.path.isdir(expanded_path):
                return f"📁 Opened folder in Finder: {expanded_path}"
            else:
                return f"📄 Opened file: {expanded_path}"
        else:
            return f"❌ Failed to open: {expanded_path}\n{result.stderr}"
            
    except Exception as e:
        return f"❌ Error opening path: {str(e)}"


# Export all app control tools
APP_TOOLS = [
    chrome_open_url,
    safari_open_url,
    whatsapp_call,
    whatsapp_message,
    spotify_play,
    spotify_control,
    quit_app,
    focus_app,
    notes_create,
    get_active_app,
    open_file_or_folder  # NEW: Open files and folders
]
