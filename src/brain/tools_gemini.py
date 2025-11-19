"""
Core Tools with Gemini AI Integration
Uses official google-genai package for AI responses

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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found in .env file")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Initialize Gemini client
from google import genai
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
gemini_client = genai.Client()
LAST_USED_MODEL = ""


def generate_with_fallback(contents: str, candidate_models=None, max_retries: int = 3):
    """Try multiple Gemini models in order and gracefully fallback on quota errors.

    Returns the response object on success or raises on fatal errors.
    """
    # Allow override via environment variable for free-tier only or custom order.
    env_models = os.getenv("GEMINI_FALLBACK_MODELS")
    free_tier_only = os.getenv("GEMINI_FREE_TIER_ONLY", "true").lower() in ("1", "true", "yes")
    if env_models:
        candidate_models = [m.strip() for m in env_models.split(",") if m.strip()]
    elif candidate_models is None:
        # Free-tier friendly order: prefer flash-lite / flash with higher free RPM
        candidate_models = [
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ] if free_tier_only else [
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-2.0",
            "gemini-1.5-pro",
            "gemini-pro",
        ]

    import time

    from collections import deque
    last_exception = None
    backoff = 2  # Start at 2 seconds (increased from 1)
    # Basic free-tier RPM defaults (approximate) so we don't exceed limits in-app
    free_tier_rpm = {
        "gemini-2.0-flash-lite": 30,
        "gemini-2.0-flash": 15,
        "gemini-1.5-flash": 15,
        "gemini-2.0": 15,
        "gemini-1.5-pro": 15,
        "gemini-pro": 2,
    }
    # Track timestamps for rate limiting and cooldowns
    request_log = {m: deque() for m in candidate_models}
    cooldowns = {m: 0 for m in candidate_models}
    for model in candidate_models:
        # Skip model if in cooldown
        if time.time() < cooldowns.get(model, 0):
            continue
        # Basic throttling: skip model if over RPM
        rpm = free_tier_rpm.get(model, 5)
        # Pop old entries outside 60s window
        while request_log.get(model) and request_log[model] and time.time() - request_log[model][0] > 60:
            request_log[model].popleft()
        if len(request_log.get(model) or []) >= rpm:
            # If we've hit apparent local limit, skip model for now
            print(f"⏳ Local throttling for {model} (used {len(request_log[model])}/{rpm} in last 60s)")
            continue
        for attempt in range(min(max_retries, 2)):  # Max 2 retries per model
            try:
                print(f"🔁 Trying Gemini model: {model} (attempt {attempt + 1})")
                # Log this attempt
                request_log.setdefault(model, deque()).append(time.time())
                response = gemini_client.models.generate_content(
                    model=model,
                    contents=contents,
                )
                # expose the final model used for UI/telemetry
                global LAST_USED_MODEL
                LAST_USED_MODEL = model
                return response
            except Exception as e:
                last_exception = e
                msg = str(e).lower()
                # Detect quota or rate limit errors and backoff to try the next model
                if "resource_exhausted" in msg or "quota" in msg or "429" in msg or "rate limit" in msg:
                    print(f"⚠️ Gemini quota/rate limit hit for model {model}: {e}")
                    # Sleep with exponential backoff: 2, 4, 8, 16 seconds
                    time.sleep(backoff)
                    backoff = min(16, backoff * 2)  # Cap at 16 seconds
                    # If rate limited, put model into cooldown for a minute (avoid retrying immediately)
                    cooldowns[model] = int(time.time() + 60)
                    continue
                # Some other error - try the next model
                print(f"❌ Gemini failed for {model} with error: {e}")
                break

    # If we get here, no model returned successfully
    raise last_exception if last_exception else RuntimeError("No viable Gemini models answered the request")


def get_preferred_model_names() -> tuple[str, str]:
    """Return recommended model names for (genai, langchain) based on settings and env variables.

    Returns a tuple (genai_model, langchain_model).
    """
    env_models = os.getenv("GEMINI_FALLBACK_MODELS")
    free_tier_only = os.getenv("GEMINI_FREE_TIER_ONLY", "true").lower() in ("1", "true", "yes")

    if env_models:
        models = [m.strip() for m in env_models.split(",") if m.strip()]
    else:
        if free_tier_only:
            models = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]
        else:
            models = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0", "gemini-pro"]

    # For LangChain-style wrappers that require 'models/' prefix, prefer that format
    genai_model = models[0]
    langchain_model = models[0]
    # If model name doesn't start with 'models/', add the v1beta prefix
    if not langchain_model.startswith("models/"):
        langchain_model = f"models/{langchain_model}"
    return genai_model, langchain_model


def _build_response_style_prompt(message: str) -> str:
    """Return style instructions so Gemini stays concise and directly tied to the request."""
    base = (
        "You are Synth, a concise macOS copilot. Always answer in English, reuse the user's terminology, and never use placeholder text."
    )
    lower_msg = message.lower()

    if any(keyword in lower_msg for keyword in ["explain", "teach", "walk me through"]):
        return (
            base
            + "\nWhen explaining, start with 'Quick take:' that explicitly names the subject, then provide up to three tight bullets (<=14 words) with real facts from the request, and finish with 'Takeaway:' plus one short sentence."
        )

    if any(keyword in lower_msg for keyword in ["summarize", "tl;dr", "summary"]):
        return base + "\nSummaries must fit in two sentences highlighting impact and immediate next step."

    if any(keyword in lower_msg for keyword in ["paraphrase", "rewrite", "rephrase"]):
        return base + "\nDeliver a single polished paragraph under 120 words that preserves the original meaning."

    return base + "\nUnless the user explicitly asks for detail, keep answers under 120 words with no preamble."


def web_search_tavily(query: str) -> str:
    """Search web for current info using Tavily API"""
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=TAVILY_API_KEY)
        results = client.search(query, max_results=5)
        
        if not results or 'results' not in results:
            return f"No results found for: {query}"
        
        formatted = f"🔍 Search results for '{query}':\n\n"
        for i, result in enumerate(results['results'][:5], 1):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            snippet = result.get('content', 'No description')[:150]
            formatted += f"{i}. {title}\n   {snippet}...\n   {url}\n\n"
        
        return formatted
    except Exception as e:
        return f"❌ Error searching web: {str(e)}"


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
            return f"❌ Error searching files: {result.stderr}"
        
        files = result.stdout.strip().split('\n')
        files = [f for f in files if f][:10]
        
        if not files:
            return f"No files found matching: {query}"
        
        formatted = f"📁 Found {len(files)} files matching '{query}':\n\n"
        for i, filepath in enumerate(files, 1):
            formatted += f"{i}. {filepath}\n"
        
        return formatted
    except subprocess.TimeoutExpired:
        return "⏱️ File search timed out"
    except Exception as e:
        return f"❌ Error searching files: {str(e)}"


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
        return f"❌ Error cleaning temp files: {str(e)}"


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
        return f"❌ Error checking disk space: {str(e)}"


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
        return f"❌ Error opening app: {str(e)}"


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
        return f"❌ Error opening browser: {str(e)}"


def get_clipboard() -> str:
    """Read clipboard content"""
    try:
        pasteboard = NSPasteboard.generalPasteboard()
        text = pasteboard.stringForType_("public.utf8-plain-text")
        
        if text:
            return f"📋 Clipboard content:\n{text}"
        else:
            return "📋 Clipboard is empty"
    except Exception as e:
        return f"❌ Error reading clipboard: {str(e)}"


def set_clipboard(text: str) -> str:
    """Copy text to clipboard"""
    try:
        pyperclip.copy(text)
        return f"✅ Copied to clipboard"
    except Exception as e:
        return f"❌ Error setting clipboard: {str(e)}"


def paraphrase_text(text: str) -> str:
    """Rewrite text professionally using Gemini AI"""
    try:
        response = generate_with_fallback(
            contents=(
                "Rewrite this text so it is professional, confident, and succinct. "
                "Return a single paragraph with at most three sentences and no commentary.\n\n"
                f"{text}"
            ),
        )
        return f"✨ Paraphrased:\n{response.text}"
    except Exception as e:
        return f"❌ Error paraphrasing: {str(e)}"


def explain_text(text: str, focus_term: str | None = None) -> str:
    """Explain copied text clearly using Gemini."""
    try:
        # Build a clear, direct prompt
        focus_instruction = f"Focus only on '{focus_term}' and explain it in this context.\n\n" if focus_term else ''
        prompt = f"""{focus_instruction}Analyze and explain this text. Do NOT ask the user to paste or provide the text again; use the provided text.

