"""
Web Search/Research Plugin - Phase 5: Advanced Features
Smart web searches, article summarization, research assistance
"""

import re
import logging
from typing import List
from pathlib import Path
from urllib.parse import quote_plus

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class WebSearchPlugin(BasePlugin):
    """
    Intelligent web search and research assistance.
    
    Features:
    - Smart search query generation
    - Multi-engine search suggestions
    - Research assistance
    - Article/documentation lookup
    - Stack Overflow integration
    """
    
    # Search engines
    SEARCH_ENGINES = {
        'google': 'https://www.google.com/search?q={}',
        'duckduckgo': 'https://duckduckgo.com/?q={}',
        'bing': 'https://www.bing.com/search?q={}',
        'stackoverflow': 'https://stackoverflow.com/search?q={}',
        'github': 'https://github.com/search?q={}',
        'youtube': 'https://www.youtube.com/results?search_query={}',
        'wikipedia': 'https://en.wikipedia.org/wiki/Special:Search?search={}',
    }
    
    # Question patterns
    QUESTION_WORDS = ['how', 'what', 'why', 'when', 'where', 'who', 'which']
    
    # Code/tech patterns
    CODE_INDICATORS = [
        'error', 'exception', 'bug', 'fix', 'install', 'configure',
        'tutorial', 'guide', 'documentation', 'api', 'library',
        'function', 'class', 'method', 'variable'
    ]
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="web_search_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Intelligent web search and research assistance",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains searchable content."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text.lower()
        
        # Check for questions
        is_question = any(text.startswith(word) for word in self.QUESTION_WORDS) or '?' in text
        
        # Check for search-worthy length (not too short, not too long)
        word_count = len(text.split())
        reasonable_length = 3 <= word_count <= 100
        
        # Check for code/tech indicators
        is_tech = any(indicator in text for indicator in self.CODE_INDICATORS)
        
        return (is_question or is_tech) and reasonable_length
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze and provide search suggestions."""
        suggestions = []
        text = context.clipboard_text.strip()
        
        if not text:
            return suggestions
        
        # Determine search type
        search_type = self._determine_search_type(text)
        
        if search_type == 'code_error':
            suggestions.extend(self._suggest_error_search(text))
        elif search_type == 'question':
            suggestions.extend(self._suggest_question_search(text))
        elif search_type == 'documentation':
            suggestions.extend(self._suggest_documentation_search(text))
        elif search_type == 'general':
            suggestions.extend(self._suggest_general_search(text))
        
        return suggestions
    
    def _determine_search_type(self, text: str) -> str:
        """Determine the type of search needed."""
        text_lower = text.lower()
        
        # Code error
        if 'error' in text_lower or 'exception' in text_lower or 'traceback' in text_lower:
            return 'code_error'
        
        # Documentation
        if 'documentation' in text_lower or 'docs' in text_lower or 'api' in text_lower:
            return 'documentation'
        
        # Question
        if any(text_lower.startswith(word) for word in self.QUESTION_WORDS) or '?' in text:
            return 'question'
        
        return 'general'
    
    def _suggest_error_search(self, text: str) -> List[PluginSuggestion]:
        """Suggest searches for error messages."""
        suggestions = []
        
        # Extract error message (simplified)
        error_msg = self._extract_error_message(text)
        query = quote_plus(error_msg)
        
        # Stack Overflow
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='🔍 Search Stack Overflow',
            description=f'Find solutions for: {error_msg[:50]}...',
            confidence=0.95,
            action_params={'url': self.SEARCH_ENGINES['stackoverflow'].format(query)},
            priority=10
        ))
        
        # Google
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='🌐 Google Search',
            description='Search on Google',
            confidence=0.90,
            action_params={'url': self.SEARCH_ENGINES['google'].format(query)},
            priority=9
        ))
        
        return suggestions
    
    def _suggest_question_search(self, text: str) -> List[PluginSuggestion]:
        """Suggest searches for questions."""
        suggestions = []
        query = quote_plus(text[:200])  # Limit query length
        
        # Google for general questions
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='🔎 Google Search',
            description=f'Search: {text[:50]}...',
            confidence=0.88,
            action_params={'url': self.SEARCH_ENGINES['google'].format(query)},
            priority=9
        ))
        
        # Wikipedia for factual questions
        if any(word in text.lower() for word in ['what is', 'who is', 'where is', 'when was']):
            suggestions.append(PluginSuggestion(
                plugin_name=self.metadata.name,
                action_type='open_url',
                title='📚 Wikipedia',
                description='Search Wikipedia',
                confidence=0.82,
                action_params={'url': self.SEARCH_ENGINES['wikipedia'].format(query)},
                priority=8
            ))
        
        return suggestions
    
    def _suggest_documentation_search(self, text: str) -> List[PluginSuggestion]:
        """Suggest searches for documentation."""
        suggestions = []
        query = quote_plus(text)
        
        # Google with "documentation" added
        doc_query = quote_plus(f"{text} documentation")
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='📖 Search Documentation',
            description='Find official docs',
            confidence=0.90,
            action_params={'url': self.SEARCH_ENGINES['google'].format(doc_query)},
            priority=9
        ))
        
        # GitHub for library/package docs
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='💻 GitHub Search',
            description='Search GitHub repositories',
            confidence=0.85,
            action_params={'url': self.SEARCH_ENGINES['github'].format(query)},
            priority=8
        ))
        
        return suggestions
    
    def _suggest_general_search(self, text: str) -> List[PluginSuggestion]:
        """Suggest general web searches."""
        suggestions = []
        query = quote_plus(text[:200])
        
        # Google
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='🌍 Google Search',
            description=f'Search: {text[:50]}...',
            confidence=0.85,
            action_params={'url': self.SEARCH_ENGINES['google'].format(query)},
            priority=8
        ))
        
        # DuckDuckGo for privacy-conscious users
        suggestions.append(PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='🦆 DuckDuckGo',
            description='Privacy-focused search',
            confidence=0.75,
            action_params={'url': self.SEARCH_ENGINES['duckduckgo'].format(query)},
            priority=6
        ))
        
        return suggestions
    
    def _extract_error_message(self, text: str) -> str:
        """Extract the core error message."""
        lines = text.split('\n')
        
        # Look for lines with "Error" or "Exception"
        for line in lines:
            if 'Error' in line or 'Exception' in line:
                return line.strip()
        
        # Return first line if no error found
        return lines[0][:100]


if __name__ == "__main__":
    print("\n🧪 Testing Web Search Plugin...\n")
    
    plugin = WebSearchPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    
    # Test 1: Error message
    print("\n1️⃣ Test: Error Message")
    context = PluginContext(clipboard_text="TypeError: Cannot read property 'length' of undefined")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 2: Question
    print("\n2️⃣ Test: Question")
    context = PluginContext(clipboard_text="How to use async/await in Python?")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 3: Documentation
    print("\n3️⃣ Test: Documentation")
    context = PluginContext(clipboard_text="React hooks documentation")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    print("\n✅ Web Search Plugin test complete!\n")
