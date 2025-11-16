"""
Web Search/Research Plugin - Phase 5: Advanced Features
Smart web searches, article summarization, research assistance, content indexing

Enhanced with RAG integration for indexing web content
"""

import re
import logging
from typing import List, Optional
from pathlib import Path
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

# Try to import readability for clean text extraction
try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False
    print("⚠️  readability-lxml not installed. Run: pip install readability-lxml")

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
        
        if not context.clipboard_text:
            return suggestions
            
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
    
    def fetch_and_index(self, url: str, rag=None) -> Optional[str]:
        """
        Fetch webpage content and add to RAG (new feature)
        
        Args:
            url: URL to fetch
            rag: SynthRAG instance (optional)
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Extract clean text
            if READABILITY_AVAILABLE:
                # Use readability for clean article extraction
                doc = Document(response.text)
                title = doc.title()
                content = doc.summary()
                
                # Parse HTML to get text
                soup = BeautifulSoup(content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
            else:
                # Fallback to basic BeautifulSoup extraction
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get title
                title = soup.title.string if soup.title else url
                
                # Get text
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            # Add to RAG if provided
            if rag and clean_text:
                metadata = {
                    'url': url,
                    'title': title,
                    'content_type': 'webpage'
                }
                rag.add_document(clean_text, url, metadata)
                logger.info(f"Indexed webpage: {url}")
            
            return clean_text
            
        except Exception as e:
            logger.error(f"Failed to fetch/index {url}: {e}")
            return None
    
    def search_indexed_content(self, query: str, rag=None, top_k: int = 3) -> Optional[List]:
        """
        Search previously indexed web content in RAG
        
        Args:
            query: Search query
            rag: SynthRAG instance (optional)
            top_k: Number of results
            
        Returns:
            List of search results from RAG or None
        """
        if not rag:
            return None
        
        try:
            # Search RAG for web content
            results = rag.search(query, top_k=top_k, min_score=0.4)
            
            # Filter for webpage sources only
            web_results = [
                r for r in results 
                if r.get('metadata', {}).get('content_type') == 'webpage'
            ]
            
            return web_results
            
        except Exception as e:
            logger.error(f"Failed to search indexed content: {e}")
            return None


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
    
    # Test 4: Fetch and index (if URL provided)
    print("\n4️⃣ Test: Fetch and Index")
    test_url = "https://example.com"
    print(f"   Testing with URL: {test_url}")
    content = plugin.fetch_and_index(test_url)
    if content:
        print(f"   ✅ Fetched {len(content)} characters")
        print(f"   Preview: {content[:100]}...")
    else:
        print(f"   ⚠️  Could not fetch content (expected for example.com)")
    
    print("\n✅ Web Search Plugin test complete!\n")
