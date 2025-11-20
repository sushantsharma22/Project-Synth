#!/usr/bin/env python3
"""
Agent Modes - AI-Powered Tool Selection with Delta (Ollama)

Uses Delta (qwen2.5:3b) to intelligently decide which tool to use.
NO hardcoded keywords - pure AI decision making!

Modes:
- ask_mode_agent: AI-powered tool selection via Delta (Ollama)
- agent_mode_full: Full autonomous mode with all 49 tools
"""

def ask_mode_agent(query: str, clipboard_text: str | None = None, progress_callback=None, log_callback=None):
    """
    ASK MODE AGENT - AI-Powered Tool Selection with LOCAL-FIRST Architecture
    
    Uses Delta (Ollama qwen2.5:3b) to intelligently decide which tool to use.
    NOW WITH: Local-First, Cloud-Fallback + Detailed Logging!
    
    Flow:
    1. User asks question
    2. Delta AI analyzes query → selects tool
    3. Tool executes → returns raw data  
    4. Brain humanizes output (Local-First, Gemini Fallback)
    5. User gets friendly response + detailed logs
    
    Args:
        query: User's question
        clipboard_text: Optional clipboard context
        progress_callback: Optional function(msg) for UI updates
        log_callback: Optional function(event, data) for detailed logging
        
    Returns:
        str: Humanized, friendly answer
    """
    import time
    
    def progress(msg):
        """Helper to send progress updates"""
        if progress_callback:
            progress_callback(msg)
        print(f"📊 {msg}")
    
    def log_event(event_type, data):
        """Helper to log events"""
        if log_callback:
            log_callback(event_type, data)
    
    try:
        progress("🤖 AI analyzing query to select best tool...")
        log_event("ROUTING_START", {"query": query})
        
        # STEP 1: Ask Delta (Ollama) which tool to use
        routing_decision = _ask_delta_for_routing(query, progress)
        
        tool_name = routing_decision.get('tool', 'general_chat')
        params = routing_decision.get('params', {})
        reasoning = routing_decision.get('reasoning', 'No reasoning provided')
        
        progress(f"🎯 Delta decided: {tool_name}")
        progress(f"💭 Reasoning: {reasoning}")
        
        log_event("TOOL_SELECTED", {
            "tool": tool_name,
            "params": params,
            "reasoning": reasoning
        })
        
        # STEP 2: Execute the tool Delta selected
        raw_result = _execute_selected_tool(
            tool_name=tool_name,
            params=params,
            original_query=query,
            clipboard_text=clipboard_text,
            progress=progress,
            log_callback=log_callback  # Pass logging function
        )
        
        log_event("TOOL_EXECUTED", {
            "tool": tool_name,
            "result_length": len(raw_result),
            "result_preview": raw_result[:200]
        })
        
        # STEP 3: SYNTHESIS PIPELINE - Humanize the output
        # Skip humanization for tools that already return friendly text
        skip_humanization = tool_name in ['general_chat', 'web_search']
        
        if skip_humanization:
            log_event("HUMANIZATION_SKIPPED", {"reason": "Tool already friendly"})
            return raw_result
        
        progress("✨ Making response friendly...")
        log_event("HUMANIZATION_START", {"input_length": len(raw_result)})
        
        # Import DeltaBrain for humanization
        from brain_client import DeltaBrain
        brain = DeltaBrain()
        
        # Humanize with logging
        def humanize_log(msg):
            progress(msg)
            log_event("HUMANIZATION_LOG", {"message": msg})
        
        # Humanize the raw tool output (LOCAL-FIRST!)
        friendly_result = brain.humanize_tool_output(
            query=query,
            tool_output=raw_result,
            tool_name=tool_name,
            log_callback=humanize_log
        )
        
        log_event("HUMANIZATION_COMPLETE", {
            "output_length": len(friendly_result),
            "model_used": "Delta-Local-or-Gemini-Fallback"
        })
        
        return friendly_result
        
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

get_weather
- Provides current weather conditions and forecast for a city
- Parameters: {"city": "city_name"}

get_stock_price
- Retrieves current stock or cryptocurrency prices
- Parameters: {"ticker": "AAPL"}

