#!/usr/bin/env python3
"""
RAG - Web Search Module
Searches the web and retrieves relevant information for AI context
"""

import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
from datetime import datetime


@dataclass
class SearchResult:
    """A single search result"""
    title: str
    url: str
    snippet: str
    source: str


class WebSearchRAG:
    """
    Web search for RAG (Retrieval-Augmented Generation)
    Searches multiple sources and aggregates results
    """
    
    def __init__(self):
        self.timeout = 5
        
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Search using DuckDuckGo HTML scraping
        More reliable than API for current events
        """
        results = []
        try:
            # Use DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                # Simple HTML parsing to extract results
                html = response.text
                
                # Find result blocks (simplified parsing)
                import re
                
                # Extract title and snippet patterns
                pattern = r'<a class="result__a"[^>]*>([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, html, re.DOTALL)
                
                for i, (title, snippet) in enumerate(matches[:max_results]):
                    # Clean up HTML entities
                    title = title.strip()
                    snippet = snippet.strip()
                    
                    results.append(SearchResult(
                        title=title[:200],
                        url='',  # URL extraction is complex, skipping for now
                        snippet=snippet[:500],
                        source='DuckDuckGo'
                    ))
            
            # Fallback to API if HTML parsing fails
            if not results:
                api_url = "https://api.duckduckgo.com/"
                params = {
                    'q': query,
                    'format': 'json',
                    'no_html': 1,
                    'skip_disambig': 1
                }
                
                response = requests.get(api_url, params=params, timeout=self.timeout)
                data = response.json()
                
                # Get abstract if available
                if data.get('Abstract'):
                    results.append(SearchResult(
                        title=data.get('Heading', query),
                        url=data.get('AbstractURL', ''),
                        snippet=data['Abstract'],
                        source='DuckDuckGo'
                    ))
                
                # Get related topics (handle nested structure)
                for topic in data.get('RelatedTopics', []):
                    if isinstance(topic, dict):
                        if 'Text' in topic and 'FirstURL' in topic:
                            # Direct topic
                            results.append(SearchResult(
                                title=topic.get('Text', '')[:100],
                                url=topic.get('FirstURL', ''),
                                snippet=topic.get('Text', ''),
                                source='DuckDuckGo'
                            ))
                        elif 'Topics' in topic:
                            # Nested topics
                            for subtopic in topic.get('Topics', []):
                                if 'Text' in subtopic and 'FirstURL' in subtopic:
                                    results.append(SearchResult(
                                        title=subtopic.get('Text', '')[:100],
                                        url=subtopic.get('FirstURL', ''),
                                        snippet=subtopic.get('Text', ''),
                                        source='DuckDuckGo'
                                    ))
                    
                    if len(results) >= max_results:
                        break
                    
        except Exception as e:
            print(f"⚠️ DuckDuckGo search failed: {e}")
            
        return results
    
    def search_wikipedia(self, query: str) -> List[SearchResult]:
        """
        Search Wikipedia for information (DISABLED - API issues)
        """
        # Wikipedia API has JSON parsing issues, disabled for now
        return []
    
    def search_news(self, query: str) -> List[SearchResult]:
        """
        Search for recent news articles
        Uses Google News RSS (no API key needed)
        """
        results = []
        try:
            import feedparser
            from urllib.parse import quote_plus
            
            # Google News RSS feed with proper URL encoding
            encoded_query = quote_plus(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            feed = feedparser.parse(url)
            
            for entry in feed.entries[:5]:  # Get more results
                title_val = entry.get('title', '')
                url_val = entry.get('link', '')
                summary_val = entry.get('summary', '')
                
                results.append(SearchResult(
                    title=str(title_val) if title_val else '',
                    url=str(url_val) if url_val else '',
                    snippet=str(summary_val)[:300] if summary_val else '',
                    source='Google News'
                ))
                
        except ImportError:
            print("⚠️ feedparser not installed, skipping news search")
        except Exception as e:
            print(f"⚠️ News search failed: {e}")
            
        return results
    
    def search_google_direct(self, query: str) -> List[SearchResult]:
        """
        Search Google directly (backup method)
        Uses simple HTTP request to Google search
        """
        results = []
        try:
            import re
            from urllib.parse import quote
            
            search_url = f"https://www.google.com/search?q={quote(query)}&num=5"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                html = response.text
                
                # Extract search result titles and snippets
                # Pattern for title
                title_pattern = r'<h3[^>]*>([^<]+)</h3>'
                titles = re.findall(title_pattern, html)
                
                # Pattern for snippet
                snippet_pattern = r'<div class="VwiC3b[^"]*"[^>]*>([^<]+)</div>'
                snippets = re.findall(snippet_pattern, html)
                
                # Combine results
                for i in range(min(len(titles), len(snippets), 3)):
                    results.append(SearchResult(
                        title=titles[i][:200],
                        url='',
                        snippet=snippets[i][:400],
                        source='Google'
                    ))
                    
        except Exception as e:
            print(f"⚠️ Google search failed: {e}")
            
        return results
    
    def search(self, query: str, include_news: bool = True) -> Dict:
        """
        Main search function - searches multiple sources with fallbacks
        
        Args:
            query: Search query
            include_news: Whether to include recent news (default True for current events)
            
        Returns:
            Dict with search results and formatted context
        """
        all_results = []
        
        # Auto-detect if news is needed when include_news=True
        if include_news:
            query_lower = query.lower()
            news_keywords = ['latest', 'recent', 'today', 'election', 'news', 'current', 'yesterday', 'breaking', '2025', '2024']
            actually_needs_news = any(keyword in query_lower for keyword in news_keywords)
            
            if actually_needs_news:
                news_results = self.search_news(query)
                all_results.extend(news_results)
        
        # Always try multiple sources for better coverage
        # Priority: DuckDuckGo (fast) → Google (comprehensive)
        ddg_results = self.search_duckduckgo(query, max_results=5)
        all_results.extend(ddg_results)
        
        google_results = self.search_google_direct(query)
        all_results.extend(google_results)
        
        # Deduplicate by URL/title
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result.title.lower()[:50], result.url)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Format context for AI
        context = self.format_context(unique_results)
        
        return {
            'query': query,
            'results': unique_results,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'sources_count': len(unique_results)
        }
    
    def format_context(self, results: List[SearchResult]) -> str:
        """
        Format search results into context for AI
        """
        if not results:
            return "No relevant information found from web search."
        
        context_parts = [
            "=== WEB SEARCH RESULTS ===\n",
            f"Found {len(results)} relevant sources:\n"
        ]
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"\n{i}. {result.title} ({result.source})")
            context_parts.append(f"   URL: {result.url}")
            context_parts.append(f"   {result.snippet[:300]}...\n")
        
        return "\n".join(context_parts)


# Quick test
if __name__ == "__main__":
    rag = WebSearchRAG()
    
    print("🔍 Testing Web Search RAG...")
    
    test_queries = [
        "Bihar elections 2024",
        "Python programming",
        "Climate change"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        results = rag.search(query)
        print(f"Found {results['sources_count']} sources")
        print(results['context'][:500])
