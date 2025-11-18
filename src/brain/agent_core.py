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
            # Invoke agent with user command
            result = agent.invoke({
                "messages": [("user", command)]
            })
            
            elapsed_time = time.time() - start_time
            
            # Check timeout
            if elapsed_time > timeout:
                return f"⏱️ Command timed out after {timeout}s"
            
            # Extract final response
            messages = result.get("messages", [])
            if not messages:
                return "No response from agent"
            
            # Get last message (final answer)
            final_message = messages[-1]
            
            # Return content based on message type
            if hasattr(final_message, 'content'):
                return final_message.content
            else:
                return str(final_message)
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying... Error: {str(e)}")
                continue
            else:
                return f"❌ Agent failed after {max_retries} attempts: {str(e)}"
    
    return "Agent execution failed"
