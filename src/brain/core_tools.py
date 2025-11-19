"""
Core Tools for Project Synth Autonomous Agent
Enhanced with Live Tools for instant, free specific queries

Author: Sushant Sharma
Date: November 19, 2025
"""

import os
import subprocess
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
try:
    try:
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            # Static import for type checkers; runtime import is optional
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            HAS_LANGCHAIN_GOOGLE_GENAI = True
        except Exception:
            ChatGoogleGenerativeAI = None
            HAS_LANGCHAIN_GOOGLE_GENAI = False
            print("⚠️ langchain_google_genai not installed. Falling back to genai client or free-tier models.")
        HAS_LANGCHAIN_GOOGLE_GENAI = True
    except Exception:
        ChatGoogleGenerativeAI = None
        HAS_LANGCHAIN_GOOGLE_GENAI = False
        print("⚠️ langchain_google_genai not installed. Falling back to genai client or free-tier models.")
    HAS_LANGCHAIN_GOOGLE_GENAI = True
except Exception:
    ChatGoogleGenerativeAI = None
    HAS_LANGCHAIN_GOOGLE_GENAI = False
    print("⚠️ langchain_google_genai not installed. Gemini LLM via LangChain disabled. Falling back to genai client.")
from AppKit import NSPasteboard
import pyperclip
from dotenv import load_dotenv

# Import Live Tools (instant, free, specific queries)
from src.brain.live_tools import (
    get_weather,
    get_stock_price,
    search_wikipedia,
    get_definition,
    is_website_down,
    search_reddit_opinions
)

# Load environment variables
load_dotenv()

# Get API keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add it.")


@tool
def web_search_free(query: str) -> str:
    """Search web for current info, news, facts, recent events. FREE with 3-tier fallback system.
    Use for any time-sensitive or factual queries that aren't covered by specific tools.
    
    Args:
        query: Search query string
        
    Returns:
        Formatted search results with titles and snippets
    """
    try:
        from src.rag.web_search import WebSearchRAG
        
        # Initialize web search RAG
        rag = WebSearchRAG()
        
        # Perform search (3-tier: Google → DuckDuckGo → Tavily)
        results = rag.search(query, include_news=True)
        
        if results['sources_count'] == 0:
            return f"No results found for: {query}"
        
        # Return formatted context
        return results['context']
        
    except Exception as e:
        return f"Error searching web: {str(e)}"


@tool
def web_search_tavily(query: str) -> str:
    """DEPRECATED: Use web_search_free instead. Legacy Tavily search (requires API key).
    
    Args:
        query: Search query string
        
    Returns:
        Formatted search results
    """
    try:
        if not TAVILY_API_KEY:
            return "⚠️  Tavily API key not configured. Using free web search instead..."
        
        search = TavilySearchResults(
            api_key=TAVILY_API_KEY,
            max_results=5
        )
        results = search.invoke(query)
        
        if not results:
            return f"No results found for: {query}"
        
        formatted = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            snippet = result.get('content', 'No description')
            formatted += f"{i}. {title}\n   {snippet}\n   URL: {url}\n\n"
        
        return formatted
    except Exception as e:
        return f"Error searching web: {str(e)}"


@tool
def file_search(query: str) -> str:
    """Find files on Mac by name. Returns list of file paths.
    
    Args:
        query: File name or pattern to search for
        
    Returns:
        List of file paths found
    """
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
        files = [f for f in files if f][:10]  # Limit to 10 results
        
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


@tool
def clean_temp_files() -> str:
    """Remove temporary files and caches to free disk space.
    
    Returns:
        Message with MB cleaned
    """
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


@tool
def get_disk_space() -> str:
    """Check available disk storage on Mac.
    
    Returns:
        Formatted string with disk space information
    """
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


@tool
def open_app(app_name: str) -> str:
    """Open any macOS application by name. Examples: Chrome, Safari, WhatsApp, Spotify, Notes.
    
    Args:
        app_name: Name of the application to open
        
    Returns:
        Success or error message
    """
    try:
        script = f'tell application "{app_name}" to activate'
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return f"❌ Could not open {app_name}. App may not be installed.\nError: {result.stderr}"
        
        return f"✅ Opened {app_name}"
    except subprocess.TimeoutExpired:
        return f"Timeout opening {app_name}"
    except Exception as e:
        return f"Error opening app: {str(e)}"


@tool
def chrome_search(query: str) -> str:
    """Open Chrome browser and search Google. Use when user wants to browse or research online.
    
    Args:
        query: Search query for Google
        
    Returns:
        Success message
    """
    try:
        # URL encode the query
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
            # Try with Safari as fallback
            script = f'tell application "Safari" to open location "{url}"'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return f"❌ Could not open browser"
        
        return f"✅ Opened browser searching for: {query}"
    except Exception as e:
        return f"Error opening browser: {str(e)}"


@tool
def get_clipboard() -> str:
    """Read current clipboard content. Use when user says 'this text', 'what I copied', or 'the text above'.
    
    Returns:
        Clipboard text or "Clipboard empty" message
    """
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_("public.utf8-plain-text")
        
        if text:
            return f"Clipboard content:\n{text}"
        else:
            return "Clipboard is empty"
    except Exception as e:
        return f"Error reading clipboard: {str(e)}"