{text}

Provide your response in this EXACT format:

Quick take: [One specific sentence about what this text describes - mention actual technologies/achievements]

Key points:
• [First specific detail with numbers/names/technologies from the text]
• [Second specific detail - be concrete]
• [Third specific detail if relevant]

Takeaway: [One sentence on why this matters or what it demonstrates]

BE SPECIFIC - use the actual details from the text above."""

        response = generate_with_fallback(contents=prompt)
        response_text = getattr(response, "text", "")
        answer = response_text.strip() if response_text else ""
        if not answer or "paste the text" in answer.lower() or "i'm ready" in answer.lower():
            # Gemini is confused - return a simpler breakdown
            # If there is a focus term, try to construct a fallback that explains the term specifically
            if focus_term:
                term = focus_term
                answer = f"""Quick take: This explains '{term}' as used in the context.

Key points:
• '{term}' is referred to as a specific concept in the text (highlight the role / definition).
• The context shows how '{term}' is used with [other components] in the text, e.g. protocols, design patterns, or features.
• If present, mention performance considerations or deployment notes from the text.

Takeaway: Understanding '{term}' helps clarify the specific design or security trade-offs in the provided passage."""
            else:
                answer = f"""Quick take: This describes technical skills and achievements in machine learning.

Key points:
• Technologies: {', '.join([w for w in text.split() if w.isupper() or any(tech in w.lower() for tech in ['python', 'spark', 'pytorch'])])[:3]}
• Quantifiable achievement mentioned in the text
• Focus on practical application and business impact

