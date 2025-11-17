"""
Greeting Detection Plugin - Phase 5: Advanced Features
Detects and responds to greetings without calling Brain AI

High priority plugin that responds instantly to common greetings.
"""

import re
import logging
import random
from typing import List
from pathlib import Path
from datetime import datetime

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class GreetingPlugin(BasePlugin):
    """
    Detects greetings and responds instantly without calling Brain AI.
    
    Features:
    - Detects: hi, hello, hey, good morning, good afternoon, good evening
    - Time-appropriate responses
    - High confidence (0.99) for instant activation
    - Priority 10 (highest)
    """
    
    # Greeting patterns (case-insensitive)
    GREETING_PATTERNS = [
        r'\bhi\b',
        r'\bhello\b',
        r'\bhey\b',
        r'\bhiya\b',
        r'\bhowdy\b',
        r'\bgreetings\b',
        r'\bgood\s+morning\b',
        r'\bgood\s+afternoon\b',
        r'\bgood\s+evening\b',
        r'\bgood\s+day\b',
        r'\bwhat\'?s\s+up\b',
        r'\bhow\s+are\s+you\b',
        r'\bhow\'?s\s+it\s+going\b',
    ]
    
    # Response templates
    RESPONSES = {
        'morning': [
            "Good morning! ☀️ How can I help you today?",
            "Morning! 🌅 Ready to tackle the day? What can I do for you?",
            "Good morning! ☕ What would you like to work on?",
        ],
        'afternoon': [
            "Good afternoon! 👋 What can I help you with?",
            "Hey! 🌤️ How can I assist you this afternoon?",
            "Good afternoon! What's on your mind?",
        ],
        'evening': [
            "Good evening! 🌙 How can I help?",
            "Evening! 🌆 What can I do for you?",
            "Good evening! Still working hard? How can I assist?",
        ],
        'default': [
            "Hi there! 👋 How can I help you today?",
            "Hello! 🤖 What would you like me to do?",
            "Hey! I'm Synth, your AI assistant. How can I help?",
            "Greetings! 🚀 What can I do for you?",
        ]
    }
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="greeting_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Instant greeting responses without AI call",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains a greeting."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text.strip().lower()
        
        # Must be short (greetings are typically 1-5 words)
        word_count = len(text.split())
        if word_count > 10:
            return False
        
        # Check for greeting patterns
        for pattern in self.GREETING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Provide greeting response."""
        if not self.can_handle(context):
            return []
        
        # Determine time of day
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        elif 17 <= hour < 22:
            time_of_day = 'evening'
        else:
            time_of_day = 'default'
        
        # Select random response for this time of day
        response = random.choice(self.RESPONSES[time_of_day])
        
        # Create suggestion
        suggestion = PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_message',
            title='👋 Greeting',
            description=response,
            confidence=0.99,  # Very high confidence
            action_params={
                'message': response,
                'type': 'greeting'
            },
            priority=10  # Highest priority
        )
        
        return [suggestion]
    
    def on_suggestion_accepted(self, suggestion: PluginSuggestion):
        """Track greeting acceptance."""
        logger.info(f"Greeting accepted: {suggestion.description[:30]}...")
    
    def on_suggestion_rejected(self, suggestion: PluginSuggestion):
        """Track greeting rejection."""
        logger.debug(f"Greeting rejected: {suggestion.description[:30]}...")


if __name__ == "__main__":
    print("\n🧪 Testing Greeting Plugin...\n")
    
    plugin = GreetingPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    print(f"   Priority: 10 (Highest)")
    print(f"   Confidence: 0.99")
    
    # Test greetings
    test_cases = [
        "hi",
        "hello",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "what's up",
        "how are you",
        "This is not a greeting at all, it's a long sentence",
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: '{test}'")
        print(f"{'='*60}")
        
        context = PluginContext(clipboard_text=test)
        can_handle = plugin.can_handle(context)
        print(f"Can handle: {can_handle}")
        
        if can_handle:
            suggestions = plugin.analyze(context)
            for s in suggestions:
                print(f"\n✅ Suggestion:")
                print(f"   Title: {s.title}")
                print(f"   Response: {s.description}")
                print(f"   Confidence: {s.confidence}")
                print(f"   Priority: {s.priority}")
    
    print("\n" + "="*60)
    print("✅ Greeting Plugin test complete!")
    print("="*60 + "\n")
