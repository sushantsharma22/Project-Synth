"""
Agent Modes for Synth - ReAct Iterative Agents
Implements iterative planning and tool execution for Chat, Ask, and Agent modes

Author: Sushant Sharma
Date: November 18, 2025
"""

import os
from typing import Optional, Callable
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if LangChain is available
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    print("⚠️  LangChain not installed. Run: pip install langchain langchain-community")

from src.brain.core_tools import CHAT_TOOLS, ASK_TOOLS, ALL_TOOLS


# ═══════════════════════════════════════════════════════════════════════
# CHAT MODE AGENT - Conversational with Web Search Iteration
# ═══════════════════════════════════════════════════════════════════════

def chat_mode_agent(
    query: str,
    conversation_context: str = "",
    progress_callback: Optional[Callable[[str], None]] = None,
    max_iterations: int = 5
) -> str:
    """
    Chat mode with iterative web search and synthesis.
    
    Process:
    1. Analyze query - identify topics needing research
    2. Execute web searches for each topic
    3. Check completeness - search again if needed
    4. Synthesize all findings into coherent answer
    5. Cite sources
    
    Args:
        query: User's question
        conversation_context: Previous conversation (last 10 messages)
        progress_callback: Function to show progress updates
        max_iterations: Maximum tool calls (default 5)
        
    Returns:
        Synthesized answer with sources
    """
    
    if not HAS_LANGCHAIN:
        # Fallback to simple general_chat if LangChain not available
        from src.brain.tools_gemini import general_chat
        return general_chat(query)
    
    def show_progress(msg: str):
        """Show progress if callback provided"""
        if progress_callback:
            progress_callback(msg)
    
    try:
        # Initialize LLM with Gemini
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        )
        
        # Create ReAct agent with CHAT_TOOLS (web search + general_chat)
        agent = create_react_agent(llm, CHAT_TOOLS)
        
        # Build system prompt for chat mode
        current_date = datetime.now().strftime("%B %d, %Y")
        current_time = datetime.now().strftime("%I:%M %p")
        
        system_prompt = f"""You are Synth Chat - an intelligent conversational assistant.
Current date: {current_date} at {current_time}

CONVERSATION CONTEXT:
{conversation_context if conversation_context else "No previous conversation"}

YOUR CAPABILITIES:
- Web search for current events, news, facts, recent information
- General conversation and knowledge synthesis

YOUR APPROACH:
When user asks about current events or multiple topics:
1. Break question into separate topics if needed
2. Use web_search_tavily for EACH topic separately
3. After each search, evaluate: "Do I have complete information?"
4. If incomplete or need more details, search again with refined query
5. Once you have sufficient data, use general_chat to synthesize
6. Combine all findings into one coherent answer
7. Always cite sources at the end

CRITICAL RULES:
- Search for each topic individually (don't try to combine in one search)
- If question has 3 topics, make 3 separate searches
- Check results after each search - if insufficient, search again
- Use specific queries (e.g., "Himachal elections 2025 results" not "elections")
- Always include sources with URLs at the bottom
- Keep final answer conversational and comprehensive (300-500 words)

USER QUERY:
{query}

Think step by step:
1. Identify topics needing research
2. Search for each topic
3. Check if you have complete info
4. Synthesize final answer with all sources"""
        
        # Show planning progress
        show_progress("💭 Planning approach...")
        
        # Invoke agent with streaming to capture intermediate steps
        iteration_count = 0
        final_response = None
        
        for chunk in agent.stream(
            {"messages": [HumanMessage(content=system_prompt)]},
            {"recursion_limit": max_iterations + 10}
        ):
            iteration_count += 1
            
            # Extract progress from agent's thoughts
            if "agent" in chunk:
                agent_msg = chunk["agent"]["messages"][0]
                
                # Check if it's a tool call
                if hasattr(agent_msg, "tool_calls") and agent_msg.tool_calls:
                    for tool_call in agent_msg.tool_calls:
                        tool_name = tool_call.get("name", "unknown")
                        if tool_name == "web_search_tavily":
                            args = tool_call.get("args", {})
                            search_query = args.get("query", "")[:50]
                            show_progress(f"🔍 Searching: {search_query}... ({iteration_count}/{max_iterations})")
                        elif tool_name == "general_chat":
                            show_progress(f"🤖 Synthesizing answer... ({iteration_count}/{max_iterations})")
                
                # Check for final answer
                if hasattr(agent_msg, "content") and agent_msg.content:
                    final_response = agent_msg.content
            
            # Check for tools output
            if "tools" in chunk:
                tools_msg = chunk["tools"]["messages"][0]
                if hasattr(tools_msg, "content"):
                    # Tool executed successfully
                    show_progress(f"✅ Retrieved data ({iteration_count}/{max_iterations})")
        
        show_progress("✅ Complete! Formatting answer...")
        
        # Return final response
        if final_response:
            # Clean up response (remove any agent artifacts)
            response = str(final_response)
            if isinstance(final_response, list):
                response = "\n".join(str(r) for r in final_response)
            return response
        else:
            return "I encountered an issue processing your request. Please try again."
            
    except Exception as e:
        import traceback
        error_msg = f"❌ Chat mode error: {str(e)[:200]}"
        print(f"Chat mode error:\n{traceback.format_exc()}")
        
        # Fallback to simple chat
        try:
            from src.brain.tools_gemini import general_chat
            show_progress("⚠️ Fallback to simple mode...")
            return general_chat(query)
        except:
            return error_msg


