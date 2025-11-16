"""
Brain Client - Connect to Delta Ollama from Mac
Multi-GPU AI system for code analysis and debugging

Author: Sushant Sharma (ssewuna123@gmail.com)
System: Delta HPC Cluster (delta.cs.uwindsor.ca)
Version: 1.0
"""
import requests
import json

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
    
    def ask(self, prompt, mode="balanced", max_tokens=None):
        """Send question to Brain
        
        Args:
            prompt: Your question or request
            mode: "fast", "balanced", or "smart"
            max_tokens: Optional max tokens for response (None = unlimited)
            
        Returns:
            AI response as string
        """
        # Auto-detect if response should be concise
        prompt_lower = prompt.lower()
        instruction_keywords = ['concise', 'brief', 'short', 'quick', 'summary', 'tldr']
        is_concise_request = any(keyword in prompt_lower for keyword in instruction_keywords)
        
        # Set max_tokens based on instruction detection if not explicitly provided
        if max_tokens is None and is_concise_request:
            max_tokens = 256  # Limit to ~256 tokens for concise responses
        
        port = self.ports[mode]
        model = self.models[mode]
        url = f"http://{self.host}:{port}/api/generate"
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            # Add max_tokens if specified
            if max_tokens:
                payload["options"] = {"num_predict": max_tokens}
            
            response = requests.post(url, json=payload, timeout=90)
            return response.json()["response"]
        except requests.exceptions.Timeout:
            return f"Timeout Error: Brain took longer than 90 seconds to respond.\nTry using 'fast' mode or check if Brain is overloaded."
        except requests.exceptions.ConnectionError:
            return f"Connection Error: Cannot connect to Brain on port {port}.\nMake sure SSH tunnel is active with: ./brain_monitor_key.sh"
        except requests.exceptions.RequestException as e:
            return f"Connection Error: {str(e)}\nMake sure SSH tunnel is active!"
        except KeyError:
            return f"Error: Invalid response from Brain. The model may not be loaded."
        except Exception as e:
            return f"Error: {str(e)}"
    
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
    
    def analyze_error(self, error_msg, code=""):
        """Analyze code error and provide solution
        
        Args:
            error_msg: Error message or exception
            code: Code snippet that caused the error (optional)
            
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
        return self.ask(prompt, mode="balanced")
    
    def explain_code(self, code, mode="balanced"):
        """Explain what code does
        
        Args:
            code: Code snippet to explain
            mode: Model to use
            
        Returns:
            Explanation of the code
        """
        prompt = f"""Explain what this code does:

{code}

Provide a clear, concise explanation."""
        return self.ask(prompt, mode=mode)
    
    def optimize_code(self, code, mode="smart"):
        """Optimize code for better performance
        
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
        return self.ask(prompt, mode=mode)
    
    def review_code(self, code, mode="balanced"):
        """Review code for bugs and best practices
        
        Args:
            code: Code to review
            mode: Model to use
            
        Returns:
            Code review with suggestions
        """
        prompt = f"""Review this code for bugs, security issues, and best practices:

{code}

Provide:
1. Issues found
2. Suggestions for improvement
3. Fixed version if needed"""
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

