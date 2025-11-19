"""
macOS System Control Tools for Project Synth Autonomous Agent
Provides system operations: brightness, volume, battery, etc.

Author: Sushant Sharma
Date: November 17, 2025
"""

import subprocess
import platform
from langchain.tools import tool


@tool
def set_brightness(level: int) -> str:
    """Adjust screen brightness 0-100. Use when user mentions screen too bright/dark.
    
    Note: Requires 'brew install brightness' to be installed.
    
    Args:
        level: Brightness level 0-100
        
    Returns:
        Confirmation message
    """
    try:
        # Clamp level
        level = max(0, min(100, level))
        
        # Convert to 0.0-1.0 scale
        brightness_value = level / 100.0
        
        result = subprocess.run(
            ['brightness', str(brightness_value)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"✅ Screen brightness set to {level}%"
        else:
            return f"⚠️ Brightness command not found. Install with: brew install brightness"
            
    except FileNotFoundError:
        return f"⚠️ Brightness tool not installed. Install with: brew install brightness"
    except Exception as e:
        return f"❌ Error setting brightness: {str(e)}"


@tool
def set_volume(level: int) -> str:
    """Set system volume 0-100.
    
    Args:
        level: Volume level 0-100
        
    Returns:
        Confirmation message
    """
    try:
        # Clamp level
        level = max(0, min(100, level))
        
        script = f'set volume output volume {level}'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return f"🔊 Volume set to {level}%"
        else:
            return f"❌ Failed to set volume"
            
    except Exception as e:
        return f"❌ Error setting volume: {str(e)}"


@tool
def get_battery() -> str:
    """Check battery level and charging status.
    
    Returns:
        Battery percentage and charging status
    """
    try:
        result = subprocess.run(
            ['pmset', '-g', 'batt'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # Parse percentage
            import re
            match = re.search(r'(\d+)%', output)
            if match:
                percent = match.group(1)
                
                # Check charging status
                if 'AC Power' in output or 'charging' in output.lower():
                    status = "charging"
                elif 'discharging' in output.lower():
                    status = "discharging"
                else:
                    status = "charged"
                
                return f"🔋 Battery: {percent}% ({status})"
            else:
                return "⚠️ Could not parse battery info"
        else:
            return "❌ Failed to get battery status"
            
    except Exception as e:
        return f"❌ Error getting battery: {str(e)}"


@tool
def get_system_info() -> str:
    """Get Mac system information: OS, CPU, RAM, Python version.
    
    Returns:
        Formatted system details
    """
    try:
        info = []
        info.append(f"💻 System: {platform.system()} {platform.release()}")
        info.append(f"🖥️  Machine: {platform.machine()}")
        info.append(f"🐍 Python: {platform.python_version()}")
        info.append(f"📛 Node: {platform.node()}")
        
        # Try to get macOS version
        try:
            mac_ver = platform.mac_ver()[0]
            if mac_ver:
                info.append(f"🍎 macOS: {mac_ver}")
        except:
            pass
        
        return "\n".join(info)
        
    except Exception as e:
        return f"❌ Error getting system info: {str(e)}"


@tool
def wifi_status() -> str:
    """Check WiFi connection and network name.
    
    Returns:
        Network name or disconnected status
    """
    try:
        result = subprocess.run(
            ['networksetup', '-getairportnetwork', 'en0'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            
            if 'not associated' in output.lower():
                return "📡 WiFi: Not connected"
            else:
                # Extract network name
                network = output.replace('Current Wi-Fi Network:', '').strip()
                return f"📡 WiFi: Connected to '{network}'"
        else:
            return "❌ Failed to check WiFi status"
            
    except Exception as e:
        return f"❌ Error checking WiFi: {str(e)}"


@tool
def get_memory_usage() -> str:
    """Check RAM usage on Mac.
    
    Returns:
        Memory statistics
    """
    try:
        # Try using psutil if available
        try:
            import psutil
            mem = psutil.virtual_memory()
            
            total_gb = mem.total / (1024 ** 3)
            used_gb = mem.used / (1024 ** 3)
            percent = mem.percent
            
            return f"🧠 RAM: {used_gb:.1f}GB / {total_gb:.1f}GB ({percent}% used)"
        except ImportError:
            # Fallback to vm_stat
            result = subprocess.run(
                ['vm_stat'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return f"🧠 Memory stats:\n{result.stdout[:300]}"
            else:
                return "⚠️ Install psutil for better memory info: pip install psutil"
                
    except Exception as e:
        return f"❌ Error getting memory usage: {str(e)}"


@tool
def get_running_apps() -> str:
    """List all currently running applications.
    
    Returns:
        Formatted list of app names
    """
    try:
        try:
            from AppKit import NSWorkspace  # type: ignore
        except Exception:
            NSWorkspace = None  # type: ignore
    
        if NSWorkspace is None:
            return "⚠️ AppKit not available. Install: pip install pyobjc-framework-Cocoa"
    
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        # Filter to user apps (not background processes)
        app_names = []
        for app in running_apps:
            name = app.localizedName()
            if name and not name.startswith('com.') and app.activationPolicy() == 0:
                app_names.append(name)
        
        if not app_names:
            return "📱 No apps running"
        
        # Sort and limit
        app_names.sort()
        app_list = app_names[:15]
        
        output = ["📱 Running Apps:"]
        for app in app_list:
            output.append(f"  • {app}")
        
        if len(app_names) > 15:
            output.append(f"  ... and {len(app_names) - 15} more")
        
        return "\n".join(output)
        
    except ImportError:
        return "⚠️ AppKit not available. Install: pip install pyobjc-framework-Cocoa"
    except Exception as e:
        return f"❌ Error listing apps: {str(e)}"


# Export all system tools
SYSTEM_TOOLS = [
    set_brightness,
    set_volume,
    get_battery,
    get_system_info,
    wifi_status,
    get_memory_usage,
    get_running_apps
]
