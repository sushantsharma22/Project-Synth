"""
AI Text Processing Tools for Project Synth Autonomous Agent
Provides AI-powered text operations using Gemini

Author: Sushant Sharma
Date: November 17, 2025
"""

import os
from dotenv import load_dotenv
from langchain.tools import tool

# Load environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check for LangChain Google GenAI
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_LANGCHAIN_GOOGLE_GENAI = True
except ImportError:
    HAS_LANGCHAIN_GOOGLE_GENAI = False


@tool
def summarize_text(text: str) -> str:
    """Create concise bullet-point summary. Use for long articles, documents, or web pages.
    
    Args:
        text: Text to summarize
        
    Returns:
        Bullet-point summary
    """
    try:
        if not HAS_LANGCHAIN_GOOGLE_GENAI:
            # Fallback to tools_gemini
            from src.brain.tools_gemini import general_chat
            return general_chat(f"Summarize in clear bullet points:\n\n{text}")
        
        # Use preferred model
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,
            max_tokens=400
        )
        
        prompt = f"Summarize this in clear bullet points:\n\n{text}"
        response = llm.invoke(prompt)
        
        return f"📝 Summary:\n{response.content}"
        
    except Exception as e:
        return f"❌ Error summarizing: {str(e)}"


@tool
def translate_text(text: str, target_language: str) -> str:
    """Translate text to another language. Examples: Spanish, French, Hindi, Japanese.
    
    Args:
        text: Text to translate
        target_language: Target language name
        
    Returns:
        Translated text
    """
    try:
        if not HAS_LANGCHAIN_GOOGLE_GENAI:
            # Fallback to tools_gemini
            from src.brain.tools_gemini import general_chat
            return general_chat(f"Translate to {target_language}:\n\n{text}")
        
        # Use preferred model
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        
        prompt = f"Translate this text to {target_language}. Only return the translation:\n\n{text}"
        response = llm.invoke(prompt)
        
        return f"🌐 Translation ({target_language}):\n{response.content}"
        
    except Exception as e:
        return f"❌ Error translating: {str(e)}"


@tool
def explain_concept(concept: str) -> str:
    """Explain any concept, term, or topic in simple language.
    
    Args:
        concept: Concept or topic to explain
        
    Returns:
        Simple explanation
    """
    try:
        if not HAS_LANGCHAIN_GOOGLE_GENAI:
            # Fallback to tools_gemini
            from src.brain.tools_gemini import general_chat
            return general_chat(f"Explain in simple terms: {concept}")
        
        # Use preferred model
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.5
        )
        
        prompt = f"Explain '{concept}' in simple, easy-to-understand language. Use examples if helpful."
        response = llm.invoke(prompt)
        
        return f"💡 Explanation:\n{response.content}"
        
    except Exception as e:
        return f"❌ Error explaining: {str(e)}"


@tool
def code_explain(code: str) -> str:
    """Explain what code does line by line.
    
    Args:
        code: Code to explain
        
    Returns:
        Code explanation
    """
    try:
        if not HAS_LANGCHAIN_GOOGLE_GENAI:
            # Fallback to tools_gemini
            from src.brain.tools_gemini import general_chat
            return general_chat(f"Explain this code clearly:\n\n{code}")
        
        # Use preferred model
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.3
        )
        
        prompt = f"""Explain what this code does, line by line if needed:

{code}

Provide a clear, detailed explanation."""
        response = llm.invoke(prompt)
        
        return f"💻 Code Explanation:\n{response.content}"
        
    except Exception as e:
        return f"❌ Error explaining code: {str(e)}"


@tool
def code_debug(code: str, error: str) -> str:
    """Debug code errors and provide fixes. Use when user has error messages.
    
    Args:
        code: Code with error
        error: Error message
        
    Returns:
        Fix suggestions
    """
    try:
        if not HAS_LANGCHAIN_GOOGLE_GENAI:
            # Fallback to tools_gemini
            from src.brain.tools_gemini import general_chat
            return general_chat(f"Fix this error in code:\n\nCode:\n{code}\n\nError:\n{error}")
        
        # Use preferred model
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,
            max_tokens=500
        )
        
        prompt = f"""Debug this code error and provide a fix:

CODE:
{code}

ERROR:
{error}

Provide:
1. What's causing the error
2. How to fix it
3. Corrected code if needed"""
        
        response = llm.invoke(prompt)
        
        return f"🔧 Debug Solution:\n{response.content}"
        
    except Exception as e:
        return f"❌ Error debugging: {str(e)}"


@tool
def improve_writing(text: str) -> str:
    """Improve grammar, clarity, and professionalism of text.
    
    Args:
        text: Text to improve
        
    Returns:
        Improved version
    """
    try:
        if not HAS_LANGCHAIN_GOOGLE_GENAI:
            # Fallback to tools_gemini paraphrase
            from src.brain.tools_gemini import paraphrase_text
            return paraphrase_text(text)
        
        # Use preferred model
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.5
        )
        
        prompt = f"""Improve this text for clarity, grammar, and professionalism. Keep the same meaning but make it better:

{text}

Return only the improved version."""
        
        response = llm.invoke(prompt)
        
        return f"✨ Improved Writing:\n{response.content}"
        
    except Exception as e:
        return f"❌ Error improving writing: {str(e)}"


# Export all AI tools
AI_TOOLS = [
    summarize_text,
    translate_text,
    explain_concept,
    code_explain,
    code_debug,
    improve_writing
]
