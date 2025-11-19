#!/usr/bin/env python3
"""
Agent Modes - AI-Powered Tool Selection with Delta (Ollama)

Uses Delta (qwen2.5:3b) to intelligently decide which tool to use.
NO hardcoded keywords - pure AI decision making!

Modes:
- ask_mode_agent: AI-powered tool selection via Delta (Ollama)
- agent_mode_full: Full autonomous mode with all 49 tools
"""

def ask_mode_agent(query: str, clipboard_text: str | None = None, progress_callback=None):
    """
    ASK MODE AGENT - AI-Powered Tool Selection
    
    Uses Delta (Ollama qwen2.5:3b) to intelligently decide which tool to use.
    The AI understands the query and picks the best tool - no hardcoding!
    
    Flow:
    1. User asks question
    2. Delta AI analyzes query
    3. Delta decides which tool to use
    4. Tool executes and returns answer
    5. Gemini only used as fallback or for final synthesis
    
    Args:
        query: User's question
        clipboard_text: Optional clipboard context
        progress_callback: Optional function to call with progress updates
        
    Returns:
        str: Answer to the query
    """
    import time
    
    def progress(msg):
        """Helper to send progress updates"""
        if progress_callback:
            progress_callback(msg)
        print(f"📊 {msg}")
    
    try:
        progress("🤖 AI analyzing query to select best tool...")
        
        # STEP 1: Ask Delta (Ollama) which tool to use
        routing_decision = _ask_delta_for_routing(query, progress)
        
        tool_name = routing_decision.get('tool', 'general_chat')
        params = routing_decision.get('params', {})
        reasoning = routing_decision.get('reasoning', 'No reasoning provided')
        
        progress(f"🎯 Delta decided: {tool_name}")
        progress(f"💭 Reasoning: {reasoning}")
        
        # STEP 2: Execute the tool Delta selected
        result = _execute_selected_tool(
            tool_name=tool_name,
            params=params,
            original_query=query,
            clipboard_text=clipboard_text,
            progress=progress
        )
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        return f"Error: {str(e)[:200]}\n\nPlease try rephrasing your question."


def _ask_delta_for_routing(query: str, progress_callback):
    """
    Ask Delta (Ollama) to decide which tool to use.
    
    This is the AI intelligence layer - no hardcoded keywords!
    """
    import requests
    import json
    import re
    
    tools_guide = """Available Tools:

1. get_weather
   Use when: User asks about weather, temperature, should take umbrella, rain, forecast
   Parameters: {"city": "city_name"}
   Example: "Should I take umbrella?" → get_weather

2. get_stock_price
   Use when: User asks about stock prices, crypto prices, market data
   Parameters: {"ticker": "AAPL"}
   Example: "What's Tesla stock?" → get_stock_price

3. search_wikipedia
   Use when: User asks "who is", "what is", "tell me about", biography, history
   Parameters: {"query": "search_term"}
   Example: "Who was Einstein?" → search_wikipedia

4. get_definition
   Use when: User asks "define", "meaning of", "what does X mean"
   Parameters: {"word": "word"}
   Example: "Define serendipity" → get_definition

5. is_website_down
   Use when: User asks if website is down, working, online, offline
   Parameters: {"url": "website.com"}
   Example: "Is Google down?" → is_website_down

6. search_reddit_opinions
   Use when: User asks about Reddit opinions, reviews, "best X", recommendations
   Parameters: {"topic": "query"}
   Example: "Best laptops Reddit" → search_reddit_opinions

7. web_search
   Use when: User asks about latest news, current events, recent information
   Parameters: {"query": "search_query"}
   Example: "Latest AI news" → web_search

8. general_chat
   Use when: General questions, conversations, anything else
   Parameters: {"query": "user_query"}
   Example: "Explain quantum physics" → general_chat
"""

    delta_prompt = f"""You are a smart tool router. Analyze the user's query and pick the BEST tool.

{tools_guide}

USER QUERY: "{query}"

Think:
- What is the user really asking?
- Which tool is BEST for this?
- What parameters does it need?

Respond with ONLY valid JSON (no markdown, no code blocks):
{{"tool": "tool_name", "params": {{"key": "value"}}, "reasoning": "why this tool"}}"""

    try:
        progress_callback("🧠 Asking Delta AI for decision...")
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'qwen2.5:3b',  # Fastest model (6s)
                'prompt': delta_prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,  # Low temperature for consistent routing
                    'num_predict': 150
                }
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result_text = response.json().get('response', '').strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result_json = json.loads(json_match.group(0))
                    return result_json
                except json.JSONDecodeError:
                    pass
        
        # Fallback if Delta fails
        progress_callback("⚠️  Delta routing failed, using fallback...")
        return {
            'tool': 'general_chat',
            'params': {'query': query},
            'reasoning': 'Delta unavailable, using fallback'
        }
        
    except Exception as e:
        progress_callback(f"⚠️  Delta error: {str(e)[:50]}")
        return {
            'tool': 'general_chat',
            'params': {'query': query},
            'reasoning': f'Error: {str(e)[:50]}'
        }


