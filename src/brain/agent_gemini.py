"""
Enhanced Autonomous Agent with Gemini AI
Pattern-based routing + Gemini for general questions

Author: Sushant Sharma
Date: November 17, 2025
"""

import os
from dotenv import load_dotenv
from src.brain.tools_gemini import (
    web_search_tavily,
    file_search,
    clean_temp_files,
    get_disk_space,
    open_app,
    chrome_search,
    get_clipboard,
    paraphrase_text,
    explain_text,
    general_chat
)

# Load environment variables
load_dotenv()


def execute_autonomous(command: str) -> str:
    """
    Execute command autonomously with Gemini AI fallback
    
    Uses pattern matching for specific tools, Gemini for general questions.
    
    Args:
        command: User query/command
        
    Returns:
        Tool execution result or AI response
    """
    command_lower = command.lower()
    
    # Web search patterns
    if any(keyword in command_lower for keyword in [
        'weather', 'news', 'latest', 'current', 'today', 'yesterday',
        'what is', 'who is', 'when did', 'search for', 'find out about'
    ]):
        return web_search_tavily(command)
    
    # File search patterns
    if any(keyword in command_lower for keyword in [
        'find file', 'locate file', 'search file', 'where is file'
    ]) or any(ext in command_lower for ext in ['.py', '.txt', '.pdf', '.doc']):
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
        'disk space', 'storage', 'how much space', 'free disk', 'available space'
    ]):
        return get_disk_space()
    
    # Open app
    if 'open' in command_lower and any(app in command_lower for app in [
        'chrome', 'safari', 'notes', 'spotify', 'whatsapp', 'slack', 'mail', 'messages'
    ]):
        # Extract app name
        for app in ['chrome', 'safari', 'notes', 'spotify', 'whatsapp', 'slack', 'mail', 'messages']:
            if app in command_lower:
                app_name = app.capitalize()
                if app == 'chrome':
                    app_name = 'Google Chrome'
                elif app == 'mail':
                    app_name = 'Mail'
                return open_app(app_name)
    
    # Browser search
    if any(keyword in command_lower for keyword in [
        'google', 'browse', 'look up'
    ]) and 'search' in command_lower:
        query = command.replace('google', '').replace('search', '').replace('browse', '').strip()
        return chrome_search(query)
    
    # Clipboard operations
    if any(keyword in command_lower for keyword in [
        'clipboard', 'copied', 'paste', 'what i copied', 'what did i copy'
    ]):
        return get_clipboard()
    
    # Paraphrase/rewrite
    if any(keyword in command_lower for keyword in [
        'paraphrase', 'rewrite', 'rephrase', 'make professional', 'improve this'
    ]):
        clipboard_text = _extract_clipboard_text()
        if clipboard_text:
            return paraphrase_text(clipboard_text)
        return "📋 Please copy some text first, then ask me to paraphrase it"

    if any(keyword in command_lower for keyword in [
        'explain', 'explanation', 'describe', 'break down'
    ]):
        clipboard_text = _extract_clipboard_text()
        if clipboard_text:
            return explain_text(clipboard_text)
        return "📋 Copy the passage with Cmd+C, then ask me to explain it."
    
    # Default: Use Gemini AI for general questions
    return general_chat(command)


def _extract_clipboard_text():
    """Return just the clipboard payload text, or None if empty."""
    clipboard_payload = get_clipboard()
    marker = "📋 Clipboard content:\n"
    if clipboard_payload.startswith(marker):
        text = clipboard_payload[len(marker):].strip()
        return text if text else None
    return None
