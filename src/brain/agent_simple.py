"""
SIMPLIFIED AUTONOMOUS AGENT - Tavily Only (No Gemini needed!)
Uses pattern matching + Tavily for autonomous command execution

Since Gemini has dependency conflicts, using a simpler approach:
- Pattern-based tool selection (like original routing but cleaner)
- Tavily for web search
- Works immediately without LLM complications

Author: Sushant Sharma
Date: November 17, 2025
"""

import os
from dotenv import load_dotenv
from src.brain.tools_simple import (
    web_search_tavily,
    file_search,
    clean_temp_files,
    get_disk_space,
    open_app,
    chrome_search,
    get_clipboard,
    set_clipboard
)

# Load environment variables
load_dotenv()

def execute_autonomous(command: str) -> str:
    """
    Execute command autonomously - simplified pattern matching
    
    This is a simplified version that doesn't need Gemini.
    Uses pattern matching to decide which tool to use.
    
    Args:
        command: User query/command
        
    Returns:
        Tool execution result
    """
    command_lower = command.lower()
    
    # Web search patterns
    if any(keyword in command_lower for keyword in [
        'weather', 'news', 'latest', 'current', 'today',
        'what is', 'who is', 'when did', 'search', 'find out'
    ]):
        return web_search_tavily(command)
    
    # File search patterns
    if any(keyword in command_lower for keyword in [
        'find file', 'locate file', 'search file', '.py', '.txt', '.pdf'
    ]):
        # Extract filename from command
        words = command.split()
        filename = words[-1] if words else "document"
        return file_search(filename)
    
    # Clean temp files
    if any(keyword in command_lower for keyword in [
        'clean', 'cleanup', 'temp', 'cache', 'free space', 'delete temp'
    ]):
        return clean_temp_files()
    
    # Disk space
    if any(keyword in command_lower for keyword in [
        'disk space', 'storage', 'how much space', 'free disk'
    ]):
        return get_disk_space()
    
    # Open app
    if 'open' in command_lower and any(app in command_lower for app in [
        'chrome', 'safari', 'notes', 'spotify', 'whatsapp', 'slack'
    ]):
        # Extract app name
        for app in ['chrome', 'safari', 'notes', 'spotify', 'whatsapp', 'slack']:
            if app in command_lower:
                return open_app(app.capitalize())
    
    # Browser search
    if any(keyword in command_lower for keyword in [
        'google', 'browse', 'look up'
    ]) and 'search' in command_lower:
        query = command.replace('google', '').replace('search', '').replace('browse', '').strip()
        return chrome_search(query)
    
    # Clipboard
    if any(keyword in command_lower for keyword in [
        'clipboard', 'copied', 'paste', 'what i copied'
    ]):
        return get_clipboard()
    
    # Default: web search
    return web_search_tavily(command)
