"""Decision Router for Project Synth

This module implements a lightweight, deterministic router that decides which
tool should be used for a given user query. The aim is to be conservative by
default (prefer local tools and free-tier Gemini models) and provide metadata
for UI and telemetry.

Contract:
- Input: query string, clipboard_text (maybe empty), config flags
- Output: dict with keys: action (local|llm|web|rag), tool (callable name), preferred_models (list), reason (str)

"""
from __future__ import annotations
from typing import Dict, List, TypedDict
import os
import re


def _is_research_query(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in ["what is", "who is", "when did", "explain", "define", "what does", "why does"]) or ('?' in query)


def _is_local_action(query: str) -> bool:
    q = query.lower()
    local_keywords = [
        'open', 'clean', 'cache', 'disk space', 'find file', 'locate file', 'chrome', 'open app', 'copy', 'clipboard', 'set clipboard'
    ]
    return any(k in q for k in local_keywords)


def _is_search(query: str) -> bool:
    q = query.lower()
    return 'search' in q or 'find' in q or 'latest' in q or 'news' in q or 'weather' in q


class Decision(TypedDict):
    action: str
    tool: str
    preferred_models: List[str]
    reason: str


def decide_tool(query: str, clipboard_text: str | None = None) -> Decision:
    """Decide the tool and preferred models for a given query.

    Returns a dict with keys: action, tool, preferred_models, reason
    """
    # Quick normalizations
    q = (query or '').strip()
    clip = clipboard_text or ''
    q_lower = q.lower()

    # Default preferred models come from tools_gemini.get_preferred_model_names() if available
    try:
        from src.brain.tools_gemini import get_preferred_model_names
        genai_model, langchain_model = get_preferred_model_names()
        preferred_models = [genai_model]
    except Exception:
        # fallback hard-coded free-tier preferences
        preferred_models = ['gemini-2.0-flash-lite', 'gemini-2.0-flash', 'gemini-1.5-flash']

    # Local actions: quick tool returns
    if _is_local_action(q):
        return {
                'action': 'local',
                'tool': 'local_tools',
                'preferred_models': [],
                'reason': 'Local pattern detected'
            }

    # Explicit search patterns prefer web search
    if _is_search(q):
        return {
                'action': 'web',
                'tool': 'web_search',
                'preferred_models': preferred_models,
                'reason': 'Search-like query'
            }

    # If clipboard text is provided and the user asked for explain/paraphrase/summarize
    if clip and any(k in q_lower for k in ['explain', 'paraphrase', 'summarize', 'rewrite', 'rephrase']):
        return {
                'action': 'llm',
                'tool': 'llm_explain' if 'explain' in q_lower else 'llm_paraphrase' if 'paraphrase' in q_lower else 'llm_summarize',
                'preferred_models': preferred_models,
                'reason': 'Clipboard + explain/paraphrase/summarize'
            }

    # If it looks like a technical research question, prefer web + llm
    if _is_research_query(q):
        return {
            'action': 'llm',
            'tool': 'llm_general_chat',
            'preferred_models': preferred_models,
            'reason': 'Research-style question'
        }

    # Fallback default - prefer LLM for generic queries
    return {
        'action': 'llm',
        'tool': 'llm_general_chat',
        'preferred_models': preferred_models,
        'reason': 'Default to LLM for generic queries'
    }


def decide_tool_for_copy_and_explain(clipboard_text: str) -> Decision:
    """Explicit helper when the user asks 'explain' on clipboard - ensures LLM"""
    preferred_models = ['gemini-2.0-flash-lite', 'gemini-2.0-flash', 'gemini-1.5-flash']
    try:
        from src.brain.tools_gemini import get_preferred_model_names
        genai_model, _ = get_preferred_model_names()
        preferred_models = [genai_model]
    except Exception:
        pass

    return {
        'action': 'llm',
        'tool': 'llm_explain',
        'preferred_models': preferred_models,
        'reason': 'Clipboard explain'
    }
