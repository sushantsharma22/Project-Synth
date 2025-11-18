#!/usr/bin/env python3
"""
Brain API Client for Project Synth
Enhanced wrapper for Delta Brain (Ollama) with context package support.

Phase 2: Brain - AI Reasoning
Handles multimodal prompts (text + image) and action parsing.
"""

import json
import time
import requests
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path

# Import context package
sys.path.insert(0, str(Path(__file__).parent.parent))
from senses.trigger_system import ContextPackage


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


class BrainAPIClient:
    """
    Enhanced Brain API client for Project Synth.
    
    Accepts ContextPackage objects and returns structured responses
    with suggested actions.
    """
    
    # Model endpoints
    MODELS = {
        'fast': {'port': 11434, 'name': 'qwen2.5:3b', 'desc': 'Fast responses'},
        'balanced': {'port': 11435, 'name': 'qwen2.5:7b', 'desc': 'Balanced'},
        'smart': {'port': 11436, 'name': 'qwen2.5:14b', 'desc': 'Deep analysis'}
    }
    
    # Action types the Brain can suggest
    ACTIONS = {
        'open_url': 'Open URL in browser',
        'search_file': 'Search for file in project',
        'fix_error': 'Suggest code fix',
        'explain_code': 'Explain code snippet',
        'add_to_clipboard': 'Add text to clipboard',
        'show_notification': 'Show notification',
        'do_nothing': 'No action needed'
    }
    
    def __init__(self, host: str = "localhost", timeout: int = 30):
        """
        Initialize Brain API client.
        
        Args:
            host: Ollama server host (default: localhost via SSH tunnel)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.timeout = timeout
        self.stats: Dict[str, float] = {
            'total_requests': 0.0,
            'successful_requests': 0.0,
            'failed_requests': 0.0,
            'avg_response_time_ms': 0.0,
            'total_response_time_ms': 0.0
        }
    
    def analyze_context(self, 
                       context: ContextPackage,
                       mode: str = 'balanced') -> BrainResponse:
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
        prompt = self._build_prompt(context)
        
        # Call appropriate model
        model_config = self.MODELS.get(mode, self.MODELS['balanced'])
        
        try:
            response_text = self._call_ollama(
                prompt=prompt,
                port=model_config['port'],
                model=model_config['name'],
                include_image=bool(context.screenshot_base64)
            )
            
            # Parse response into structured format
            brain_response = self._parse_response(
                response_text=response_text,
                model=model_config['name'],
                start_time=start_time
            )
            
            # Update stats
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            self.stats['total_response_time_ms'] += brain_response.response_time_ms
            self.stats['avg_response_time_ms'] = (
                self.stats['total_response_time_ms'] / self.stats['total_requests']
            )
            
            return brain_response
            
        except Exception as e:
            self.stats['total_requests'] += 1
            self.stats['failed_requests'] += 1
            
            return BrainResponse(
                raw_response=f"Error: {str(e)}",
                action_type='do_nothing',
                confidence=0.0,
                response_time_ms=(time.time() - start_time) * 1000,
                model_used=model_config['name']
            )
    
    def _build_prompt(self, context: ContextPackage) -> str:
        """
        Build a prompt from context package.
        
        Args:
            context: ContextPackage to analyze
            
        Returns:
            Formatted prompt string
        """
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

        # Combine prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        return full_prompt
    
    def _call_ollama(self, 
                    prompt: str,
                    port: int,
                    model: str,
                    include_image: bool = False) -> str:
        """
        Call Ollama API.
        
        Args:
            prompt: Text prompt
            port: Model port
            model: Model name
            include_image: Whether to include image (for multimodal)
            
        Returns:
            Response text
        """
        url = f"http://{self.host}:{port}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        # TODO: Add image support for multimodal
        # if include_image:
        #     payload['images'] = [image_base64]
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.timeout}s - Brain may be overloaded")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Connection failed - Is Brain running? Start SSH tunnel: ./scripts/connect_brain_key.sh (port {port})")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request error: {str(e)}")
    
    def _parse_response(self,
                       response_text: str,
                       model: str,
                       start_time: float) -> BrainResponse:
        """
        Parse Brain response into structured format.
        
        Args:
            response_text: Raw response from Brain
            model: Model name used
            start_time: Request start time
            
        Returns:
            Structured BrainResponse
        """
        response_time_ms = (time.time() - start_time) * 1000
        
        # Try to extract JSON from response
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
                # No JSON found - return raw response
                return BrainResponse(
                    raw_response=response_text,
                    action_type='do_nothing',
                    confidence=0.3,
                    response_time_ms=response_time_ms,
                    model_used=model
                )
                
        except json.JSONDecodeError:
            # JSON parsing failed - return raw response
            return BrainResponse(
                raw_response=response_text,
                action_type='do_nothing',
                confidence=0.3,
                response_time_ms=response_time_ms,
                model_used=model
            )
    
    def check_connection(self) -> bool:
        """
        Check if Brain is accessible.
        
        Returns:
            True if at least one model is accessible
        """
        for mode, config in self.MODELS.items():
            try:
                url = f"http://{self.host}:{config['port']}/api/version"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                continue
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return self.stats.copy()


# Example usage
if __name__ == "__main__":
    print("🧠 Testing Brain API Client")
    print("=" * 60)
    
    # Check connection
    client = BrainAPIClient()
    
    print("\n🔌 Checking Brain connection...")
    if client.check_connection():
        print("✅ Brain is online!")
    else:
        print("❌ Brain is offline. Start with: ./scripts/connect_brain_key.sh")
        sys.exit(1)
    
    # Create a test context package
    from senses.trigger_system import ContextPackage
    
    test_context = ContextPackage(
        clipboard_content="KeyError: 'user_id' not found in dictionary",
        clipboard_metadata={
            'timestamp': time.time(),
            'type': 'error'
        },
        screenshot_base64=None  # No screenshot for now
    )
    
    print("\n📦 Test Context:")
    print(f"   Content: {test_context.clipboard_content}")
    print(f"   Type: {test_context.clipboard_metadata['type']}")
    
    # Test with fast model
    print("\n🧪 Testing with FAST model (3B)...")
    response = client.analyze_context(test_context, mode='fast')
    
    print(f"\n📊 Response:")
    print(f"   Action Type: {response.action_type}")
    print(f"   Suggested Action: {response.suggested_action}")
    print(f"   Confidence: {response.confidence}")
    print(f"   Reasoning: {response.reasoning}")
    print(f"   Response Time: {response.response_time_ms:.0f}ms")
    print(f"   Model: {response.model_used}")
    
    # Show stats
    stats = client.get_stats()
    print(f"\n📈 Client Stats:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Successful: {stats['successful_requests']}")
    print(f"   Failed: {stats['failed_requests']}")
    print(f"   Avg response time: {stats['avg_response_time_ms']:.0f}ms")
    
    # Check if we met the target
    if response.response_time_ms < 3000:
        print(f"\n✅ Response time target met: <3 seconds")
    else:
        print(f"\n⚠️  Response time target missed: {response.response_time_ms/1000:.1f}s")