# ═══════════════════════════════════════════════════════════════════════
# ASK MODE AGENT - Smart Q&A with Enhanced Tools
# ═══════════════════════════════════════════════════════════════════════

def ask_mode_agent(
    query: str,
    clipboard_text: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    max_iterations: int = 5
) -> str:
    """
    Ask mode with web search, clipboard analysis, and text processing.
    
    Process:
    1. Analyze what user is asking
    2. Check if clipboard context is needed
    3. Use web search for current info
    4. Use AI tools for text processing (explain, summarize, etc.)
    5. Combine findings into final answer
    
    Args:
        query: User's question
        clipboard_text: Text user copied (if available)
        progress_callback: Function to show progress
        max_iterations: Maximum tool calls
        
    Returns:
        Comprehensive answer
    """
    
    if not HAS_LANGCHAIN:
        # Fallback to simple approach
        from src.brain.tools_gemini import general_chat
        enhanced_query = query
        if clipboard_text:
            enhanced_query = f"{query}\n\nContext:\n{clipboard_text[:2000]}"
        return general_chat(enhanced_query)
    
    def show_progress(msg: str):
        if progress_callback:
            progress_callback(msg)
    
    try:
        # Initialize LLM
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_model = get_preferred_model_names()
        
        llm = ChatGoogleGenerativeAI(
            model=preferred_model,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7
        )
        
        # Create ReAct agent with ASK_TOOLS (11 tools)
        agent = create_react_agent(llm, ASK_TOOLS)
        
        # Build system prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        clipboard_context = ""
        if clipboard_text:
            clipboard_context = f"\n\nCLIPBOARD TEXT (User copied this):\n{clipboard_text[:2000]}"
        
        system_prompt = f"""You are Synth Assistant - a smart Q&A helper.
Current date: {current_date}

YOUR TOOLS:
- web_search_tavily: Search for current facts, news, events
- get_clipboard: Read what user copied
- Text AI tools: explain, summarize, paraphrase, analyze
- general_chat: Synthesize answers

YOUR APPROACH:
For each query:
1. Determine what information is needed
2. If asking about copied text, use get_clipboard first
3. If needs current info, use web_search_tavily
4. If explaining/analyzing text, use appropriate AI tool
5. Check results - if incomplete, use more tools
6. Synthesize final answer combining all data
7. Maximum {max_iterations} tool calls

RULES:
- Be thorough but efficient (don't waste tool calls)
- Cite sources when using web search
- For clipboard queries, focus on the user's text
- Keep answers comprehensive (200-400 words)
{clipboard_context}

USER QUERY:
{query}"""
        
        show_progress("💭 Analyzing request...")
        
        # Invoke agent
        iteration_count = 0
        final_response = None
        
        for chunk in agent.stream(
            {"messages": [HumanMessage(content=system_prompt)]},
            {"recursion_limit": max_iterations + 10}
        ):
            iteration_count += 1
            
            if "agent" in chunk:
                agent_msg = chunk["agent"]["messages"][0]
                
                if hasattr(agent_msg, "tool_calls") and agent_msg.tool_calls:
                    for tool_call in agent_msg.tool_calls:
                        tool_name = tool_call.get("name", "unknown")
                        show_progress(f"🔧 Using: {tool_name}... ({iteration_count}/{max_iterations})")
                
                if hasattr(agent_msg, "content") and agent_msg.content:
                    final_response = agent_msg.content
            
            if "tools" in chunk:
                show_progress(f"✅ Tool complete ({iteration_count}/{max_iterations})")
        
        show_progress("✅ Complete!")
        
        if final_response:
            response = str(final_response)
            if isinstance(final_response, list):
                response = "\n".join(str(r) for r in final_response)
            return response
        else:
            return "I couldn't complete your request. Please try rephrasing."
            
    except Exception as e:
        import traceback
        print(f"Ask mode error:\n{traceback.format_exc()}")
        
        # Fallback
        try:
            from src.brain.tools_gemini import general_chat
            show_progress("⚠️ Fallback mode...")
            enhanced_query = query
            if clipboard_text:
                enhanced_query = f"{query}\n\nContext:\n{clipboard_text[:2000]}"
            return general_chat(enhanced_query)
        except:
            return f"❌ Error: {str(e)[:200]}"


