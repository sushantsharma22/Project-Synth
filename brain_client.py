"""
Brain Client - Connect to Delta Ollama from Mac
Multi-GPU AI system for code analysis and debugging

Author: Sushant Sharma (ssewuna123@gmail.com)
System: Delta HPC Cluster (delta.cs.uwindsor.ca)
Version: 1.0
"""
import requests
import json
import re
import sys
from pathlib import Path

# Add project paths for agent imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tools.web_tools import RobustSearch, WikiTool, WebReader
from src.brain.skills import Skills
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time

@dataclass
class BrainResponse:
    """Structured response from Brain API."""
    raw_response: str
    suggested_action: Optional[str] = None
    action_type: Optional[str] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    response_time_ms: float = 0.0
    model_used: str = "unknown"

class DeltaBrain:
    """Client for Delta HPC Brain system
    
    Connects to the multi-GPU Ollama Brain running on Delta HPC:
    - fast mode: 3B model (GPU 3, Port 11434) - Simple queries, ~6 sec
    - balanced mode: 7B model (GPU 2, Port 11435) - Error analysis, ~8 sec
    - smart mode: 14B model (GPU 1, Port 11436) - Optimization, ~18 sec
    """
    
    def __init__(self, host="localhost"):
        """Initialize Brain client
        
        Args:
            host: Brain server hostname (default: localhost)
                  Use 'localhost' when SSH tunnel is active
        """
        self.ports = {
            "fast": 11434,    # 3B model - GPU 3
            "balanced": 11435, # 7B model - GPU 2
            "smart": 11436     # 14B model - GPU 1
        }
        self.host = host
        self.models = {
            "fast": "qwen2.5:3b",
            "balanced": "qwen2.5:7b",
            "smart": "qwen2.5:14b"
        }
        
        # Action types the Brain can suggest
        self.ACTIONS = {
            'open_url': 'Open URL in browser',
            'search_file': 'Search for file in project',
            'fix_error': 'Suggest code fix',
            'explain_code': 'Explain code snippet',
            'add_to_clipboard': 'Add text to clipboard',
            'show_notification': 'Show notification',
            'do_nothing': 'No action needed'
        }
    
    def execute_command(self, command: str) -> str:
        """Execute command using autonomous agent with Gemini AI
        
        NEW METHOD: Uses pattern-based routing + Gemini for general questions.
        
        Args:
            command: User query/command
            
        Returns:
            Agent's response
        """
        try:
            from src.brain.agent_gemini import execute_autonomous
            return execute_autonomous(command)
        except Exception as e:
            import traceback
            return f"❌ Agent error: {str(e)}\n{traceback.format_exc()[:200]}"
    
    def safe_ask(self, prompt, mode="balanced", max_tokens=None, log_callback=None):
        """LOCAL-FIRST, CLOUD-FALLBACK: Try Delta Brain, fallback to Gemini
        
        This is the CORE method that implements intelligent fallback strategy.
        
        Args:
            prompt: Your question or request
            mode: "fast", "balanced", or "smart"
            max_tokens: Optional max tokens for response
            log_callback: Optional function(msg) to log decisions
            
        Returns:
            tuple: (response_text, model_used)
                model_used: "Delta-3B", "Delta-7B", "Delta-14B", or "Gemini"
        """
        def log(msg):
            if log_callback:
                log_callback(msg)
        
        # Auto-detect concise requests
        prompt_lower = prompt.lower()
        instruction_keywords = ['concise', 'brief', 'short', 'quick', 'summary', 'tldr']
        is_concise_request = any(keyword in prompt_lower for keyword in instruction_keywords)
        
        if max_tokens is None and is_concise_request:
            max_tokens = 256
        
        # Smart timeout based on model size
        timeouts = {"fast": 15, "balanced": 30, "smart": 60}
        timeout = timeouts.get(mode, 30)
        
        port = self.ports[mode]
        model = self.models[mode]
        model_name = f"Delta-{model.split(':')[1].upper()}"  # "Delta-3B", "Delta-7B", "Delta-14B"
        url = f"http://{self.host}:{port}/api/generate"
        
        # STEP 1: Try LOCAL Delta Brain first
        try:
            log(f"🧠 Trying {model_name} (Local, Private, Free)...")
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if max_tokens:
                payload["options"] = {"num_predict": max_tokens}
            
            response = requests.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                answer = response.json().get("response", "")
                log(f"✅ {model_name} responded successfully")
                return (answer, model_name)
            else:
                log(f"⚠️  {model_name} returned status {response.status_code}")
                raise Exception(f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            log(f"⏱️  {model_name} timed out after {timeout}s")
        except requests.exceptions.ConnectionError:
            log(f"📡 {model_name} not reachable (tunnel down?)")
        except Exception as e:
            log(f"⚠️  {model_name} error: {str(e)[:50]}")
        
        # STEP 2: FALLBACK to Gemini (Cloud)
        try:
            log("☁️  Falling back to Gemini (Cloud)...")
            from src.brain.tools_gemini import generate_with_fallback
            
            gemini_response = generate_with_fallback(prompt)
            # Extract text from response object
            response_text = gemini_response.text if hasattr(gemini_response, 'text') else str(gemini_response)
            log("✅ Gemini responded successfully")
            return (response_text, "Gemini-Cloud")
            
        except Exception as e:
            log(f"❌ Gemini also failed: {str(e)[:50]}")
            return (f"Error: Both Delta and Gemini failed. Please try again.\n{str(e)[:100]}", "Error")
    
    def ask(self, prompt, mode="balanced", max_tokens=None):
        """Legacy method - now uses safe_ask internally
        
        Args:
            prompt: Your question or request
            mode: "fast", "balanced", or "smart"
            max_tokens: Optional max tokens for response
            
        Returns:
            AI response as string
        """
        response, model_used = self.safe_ask(prompt, mode, max_tokens)
        return response
    
    def ask_with_context(self, question, context_chunks, mode="balanced", max_tokens=None):
        """Ask a question with retrieved context chunks (RAG pattern)
        
        Args:
            question: The user's question
            context_chunks: List of relevant context strings from RAG
            mode: "fast", "balanced", or "smart"
            max_tokens: Optional max tokens for response
            
        Returns:
            AI response incorporating the context
        """
        # Build enhanced prompt with context
        context_text = "\n\n".join([
            f"Context {i+1}:\n{chunk}" 
            for i, chunk in enumerate(context_chunks)
        ])
        
        enhanced_prompt = f"""Based on the following context, answer the question.

CONTEXT:
{context_text}

QUESTION: {question}

Answer the question using the context provided above. If the context doesn't contain enough information, say so and provide what you know from general knowledge."""
        
        # Use regular ask() method with the enhanced prompt
        return self.ask(enhanced_prompt, mode=mode, max_tokens=max_tokens)
    
    def analyze_error(self, error_msg, code="", log_callback=None):
        """Analyze code error and provide solution (with fallback)
        
        Args:
            error_msg: Error message or exception
            code: Code snippet that caused the error (optional)
            log_callback: Optional logging function
            
        Returns:
            Analysis with cause, fix, and corrected code
        """
        prompt = f"""Analyze this error and provide solution:

Error: {error_msg}
{f'Code: {code}' if code else ''}

Provide:
1. What caused it
2. How to fix it
3. Fixed code"""
        response, model_used = self.safe_ask(prompt, mode="balanced", log_callback=log_callback)
        return response
    
    def explain_code(self, code, mode="balanced", log_callback=None):
        """Explain what code does (with fallback)
        
        Args:
            code: Code snippet to explain
            mode: Model to use
            log_callback: Optional logging function
            
        Returns:
            Explanation of the code
        """
        prompt = f"""Explain what this code does:

{code}

Provide a clear, concise explanation."""
        response, model_used = self.safe_ask(prompt, mode=mode, log_callback=log_callback)
        return response
    
    def optimize_code(self, code, mode="smart", log_callback=None):
        """Optimize code for better performance (with fallback)
        
        Args:
            code: Code to optimize
            mode: Model to use (default: smart)
            
        Returns:
            Optimized version with explanation
        """
        prompt = f"""Optimize this code:

{code}

Provide:
1. Performance issues identified
2. Optimized version
3. Explanation of improvements"""
        response, model_used = self.safe_ask(prompt, mode=mode, log_callback=log_callback)
        return response
    
    def review_code(self, code, mode="balanced", log_callback=None):
        """Review code for bugs and best practices (with fallback)
        
        Args:
            code: Code to review
            mode: Model to use
            log_callback: Optional logging function
            
        Returns:
            Code review with suggestions
        """
        prompt = f"""Review this code for bugs, security issues, and best practices:

{code}

Provide:
1. Issues found
2. Suggestions for improvement
3. Fixed version if needed"""
        response, model_used = self.safe_ask(prompt, mode=mode, log_callback=log_callback)
        return response
        return self.ask(prompt, mode=mode)
    
    def check_connection(self):
        """Check if Brain is accessible
        
        Returns:
            dict with status for each model
        """
        results = {}
        for mode, port in self.ports.items():
            try:
                url = f"http://{self.host}:{port}/api/version"
                response = requests.get(url, timeout=5)
                results[mode] = "✅ Connected" if response.ok else "❌ Error"
            except:
                results[mode] = "❌ Not reachable"
        return results
    
    def execute_agentic_task(self, user_query, selected_text=None):
        """
        Execute an agentic task with routing, tool execution, and synthesis.
        This is the CORE AGENT LOGIC.
        
        Args:
            user_query: User's question or request
            selected_text: Optional text user has highlighted/selected
            
        Returns:
            Final synthesized answer
        """
        print(f"\n{'='*60}")
        print(f"🤖 AGENT EXECUTION: {user_query}")
        print(f"{'='*60}\n")
        
        # STEP 1: ROUTE - Decide which tool to use
        print("🎯 STEP 1: Routing to appropriate tool...")
        router_prompt = Skills.get_router_prompt(user_query, selected_text)
        
        # Use fast model for routing decision
        routing_response = self.ask(router_prompt, mode="fast", max_tokens=50)
        print(f"Raw routing response: {routing_response}")
        
        # Extract tool choice from response
        tool_match = re.search(r'\[(WEB_SEARCH|WIKIPEDIA|SUMMARIZE|PARAPHRASE|GENERAL_QA)\]', routing_response)
        
        if tool_match:
            tool_choice = tool_match.group(1)
        else:
            # Fallback - look for keywords in response
            if 'WEB_SEARCH' in routing_response.upper():
                tool_choice = 'WEB_SEARCH'
            elif 'WIKIPEDIA' in routing_response.upper():
                tool_choice = 'WIKIPEDIA'
            elif 'SUMMARIZE' in routing_response.upper():
                tool_choice = 'SUMMARIZE'
            elif 'PARAPHRASE' in routing_response.upper():
                tool_choice = 'PARAPHRASE'
            else:
                tool_choice = 'GENERAL_QA'
        
        print(f"✅ Tool selected: [{tool_choice}]\n")
        
        # STEP 2: EXECUTE - Run the selected tool
        print(f"⚙️ STEP 2: Executing [{tool_choice}]...")
        context = ""
        
        if tool_choice == 'WEB_SEARCH':
            # Web search workflow
            print("🔍 Searching web...")
            searcher = RobustSearch()
            reader = WebReader()
            
            # Get top URLs from search
            urls = searcher.get_top_urls(user_query, num_urls=2)
            
            if urls:
                print(f"📄 Found {len(urls)} URLs, reading content...")
                # Read content from URLs
                context = reader.read_multiple_urls(urls, max_chars_per_url=4000)
            else:
                # Fallback to search results if can't get URLs
                context = searcher.search(user_query, max_results=5)
        
        elif tool_choice == 'WIKIPEDIA':
            # Wikipedia lookup
            wiki = WikiTool()
            context = wiki.get_summary(user_query, sentences=8)
        
        elif tool_choice == 'SUMMARIZE':
            # Summarize selected text
            if selected_text:
                summary_prompt = Skills.summarize(selected_text)
                return self.ask(summary_prompt, mode="balanced", max_tokens=400)
            else:
                return "❌ Cannot summarize - no text selected. Please highlight text first."
        
        elif tool_choice == 'PARAPHRASE':
            # Paraphrase selected text
            if selected_text:
                paraphrase_prompt = Skills.paraphrase(selected_text)
                return self.ask(paraphrase_prompt, mode="balanced", max_tokens=600)
            else:
                return "❌ Cannot paraphrase - no text selected. Please highlight text first."
        
        elif tool_choice == 'GENERAL_QA':
            # Simple question - no external data needed
            return self.ask(user_query, mode="balanced")
        
        print(f"✅ Context gathered ({len(context)} chars)\n")
        
        # STEP 3: SYNTHESIZE - Generate final answer using smart model
        print("🧠 STEP 3: Synthesizing final answer with smart model...")
        
        synthesis_prompt = f"""You are a helpful AI assistant. Answer the user's question using the provided context.

USER QUESTION:
{user_query}

CONTEXT:
{context[:12000]}

INSTRUCTIONS:
- Answer the question directly and clearly
- Use information from the context provided
- If the context doesn't contain the answer, say so
- Keep your answer focused and relevant
- Answer in ENGLISH ONLY

YOUR ANSWER:"""
        
        final_answer = self.ask(synthesis_prompt, mode="smart", max_tokens=800)
        
        print(f"\n{'='*60}")
        print("✅ AGENT EXECUTION COMPLETE")
        print(f"{'='*60}\n")
        
        return final_answer

    def classify_query_ollama(self, query: str) -> str:
        """
        Classify query using Ollama 3B fast model (~1 second)
        
        Args:
            query: User query
            
        Returns:
            One of: "WEB_SEARCH", "OLLAMA_ONLY", "MULTI_QUERY"
        """
        # FIRST: Check for multi-query patterns (rule-based for accuracy)
        query_lower = query.lower()
        
        # Multi-query indicators: "X and Y" where X and Y are different topics
        multi_indicators = [
            ' and ' in query_lower and '?' not in query_lower,  # "weather windsor and immigration news"
            query.count('?') >= 2,  # Multiple questions
        ]
        
        # Additional pattern checks
        has_weather_and_other = 'weather' in query_lower and any(word in query_lower for word in ['news', 'immigration', 'visa'])
        has_what_and_how = 'what' in query_lower and 'how' in query_lower
        has_tell_and_is = 'tell' in query_lower and 'and is' in query_lower
        
        if has_weather_and_other or has_what_and_how or has_tell_and_is:
            multi_indicators.append(True)
        
        # If clear multi-query pattern, return immediately
        if any(multi_indicators):
            # Double-check: must have at least 2 distinct topics
            topics_found = 0
            topic_keywords = [
                ['weather', 'temperature', 'forecast'],
                ['news', 'latest', 'current events'],
                ['immigration', 'visa', 'pr', 'permanent residence'],
                ['what is', 'explain', 'define'],
                ['how to', 'install', 'setup']
            ]
            
            for topic_group in topic_keywords:
                if any(keyword in query_lower for keyword in topic_group):
                    topics_found += 1
            
            if topics_found >= 2:
                return "MULTI_QUERY"
        
        # SECOND: Use LLM for remaining cases
        prompt = f"""Classify this query into ONE category. Reply with ONLY the category name in brackets.

Categories:
[WEB_SEARCH] - Needs current/real-time data (news, weather, "latest", "today", current events)
[OLLAMA_ONLY] - General knowledge questions that don't need current data
[MULTI_QUERY] - Multiple different questions in one input

Query: {query}

Classification:"""
        
        response = self.ask(prompt, mode="fast", max_tokens=10)
        
        # Extract category
        if "MULTI_QUERY" in response.upper():
            return "MULTI_QUERY"
        elif "WEB_SEARCH" in response.upper():
            return "WEB_SEARCH"
        else:
            return "OLLAMA_ONLY"
    
    def humanize_response(self, text: str, log_callback=None) -> tuple:
        """
        THE STYLE ENGINE: Transform any raw text into friendly, conversational response
        
        This is a universal humanizer that works on ANY raw data:
        - Tool outputs: "Temp: 5C" → "It's 5°C, so grab a coat!"
        - Search results: "GDP: $21T" → "The GDP is $21 trillion, quite impressive!"
        - Definitions: "noun: happiness" → "It means happiness - that warm fuzzy feeling!"
        
        Args:
            text: Raw text to humanize
            log_callback: Optional function to log decisions
            
        Returns:
            tuple: (humanized_text, model_used)
        """
        def log(msg):
            if log_callback:
                log_callback(msg)
        
        # Skip if already friendly
        if text and (text.startswith('🤖') or text.startswith('✅') or 
                     'friendly' in text.lower()[:100] or len(text) > 1500):
            log("ℹ️  Text already conversational, skipping humanization")
            return (text, "Skipped")
        
        # Smart model selection based on length (3-tier routing!)
        if len(text) < 300:
            mode = "fast"  # 3B for short text
            log("📊 Short text (<300 chars) → Using Fast model (3B)")
        elif len(text) < 1000:
            mode = "balanced"  # 7B for medium text
            log("📊 Medium text (300-1000 chars) → Using Balanced model (7B)")
        else:
            mode = "smart"  # 14B for long/complex text
            log("📊 Long text (>1000 chars) → Using Smart model (14B)")
        
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Universal friendly prompt (NO HARDCODING!)
        prompt = f"""You are a friendly, helpful AI assistant. Transform the raw data below into a warm, conversational response.

CURRENT DATE: {current_date}

RAW DATA:
{text[:2000]}

INSTRUCTIONS:
- Be friendly, warm, and conversational (like talking to a friend)
- Interpret the data naturally - don't just repeat it robotically
- If it's advice-worthy (weather, health, decisions), give helpful recommendations
- If it's factual (definitions, prices, data), explain it naturally
- Keep it concise but complete (50-200 words)
- Use a natural, human tone - NO robotic data dumps!
- Answer in ENGLISH ONLY

YOUR FRIENDLY RESPONSE:"""
        
        try:
            response, model_used = self.safe_ask(prompt, mode=mode, log_callback=log)
            log(f"✅ Humanized with {model_used}")
            return (response.strip(), model_used)
        except Exception as e:
            log(f"⚠️  Humanization failed: {e}")
            return (text, "Error-Original")
    
    def humanize_tool_output(self, query: str, tool_output: str, tool_name: str | None = None, log_callback=None) -> str:
        """
        Humanize raw tool output into friendly, conversational response
        
        This is the SYNTHESIS PIPELINE that transforms robotic data into natural language.
        NOW USES humanize_response() for intelligent model selection and fallback.
        
        Args:
            query: Original user query
            tool_output: Raw output from tool (e.g. "Temp: 5C" or "AAPL: $150.23")
            tool_name: Optional name of the tool that generated output
            log_callback: Optional logging function
            
        Returns:
            Friendly, conversational answer
        """
        def log(msg):
            if log_callback:
                log_callback(msg)
        
        # Skip humanization if output is already conversational
        if tool_output and (tool_output.startswith('🤖') or tool_output.startswith('✅') or 
                            'friendly' in tool_output.lower()[:100] or len(tool_output) > 500):
            log("ℹ️  Tool output already friendly")
            return tool_output
        
        log(f"🎨 Humanizing tool output for query: '{query[:50]}...'")
        
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Context-aware prompt that references the user's question
        context_prompt = f"""You are a friendly and helpful AI assistant. Answer the user's question using the raw data below.

CURRENT DATE: {current_date}

USER QUESTION: {query}

RAW DATA:
{tool_output[:2000]}

INSTRUCTIONS:
- Answer the user's question directly and naturally
- Interpret the data - don't just repeat it
- If the user asks "should I...", give friendly advice based on the data
- Be conversational and warm, like talking to a friend
- Keep it focused and concise (50-200 words)
- Answer in ENGLISH ONLY

YOUR FRIENDLY ANSWER:"""
        
        try:
            # Use safe_ask for automatic fallback
            response, model_used = self.safe_ask(
                context_prompt, 
                mode="fast",  # Use fast for humanization
                max_tokens=300,
                log_callback=log
            )
            log(f"✅ Humanized with {model_used}")
            return response.strip()
        except Exception as e:
            log(f"⚠️  Humanization failed: {e}")
            return tool_output
    
    def split_multi_query(self, query: str) -> list:
        """
        Split multi-query into separate sub-questions using Ollama 3B
        
        Args:
            query: Multi-part query
            
        Returns:
            List of individual sub-queries
        """
        prompt = f"""Split this query into separate individual questions. Output ONLY the questions, one per line.

Query: {query}

Individual questions:"""
        
        response = self.ask(prompt, mode="fast", max_tokens=150)
        
        # Parse response - split by newlines and filter
        lines = [line.strip() for line in response.split('\n')]
        questions = [line for line in lines if line and len(line) > 10 and not line.startswith(('-', '*', '•'))]
        
        # Remove numbering if present
        import re
        cleaned = []
        for q in questions:
            # Remove leading numbers/bullets
            q = re.sub(r'^[\d\.\)\-\*\•\s]+', '', q).strip()
            if q:
                cleaned.append(q)
        
        return cleaned if cleaned else [query]
    
    def estimate_complexity(self, query: str) -> str:
        """
        Intelligently estimate query complexity based on content and intent
        
        Args:
            query: User query
            
        Returns:
            "SIMPLE", "MEDIUM", or "COMPLEX"
        """
        # RULE-BASED CLASSIFICATION (Fast, No AI needed!)
        query_lower = query.lower()
        word_count = len(query.split())
        
        # SIMPLE indicators (3B model) - Short, basic facts
        # These OVERRIDE technical terms!
        simple_patterns = [
            'what is', 'who is', 'define', 'meaning of',
            'capital of', 'weather in', 'time in',
            'how to spell', 'translate'
        ]
        
        # Check for SIMPLE patterns FIRST (highest priority for basic questions)
        if any(pattern in query_lower for pattern in simple_patterns):
            if word_count <= 8:  # Short, simple query
                return "SIMPLE"
        
        # COMPLEX indicators (14B model) - Deep analysis, comparisons
        complex_patterns = [
            'compare', 'vs', 'versus', 'difference between',
            'analyze', 'evaluate', 'critique',
            'why does', 'explain why', 'how does',
            'pros and cons', 'advantages and disadvantages',
            'technical report', 'research', 'detailed',
            'in-depth', 'comprehensive'
        ]
        
        # Check for COMPLEX patterns
        if any(pattern in query_lower for pattern in complex_patterns):
            return "COMPLEX"
        
        # Check for technical/domain-specific terms (COMPLEX)
        # BUT only if not a simple "what is" question
        technical_indicators = [
            'fips', 'algorithm', 'protocol', 'standard',
            'architecture', 'implementation', 'benchmark',
            'cryptography', 'encryption'
        ]
        if any(term in query_lower for term in technical_indicators):
            return "COMPLEX"
        
        # MEDIUM indicators (7B model) - Multi-part, recipes, recent events
        medium_patterns = [
            'how can i', 'how do i', 'how to',
            'recipe', 'cook', 'make',
            'latest', 'recent', 'new', 'update',
            'features of', 'what are', 'list',
            'who won', 'who win', 'election', 'news'
        ]
        
        # Check for MEDIUM patterns
        if any(pattern in query_lower for pattern in medium_patterns):
            return "MEDIUM"
        
        # Fallback based on length
        if word_count >= 10:
            return "MEDIUM"  # Longer queries likely need more reasoning
        
        # Final fallback: SIMPLE for very short queries
        return "SIMPLE"
    
    def synthesize_web_results(self, query: str, search_results: dict, log_callback=None) -> tuple:
        """
        Synthesize answer from web search results using appropriate Ollama model
        NOW WITH LOCAL-FIRST, CLOUD-FALLBACK architecture!
        
        Args:
            query: Original user query
            search_results: Dict from WebSearchRAG.search() containing 'results' and 'context'
            log_callback: Optional logging function
            
        Returns:
            tuple: (synthesized_answer_with_sources, model_used)
        """
        def log(msg):
            if log_callback:
                log_callback(msg)
        
        # STEP 1: Intelligent model selection (NO HARDCODING!)
        log("🤔 Analyzing query complexity...")
        complexity = self.estimate_complexity(query)
        log(f"📊 Complexity: {complexity}")
        
        # Smart 3-tier model selection
        if complexity == "SIMPLE":
            mode = "fast"  # 3B for simple facts
            log("⚡ Simple query → Using Fast model (3B)")
        elif complexity == "MEDIUM":
            mode = "balanced"  # 7B for moderate complexity
            log("📚 Medium query → Using Balanced model (7B)")
        else:  # COMPLEX
            mode = "smart"  # 14B for deep analysis
            log("🧠 Complex query → Using Smart model (14B)")
        
        # Get context text for prompt
        context_text = search_results.get('context', '')
        
        # Build universal friendly synthesis prompt (NO HARDCODING!)
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""You are a friendly and helpful AI assistant. Answer the user's question naturally using the data below.

CURRENT DATE: {current_date}

USER QUESTION: {query}

DATA FROM WEB SOURCES:
{context_text[:8000]}

INSTRUCTIONS:
- Be warm, friendly, and conversational
- Interpret the data - don't just list facts robotically
- If the user asks for advice or "should I...", give helpful recommendations
- Answer completely and clearly in natural language
- Cite key facts when relevant
- Keep your answer focused (200-400 words)
- If data is insufficient, say so honestly and provide what you know
- Answer in ENGLISH ONLY

YOUR FRIENDLY ANSWER:"""
        
        # Use safe_ask for automatic fallback!
        answer, model_used = self.safe_ask(prompt, mode=mode, max_tokens=600, log_callback=log)
        
        # Append source list
        sources_text = "\n\n📚 Sources:\n"
        for i, result in enumerate(search_results.get('results', [])[:5], 1):
            title = result.title[:80] + "..." if len(result.title) > 80 else result.title
            sources_text += f"[{i}] {title} - {result.source}\n"
        
        return (answer + sources_text, model_used)

    def analyze_context(self, context, mode: str = 'balanced') -> BrainResponse:
        """
        Analyze a context package and suggest actions.
        
        Args:
            context: ContextPackage from trigger system
            mode: 'fast', 'balanced', or 'smart'
            
        Returns:
            BrainResponse with suggested action
        """
        start_time = time.time()
        
        # Build the prompt
        prompt = self._build_context_prompt(context)
        
        try:
            # Use safe_ask to get response
            response_text, model_used = self.safe_ask(prompt, mode=mode)
            
            # Parse response into structured format
            brain_response = self._parse_context_response(
                response_text=response_text,
                model=model_used,
                start_time=start_time
            )
            
            return brain_response
            
        except Exception as e:
            return BrainResponse(
                raw_response=f"Error: {str(e)}",
                action_type='do_nothing',
                confidence=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                model_used="error"
            )

    def _build_context_prompt(self, context) -> str:
        """Build a prompt from context package."""
        content_type = context.clipboard_metadata.get('type', 'unknown')
        content = context.clipboard_content
        
        # System prompt - defines the agent's role
        system_prompt = """You are a proactive AI assistant that helps developers by analyzing their clipboard and screen context.

When you see clipboard content, analyze it and suggest helpful actions.

Available actions:
- open_url: If clipboard contains a URL
- search_file: If clipboard contains a filename or path
- fix_error: If clipboard contains an error message
- explain_code: If clipboard contains code
- add_to_clipboard: If you want to suggest text to copy
- show_notification: If you want to show a helpful tip
- do_nothing: If no action is needed

Respond in JSON format:
{
  "action_type": "action_name",
  "suggested_action": "specific action to take",
  "confidence": 0.0-1.0,
  "reasoning": "why you suggest this"
}"""

        # User prompt - the actual context
        user_prompt = f"""Clipboard Content Type: {content_type}
Clipboard Text:
{content}

Has Screenshot: {bool(context.screenshot_base64)}

What action should I take to help the user?"""

        return f"{system_prompt}\n\n{user_prompt}"

    def _parse_context_response(self, response_text: str, model: str, start_time: float) -> BrainResponse:
        """Parse Brain response into structured format."""
        response_time_ms = (time.time() - start_time) * 1000
        
        try:
            # Look for JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                return BrainResponse(
                    raw_response=response_text,
                    suggested_action=data.get('suggested_action'),
                    action_type=data.get('action_type'),
                    confidence=data.get('confidence', 0.5),
                    reasoning=data.get('reasoning'),
                    response_time_ms=response_time_ms,
                    model_used=model
                )
            else:
                return BrainResponse(
                    raw_response=response_text,
                    action_type='do_nothing',
                    confidence=0.3,
                    response_time_ms=response_time_ms,
                    model_used=model
                )
                
        except json.JSONDecodeError:
            return BrainResponse(
                raw_response=response_text,
                action_type='do_nothing',
                confidence=0.3,
                response_time_ms=response_time_ms,
                model_used=model
            )
if __name__ == "__main__":
    print("🧠 Delta Brain Client")
    print("=" * 50)
    
    brain = DeltaBrain()
    
    # Check connection
    print("\n📡 Checking Brain connection...")
    status = brain.check_connection()
    for mode, result in status.items():
        print(f"  {mode:10} → {result}")
    
    # Quick test
    print("\n🧪 Quick test (fast model)...")
    response = brain.ask("Say 'Brain connected!' if you can hear me", mode="fast")
    print(f"Response: {response[:100]}...")
    
    print("\n✅ Brain client ready!")
    print("\nNext: Set up SSH tunnel to Delta:")
    print("  ssh -L 11434:localhost:11434 -L 11435:localhost:11435 -L 11436:localhost:11436 sharmas1@delta.cs.uwindsor.ca")