def _execute_selected_tool(tool_name: str, params: dict, original_query: str, 
                           clipboard_text: str | None, progress):
    """
    Execute the tool that Delta selected.
    """
    try:
        if tool_name == 'get_weather':
            from src.brain.live_tools import get_weather
            city = params.get('city', 'London')
            progress(f"🌤️  Getting weather for {city}...")
            return get_weather.invoke({"city": city})
        
        elif tool_name == 'get_stock_price':
            from src.brain.live_tools import get_stock_price
            ticker = params.get('ticker', 'AAPL')
            progress(f"💰 Fetching price for {ticker}...")
            return get_stock_price.invoke({"ticker": ticker})
        
        elif tool_name == 'search_wikipedia':
            from src.brain.live_tools import search_wikipedia
            topic = params.get('query', original_query)
            progress(f"📚 Searching Wikipedia for {topic[:50]}...")
            return search_wikipedia.invoke({"query": topic})
        
        elif tool_name == 'get_definition':
            from src.brain.live_tools import get_definition
            word = params.get('word', 'hello')
            progress(f"📖 Getting definition for '{word}'...")
            return get_definition.invoke({"word": word})
        
        elif tool_name == 'is_website_down':
            from src.brain.live_tools import is_website_down
            url = params.get('url', 'google.com')
            progress(f"🌐 Checking status of {url}...")
            return is_website_down.invoke({"url": url})
        
        elif tool_name == 'search_reddit_opinions':
            from src.brain.live_tools import search_reddit_opinions
            topic = params.get('topic', original_query)
            progress(f"💬 Searching Reddit for opinions...")
            return search_reddit_opinions.invoke({"topic": topic})
        
        elif tool_name == 'web_search':
            from src.rag.web_search import WebSearchRAG
            search_query = params.get('query', original_query)
            progress(f"🔍 Searching web...")
            
            rag = WebSearchRAG()
            results = rag.search(search_query, include_news=True)
            
            if results['sources_count'] > 0:
                progress(f"✅ Found {results['sources_count']} sources | 🤖 Generating answer...")
                
                from src.brain.tools_gemini import general_chat
                web_prompt = f"""Using these web search results, answer the question:

QUESTION: {original_query}

WEB RESULTS:
{results['context'][:3000]}

Provide a clear, accurate answer based on the web results above."""
                
                return general_chat(web_prompt)
            else:
                progress("⚠️  No web results, using AI knowledge...")
                from src.brain.tools_gemini import general_chat
                return general_chat(original_query)
        
        else:  # general_chat (default fallback)
            from src.brain.tools_gemini import general_chat
            
            # Use clipboard context if available
            if clipboard_text and len(clipboard_text.strip()) >= 5:
                progress(f"📋 Using clipboard context ({len(clipboard_text)} chars)")
                enhanced_query = f"""QUESTION: {original_query}

CLIPBOARD CONTEXT:
{clipboard_text[:4000]}

Answer the question based on the clipboard context above. Be clear and concise."""
                return general_chat(enhanced_query)
            else:
                progress("🤖 Generating answer...")
                return general_chat(original_query)
    
    except Exception as e:
        import traceback
        print(f"❌ Tool execution error: {e}\n{traceback.format_exc()}")
        # Fallback to general_chat
        from src.brain.tools_gemini import general_chat
        return general_chat(original_query)


def agent_mode_full(query: str, max_retries: int = 2, timeout: int = 90):
    """
    AGENT MODE - Full autonomous mode with all 49 tools
    """
    try:
        from src.brain.agent_core import execute_autonomous
        
        print(f"🤖 Agent Mode (Full) - Executing with all 49 tools...")
        result = execute_autonomous(query, max_retries=max_retries, timeout=timeout)
        
        return result
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Agent Mode Error: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        return f"Agent error: {str(e)[:200]}"


__all__ = ['ask_mode_agent', 'agent_mode_full']