# ═══════════════════════════════════════════════════════════════════════
# AGENT MODE - Full Autonomous (Wrapper for agent_core)
# ═══════════════════════════════════════════════════════════════════════

def full_agent_mode(
    query: str,
    progress_callback: Optional[Callable[[str], None]] = None,
    max_iterations: int = 10
) -> str:
    """
    Full autonomous agent with all 41 tools.
    
    This is a wrapper for agent_core.execute_autonomous which already implements
    the ReAct loop properly with LangGraph.
    
    Args:
        query: User's command/request
        progress_callback: Function to show progress
        max_iterations: Maximum iterations (default 10 for complex tasks)
        
    Returns:
        Agent's final response after all tool executions
    """
    
    def show_progress(msg: str):
        if progress_callback:
            progress_callback(msg)
    
    try:
        show_progress("🤖 Autonomous agent initializing...")
        
        # Use existing agent_core which already has proper ReAct loop
        from src.brain.agent_core import execute_autonomous
        
        result = execute_autonomous(
            query,
            max_retries=2,
            timeout=90
        )
        
        show_progress("✅ Task complete!")
        return result
        
    except Exception as e:
        import traceback
        print(f"Agent mode error:\n{traceback.format_exc()}")
        return f"❌ Agent error: {str(e)[:200]}"


# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTION - Route to Appropriate Agent
# ═══════════════════════════════════════════════════════════════════════

def route_to_agent(
    mode: str,
    query: str,
    conversation_context: str = "",
    clipboard_text: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> str:
    """
    Route query to appropriate agent based on mode.
    
    Args:
        mode: "chat", "ask", or "agent"
        query: User's query
        conversation_context: Chat history (for chat mode)
        clipboard_text: Clipboard content (for ask mode)
        progress_callback: Progress updates
        
    Returns:
        Agent's response
    """
    
    if mode == "chat":
        return chat_mode_agent(
            query=query,
            conversation_context=conversation_context,
            progress_callback=progress_callback,
            max_iterations=5
        )
    
    elif mode == "ask":
        return ask_mode_agent(
            query=query,
            clipboard_text=clipboard_text,
            progress_callback=progress_callback,
            max_iterations=5
        )
    
    elif mode == "agent":
        return full_agent_mode(
            query=query,
            progress_callback=progress_callback,
            max_iterations=10
        )
    
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'chat', 'ask', or 'agent'")
