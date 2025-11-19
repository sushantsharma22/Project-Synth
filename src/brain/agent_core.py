"""
Agent Core - LangGraph Autonomous Agent with Gemini + Tavily
Replaces manual routing with autonomous tool selection

Author: Sushant Sharma
Date: November 17, 2025
"""

import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_LANGCHAIN_GOOGLE_GENAI = True
except Exception:
    ChatGoogleGenerativeAI = None
    HAS_LANGCHAIN_GOOGLE_GENAI = False
    print("⚠️ langchain_google_genai not installed; falling back to simplified Tavily-only agent")
from src.brain.core_tools import ALL_TOOLS
import time

# Load environment variables
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please add it.")

# System prompt to force tool usage
AGENT_SYSTEM_PROMPT = """You are a powerful AI assistant with access to 41 macOS automation tools.

CRITICAL RULES:
1. When user asks you to DO something (send, open, create, delete, search, etc.), you MUST call the appropriate tool
2. NEVER just SAY you did something - you must ACTUALLY execute the tool
3. After calling a tool, report the tool's actual result to the user
4. If you're unsure which tool to use, call multiple tools to explore
5. Available tool categories:
   - Web: web_search_tavily
   - WhatsApp: whatsapp_message, whatsapp_call
   - Browser: chrome_open_url, safari_open_url
   - Apps: spotify_play, spotify_control, quit_app, focus_app
   - Files: file_search, notes_create, open_file_or_folder
   - System: get_active_app

EXAMPLES OF CORRECT BEHAVIOR:
❌ WRONG: "OK, I've sent a WhatsApp message to John"
✅ CORRECT: [Call whatsapp_message tool] → Report actual result

❌ WRONG: "I've opened Chrome to google.com"
✅ CORRECT: [Call chrome_open_url tool] → Report if it succeeded

You have the tools - USE THEM! Don't hallucinate actions."""

# Initialize Gemini LLM - using models/ prefix for v1beta API
if HAS_LANGCHAIN_GOOGLE_GENAI and ChatGoogleGenerativeAI:
    try:
        from src.brain.tools_gemini import get_preferred_model_names
        _, preferred_langchain_model = get_preferred_model_names()
        llm = ChatGoogleGenerativeAI(
            model=preferred_langchain_model,
            google_api_key=GEMINI_API_KEY,
            temperature=0.7
        )
        
        # Create agent (system prompt will be added in execute_autonomous)
        agent = create_react_agent(llm, ALL_TOOLS)
    except Exception as e:
        print(f"⚠️ Failed to initialize LLM agent: {e}; falling back to simplified Tavily-only agent")
        agent = None
else:
    agent = None


def execute_autonomous(command: str, max_retries: int = 3, timeout: int = 90) -> str:
    """
    Execute command autonomously - agent decides which tools to use
    
    Args:
        command: User query/command
        max_retries: Number of retry attempts on failure
        timeout: Max execution time in seconds
        
    Returns:
        Agent's final response
    """
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            # If agent is unavailable, fall back to simplified agent
            if not agent:
                from src.brain.agent_simple import execute_autonomous as simple_execute
                return simple_execute(command)
            
            print(f"🤖 Full Agent: Processing with all 41 tools...")
            
            # Invoke agent with system prompt + user command
            result = agent.invoke({
                "messages": [
                    ("system", AGENT_SYSTEM_PROMPT),
                    ("user", command)
                ]
            })
            
            elapsed_time = time.time() - start_time
            
            # Check timeout
            if elapsed_time > timeout:
                return f"⏱️ Command timed out after {timeout}s"
            
            # Extract final response AND check if tools were actually called
            messages = result.get("messages", [])
            if not messages:
                return "No response from agent"
            
            # Check if ANY tools were called
            tool_calls_found = False
            tools_used = []
            
            for msg in messages:
                # Check for tool calls in agent messages
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls_found = True
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        tools_used.append(tool_name)
                
                # Check for tool responses
                if hasattr(msg, 'name'):
                    tool_calls_found = True
            
            # Get last message (final answer)
            final_message = messages[-1]
            
            # Extract content
            if hasattr(final_message, 'content'):
                final_content = final_message.content
            else:
                final_content = str(final_message)
            
            # Log what happened
            if tool_calls_found:
                unique_tools = list(set(tools_used))
                print(f"✅ Full Agent: Task complete ({len(final_content)} chars) - Tools used: {', '.join(unique_tools)}")
            else:
                print(f"⚠️  Full Agent: No tools called - Agent may have hallucinated")
                # If no tools were called but command seems to require action, warn user
                action_keywords = ['send', 'open', 'create', 'delete', 'write', 'call', 'message', 'email']
                if any(keyword in command.lower() for keyword in action_keywords):
                    final_content = f"⚠️ Note: I understood your request but may not have executed the action.\n\n{final_content}\n\n(Agent didn't call any tools - please verify the action was completed)"
            
            return final_content
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying... Error: {str(e)}")
                continue
            else:
                return f"❌ Agent failed after {max_retries} attempts: {str(e)}"
    
    return "Agent execution failed"