@tool
def set_clipboard(text: str) -> str:
    """Copy text to clipboard for user to paste elsewhere.
    
    Args:
        text: Text to copy to clipboard
        
    Returns:
        Success confirmation
    """
    try:
        pyperclip.copy(text)
        return f"✅ Copied to clipboard: {text[:100]}{'...' if len(text) > 100 else ''}"
    except Exception as e:
        return f"Error setting clipboard: {str(e)}"


@tool
def paraphrase_text(text: str) -> str:
    """Rewrite text to be more professional, clear, or polished. Use when user wants to improve writing.
    
    Args:
        text: Text to paraphrase
        
    Returns:
        Paraphrased text
    """
    try:
        if HAS_LANGCHAIN_GOOGLE_GENAI and ChatGoogleGenerativeAI:
            # Use a default model that prefers free-tier models
            from src.brain.tools_gemini import get_preferred_model_names
            _, preferred_langchain_model = get_preferred_model_names()
            llm = ChatGoogleGenerativeAI(
                model=preferred_langchain_model,
                google_api_key=GEMINI_API_KEY,
                temperature=0.7
            )
            prompt = f"Rewrite this professionally and concisely:\n\n{text}"
            response = llm.invoke(prompt)
            # response.content can be str or list/dict; coerce safely to string
            content = response.content
            if isinstance(content, list):
                content = "\n".join(str(c) for c in content)
            return str(content)
        else:
            # Fall back to tools_gemini paraphrase_text implementation
            from src.brain.tools_gemini import paraphrase_text as gm_paraphrase
            return gm_paraphrase(text)
    except Exception as e:
        return f"Error paraphrasing: {str(e)}"


@tool
def general_chat(message: str) -> str:
    """Answer general questions, have conversations, explain concepts. Use when no specific action tool is needed.
    
    Args:
        message: User's question or message
        
    Returns:
        AI response
    """
    try:
        if HAS_LANGCHAIN_GOOGLE_GENAI and ChatGoogleGenerativeAI:
            from src.brain.tools_gemini import get_preferred_model_names
            _, preferred_langchain_model = get_preferred_model_names()
            llm = ChatGoogleGenerativeAI(
                model=preferred_langchain_model,
                google_api_key=GEMINI_API_KEY,
                temperature=0.7
            )
            response = llm.invoke(message)
            content = response.content
            if isinstance(content, list):
                content = "\n".join(str(c) for c in content)
            return str(content)
        else:
            # Fall back to tools_gemini.general_chat
            from src.brain.tools_gemini import general_chat as gm_general_chat
            return gm_general_chat(message)
    except Exception as e:
        return f"Error in general chat: {str(e)}"


# Import file system and system control tools
from src.brain.file_tools import FILE_TOOLS
from src.brain.system_tools import SYSTEM_TOOLS
# Import app control and AI text processing tools
from src.brain.app_tools import APP_TOOLS
from src.brain.ai_tools import AI_TOOLS


# ═══════════════════════════════════════════════════════════════════════════
# ASK_TOOLS - Safe Mode (Read-Only, No Actions)
# ═══════════════════════════════════════════════════════════════════════════
# CRITICAL: This list contains ONLY informational tools.
# NO file operations, NO system commands, NO app launching.
# Perfect for "Ask" mode where users expect information, not actions.

ASK_TOOLS = [
    # Web & Information Retrieval
    web_search_free,          # Primary web search (3-tier: Google→DDG→Tavily)
    search_wikipedia,         # Wikipedia summaries (Who/What questions)
    search_reddit_opinions,   # Reddit community opinions
    
    # Live Data Tools
    get_weather,              # Weather, temperature, umbrella questions
    get_stock_price,          # Stock/crypto prices
    get_definition,           # Word definitions
    is_website_down,          # Website status checks
    
    # System Info (Read-Only)
    get_clipboard,            # Read clipboard
    file_search,              # Find files (doesn't modify)
    get_disk_space,           # Disk usage info
    
    # AI Utilities
    general_chat,             # General Q&A
    paraphrase_text,          # Text improvement
]

# ═══════════════════════════════════════════════════════════════════════════
# ALL_TOOLS - Agent Mode (God Mode, Full Capabilities)
# ═══════════════════════════════════════════════════════════════════════════
# Contains EVERYTHING: read, write, execute, control system
# Use this for autonomous agent mode where full control is granted.

ALL_TOOLS = [
    # Safe tools from ASK_TOOLS
    *ASK_TOOLS,
    
    # Action tools (NOT in ASK_TOOLS - can modify system)
    web_search_tavily,        # Legacy Tavily (requires API key)
    clean_temp_files,         # Delete files
    open_app,                 # Launch applications
    chrome_search,            # Open browser
    set_clipboard,            # Modify clipboard
    
    # File system tools (8) - Can create/modify/delete files
    *FILE_TOOLS,
    
    # System control tools (7) - Can execute commands, control system
    *SYSTEM_TOOLS,
    
    # App control tools (10) - Can control applications
    *APP_TOOLS,
    
    # AI text processing tools (6)
    *AI_TOOLS
]

# Summary:
# - ASK_TOOLS: 13 safe, read-only tools (information retrieval only)
# - ALL_TOOLS: 13 + 26 = ~50+ tools (full system control)