search_wikipedia
- Searches Wikipedia for general knowledge, biographies, history
- Parameters: {"query": "search_term"}

get_definition
- Looks up dictionary definition of a word
- Parameters: {"word": "word"}

is_website_down
- Checks if a website is currently accessible
- Parameters: {"url": "website.com"}

search_reddit_opinions
- Searches Reddit for community discussions and opinions
- Parameters: {"topic": "query"}

web_search
- Searches the web for information, finds reports, compares products, gets latest news, research papers, technical documentation, benchmarks, specs, reviews, how-to guides, current events
- Parameters: {"query": "search_query"}

general_chat
- Direct AI conversation without external tools for explanations, discussions, creative writing, personal questions
- Parameters: {"query": "user_query"}"""

    delta_prompt = f"""You are an intelligent tool router. Analyze the user's query and select the BEST tool to answer it.

{tools_guide}

USER QUERY: "{query}"

THINK CAREFULLY:
1. What information does the user need?
2. Which tool can provide that information most directly?
3. What parameters does that tool need?

If the user needs to:
- Find/search/research/compare/get reports/latest info → Consider which tool searches that type of content
- Get weather/forecast → Consider weather tool
- Check stock/crypto prices → Consider stock tool
- Learn about a person/place/thing → Consider which tools provide that knowledge
- Get word meaning → Consider definition tool
- Check website status → Consider website tool
- See community opinions → Consider opinion tools
- Have a conversation/explanation → Consider chat tool

BE SMART. CHOOSE THE TOOL THAT BEST MATCHES WHAT THE USER ACTUALLY NEEDS.

Respond with ONLY valid JSON (no markdown, no explanations, no code blocks):
{{"tool": "tool_name", "params": {{"key": "value"}}, "reasoning": "brief explanation"}}"""

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
                           clipboard_text: str | None, progress, log_callback=None):
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
            from brain_client import DeltaBrain
            
            search_query = params.get('query', original_query)
            progress(f"🔍 Searching web...")
            
            rag = WebSearchRAG()
            results = rag.search(search_query, include_news=True)
            
            if results['sources_count'] > 0:
                progress(f"✅ Found {results['sources_count']} sources | 🤖 Generating answer...")
                
                # USE DELTA BRAIN with Local-First, Cloud-Fallback!
                brain = DeltaBrain()
                
                def synthesis_log(msg):
                    progress(msg)
                    if log_callback:
                        log_callback("SYNTHESIS_LOG", {"message": msg})
                
                answer, model_used = brain.synthesize_web_results(
                    query=original_query,
                    search_results=results,
                    log_callback=synthesis_log
                )
                
                if log_callback:
                    log_callback("SYNTHESIS_COMPLETE", {
                        "model_used": model_used,
                        "answer_length": len(answer)
                    })
                
                return answer
            else:
                progress("⚠️  No web results, using AI knowledge...")
                # Fallback to general chat if no search results
                from brain_client import DeltaBrain
                brain = DeltaBrain()
                response, model_used = brain.safe_ask(
                    original_query,
                    mode="balanced",
                    log_callback=lambda msg: progress(msg) if progress else None
                )
                return response
        
        else:  # general_chat (default fallback)
            from brain_client import DeltaBrain
            brain = DeltaBrain()
            
            # Use clipboard context if available
            if clipboard_text and len(clipboard_text.strip()) >= 5:
                progress(f"📋 Using clipboard context ({len(clipboard_text)} chars)")
                enhanced_query = f"""QUESTION: {original_query}

CLIPBOARD CONTEXT:
{clipboard_text[:4000]}

Answer the question based on the clipboard context above. Be clear and concise."""
                
                response, model_used = brain.safe_ask(
                    enhanced_query,
                    mode="balanced",
                    log_callback=lambda msg: progress(msg) if progress else None
                )
                
                if log_callback:
                    log_callback("CHAT_COMPLETE", {"model_used": model_used})
                
                return response
            else:
                progress("🤖 Generating answer...")
                response, model_used = brain.safe_ask(
                    original_query,
                    mode="balanced",
                    log_callback=lambda msg: progress(msg) if progress else None
                )
                
                if log_callback:
                    log_callback("CHAT_COMPLETE", {"model_used": model_used})
                
                return response
    
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
