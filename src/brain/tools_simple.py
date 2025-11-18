"""
Core Tools for Project Synth - Simple Python Functions  
No decorators, no LangChain tools - just plain functions

Author: Sushant Sharma
Date: November 17, 2025
"""

import os
import subprocess
from AppKit import NSPasteboard
import pyperclip
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env file. Please add it.")


def web_search_tavily(query: str) -> str:
    """Search web for current info using Tavily API"""
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        results = client.search(query, max_results=5)
        
        if not results or 'results' not in results:
            return f"No results found for: {query}"
        
        formatted = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results['results'][:5], 1):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            snippet = result.get('content', 'No description')
            formatted += f"{i}. {title}\n   {snippet}\n   URL: {url}\n\n"
        
        return formatted
    except Exception as e:
        return f"Error searching web: {str(e)}"


def file_search(query: str) -> str:
    """Find files on Mac by name"""
    try:
        result = subprocess.run(
            ['mdfind', f'kMDItemFSName == "*{query}*"'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return f"Error searching files: {result.stderr}"
        
        files = result.stdout.strip().split('\n')
        files = [f for f in files if f][:10]
        
        if not files:
            return f"No files found matching: {query}"
        
        formatted = f"Found {len(files)} files matching '{query}':\n\n"
        for i, filepath in enumerate(files, 1):
            formatted += f"{i}. {filepath}\n"
        
        return formatted
    except subprocess.TimeoutExpired:
        return "File search timed out"
    except Exception as e:
        return f"Error searching files: {str(e)}"


def clean_temp_files() -> str:
    """Remove temporary files"""
    try:
        total_cleaned = 0
        cleaned_dirs = []
        
        # Clean ~/Library/Caches
        cache_dir = os.path.expanduser("~/Library/Caches")
        if os.path.exists(cache_dir):
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    try:
                        filepath = os.path.join(root, file)
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        total_cleaned += size
                    except:
                        pass
            cleaned_dirs.append("~/Library/Caches")
        
        # Clean /tmp
        tmp_dir = "/tmp"
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                try:
                    filepath = os.path.join(root, file)
                    if os.access(filepath, os.W_OK):
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        total_cleaned += size
                except:
                    pass
        cleaned_dirs.append("/tmp")
        
        mb_cleaned = total_cleaned / (1024 * 1024)
        return f"✅ Cleaned {mb_cleaned:.2f} MB from temporary files\nDirectories: {', '.join(cleaned_dirs)}"
    except Exception as e:
        return f"Error cleaning temp files: {str(e)}"


def get_disk_space() -> str:
    """Check available disk storage"""
    try:
        stat = os.statvfs(os.path.expanduser("~"))
        free_bytes = stat.f_bavail * stat.f_frsize
        total_bytes = stat.f_blocks * stat.f_frsize
        used_bytes = total_bytes - free_bytes
        
        free_gb = free_bytes / (1024**3)
        total_gb = total_bytes / (1024**3)
        used_gb = used_bytes / (1024**3)
        percent_used = (used_gb / total_gb) * 100
        
        return f"""💾 Disk Space:
Total: {total_gb:.1f} GB
Used: {used_gb:.1f} GB ({percent_used:.1f}%)
Free: {free_gb:.1f} GB"""
    except Exception as e:
        return f"Error checking disk space: {str(e)}"


def open_app(app_name: str) -> str:
    """Open macOS application"""
    try:
        script = f'tell application "{app_name}" to activate'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return f"❌ Could not open {app_name}"
        
        return f"✅ Opened {app_name}"
    except Exception as e:
        return f"Error opening app: {str(e)}"


def chrome_search(query: str) -> str:
    """Open Chrome and search Google"""
    try:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        script = f'tell application "Google Chrome" to open location "{url}"'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            # Try Safari
            script = f'tell application "Safari" to open location "{url}"'
            subprocess.run(['osascript', '-e', script], timeout=5)
        
        return f"✅ Opened browser searching for: {query}"
    except Exception as e:
        return f"Error opening browser: {str(e)}"


def get_clipboard() -> str:
    """Read clipboard content"""
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_("public.utf8-plain-text")
        
        if text:
            return f"Clipboard content:\n{text}"
        else:
            return "Clipboard is empty"
    except Exception as e:
        return f"Error reading clipboard: {str(e)}"


def set_clipboard(text: str) -> str:
    """Copy text to clipboard"""
    try:
        pyperclip.copy(text)
        return f"✅ Copied to clipboard"
    except Exception as e:
        return f"Error setting clipboard: {str(e)}"