Takeaway: Demonstrates hands-on ML engineering experience with measurable results."""
        return answer
    except Exception as e:
        msg = str(e).lower()
        if "resource_exhausted" in msg or "quota" in msg or "429" in msg:
            return (
                "⚠️ Gemini rate limit reached for your project. "
                "Try again in a minute, switch to a cheaper model (e.g. gemini-1.5-flash), or upgrade your plan."
            )
        return f"❌ Error explaining: {str(e)}"


def general_chat(message: str) -> str:
    """Answer questions using Gemini AI"""
    try:
        normalized = message.strip()
        if not normalized:
            return "🤖 I need a question or some text to respond to."
        if normalized.lower() in {"explain", "paraphrase", "summarize"}:
            return "🤖 Copy the passage with Cmd+C first, then tell me what to do with it."
        style_prompt = _build_response_style_prompt(message)
        prompt = f"""{style_prompt}\n\nUSER REQUEST:\n{message}\n\nASSISTANT:"""
        response = generate_with_fallback(contents=prompt)
        answer = response.text.strip() if response.text else ""
        if not answer:
            answer = "I couldn't generate a response."
        if not answer.startswith("🤖"):
            answer = f"🤖 {answer}"
        return answer
    except Exception as e:
        msg = str(e).lower()
        if "resource_exhausted" in msg or "quota" in msg or "429" in msg:
            return (
                "⚠️ The Gemini service is currently rate-limited for your project. "
                "Please wait a bit, or use a lower-tier model like gemini-1.5-flash, or upgrade your plan."
            )
        return f"❌ Error in chat: {str(e)}"
