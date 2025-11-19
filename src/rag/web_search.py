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
        self.timeout = 8  # Increased from 5 to 8 seconds
        # Add session for persistent cookies (helps avoid blocks)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Search using DuckDuckGo HTML scraping
        More reliable than API for current events
        """
        results = []
        try:
            # Use DuckDuckGo HTML search
            from urllib.parse import quote_plus
            encoded_query = quote_plus(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            
            # DuckDuckGo returns 202 (Accepted) instead of 200
            if response.status_code in [200, 202]:
                html = response.text
                import re
                
                # Try BeautifulSoup for better parsing
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all result divs
                    result_divs = soup.find_all('div', class_='result')
                    
                    print(f"🔍 DuckDuckGo: Found {len(result_divs)} result blocks for '{query}'")
                    
                    for div in result_divs[:max_results]:
                        # Extract title link
                        title_link = div.find('a', class_='result__a')
                        if not title_link:
                            continue
                        
                        title = title_link.get_text(strip=True)
                        url = title_link.get('href', '')
                        # Ensure url is a string
                        if isinstance(url, list):
                            url = url[0] if url else ''
                        url_str = str(url) if url else ''
                        
                        # Extract snippet
                        snippet_elem = div.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        if title:
                            results.append(SearchResult(
                                title=title[:200],
                                url=url_str[:300],
                                snippet=snippet[:500] if snippet else title[:500],
                                source='DuckDuckGo'
                            ))
                    
                    print(f"✅ DuckDuckGo (BeautifulSoup): Extracted {len(results)} results")
                    
                except ImportError:
                    # Fallback to regex if BeautifulSoup not available
                    print("⚠️ BeautifulSoup not available, using regex fallback")
                    
                    # Simpler regex: just find links with "result__a" class
                    link_pattern = r'<a[^>]*class="result__a"[^>]*>([^<]+)</a>'
                    titles = re.findall(link_pattern, html)
                    
                    print(f"🔍 DuckDuckGo (regex): Found {len(titles)} titles for '{query}'")
                    
                    for title in titles[:max_results]:
                        title_clean = re.sub(r'\s+', ' ', title.strip())
                        if title_clean:
                            results.append(SearchResult(
                                title=title_clean[:200],
                                url='',
                                snippet=title_clean,  # Use title as snippet if no snippet found
                                source='DuckDuckGo'
                            ))
                    
                    print(f"✅ DuckDuckGo (regex): Extracted {len(results)} results")
            else:
                print(f"⚠️ DuckDuckGo returned status {response.status_code}")
            
            # Fallback to API if HTML parsing fails or no results
            if not results:
                print("🔄 Trying DuckDuckGo API fallback...")
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
                    print(f"✅ DuckDuckGo API: Got abstract")
                
                # Get related topics (handle nested structure)
                for topic in data.get('RelatedTopics', [])[:max_results]:
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
                            for subtopic in topic.get('Topics', [])[:max_results]:
                                if 'Text' in subtopic and 'FirstURL' in subtopic:
                                    results.append(SearchResult(
                                        title=subtopic.get('Text', '')[:100],
                                        url=subtopic.get('FirstURL', ''),
                                        snippet=subtopic.get('Text', ''),
                                        source='DuckDuckGo'
                                    ))
                    
                    if len(results) >= max_results:
                        break
                
                print(f"✅ DuckDuckGo API: Got {len(results)} results")
                    
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
        Search Google directly (PRIMARY method - free scraping)
        Extracts direct answers from Knowledge Graph/Answer Box
        """
        results = []
        try:
            import re
            from urllib.parse import quote
            
            # Better headers to avoid blocks
            search_url = f"https://www.google.com/search?q={quote(query)}&num=10"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = self.session.get(search_url, timeout=self.timeout)
            
            if response.status_code == 200:
                html = response.text
                
                # STEP 1: Extract Knowledge Graph / Answer Box (BNeawe class for direct answers)
                # This captures weather, quick facts, definitions
                answer_pattern = r'<div[^>]*class="[^"]*BNeawe[^"]*"[^>]*>([^<]+)</div>'
                answer_matches = re.findall(answer_pattern, html)
                
                if answer_matches:
                    # Combine first few matches for direct answer
                    direct_answer = ' '.join(answer_matches[:3])
                    # Clean up
                    direct_answer = re.sub(r'\s+', ' ', direct_answer.strip())
                    
                    if direct_answer and len(direct_answer) > 10:
                        results.append(SearchResult(
                            title='📍 Direct Answer',
                            url='',
                            snippet=direct_answer[:500],
                            source='Google Direct'
                        ))
                        print(f"✅ Google Direct Answer: {direct_answer[:100]}...")
                
                # STEP 2: Extract regular search results
                # Pattern for title
                title_pattern = r'<h3[^>]*>([^<]+)</h3>'
                titles = re.findall(title_pattern, html)
                
                # Pattern for snippet - multiple possible classes
                snippet_patterns = [
                    r'<div class="VwiC3b[^"]*"[^>]*>([^<]+)</div>',
                    r'<span class="st"[^>]*>([^<]+)</span>',
                    r'<div class="IsZvec"[^>]*>([^<]+)</div>'
                ]
                
                snippets = []
                for pattern in snippet_patterns:
                    snippets.extend(re.findall(pattern, html))
                    if snippets:
                        break
                
                print(f"🔍 Google: Found {len(titles)} titles, {len(snippets)} snippets for '{query}'")
                
                # Combine results (skip first result if we already have direct answer)
                start_idx = 0
                for i in range(start_idx, min(len(titles), len(snippets), 8)):
                    if titles[i] and snippets[i]:
                        results.append(SearchResult(
                            title=titles[i][:200],
                            url='',
                            snippet=snippets[i][:400],
                            source='Google'
                        ))
                
                print(f"✅ Google: Extracted {len(results)} total results")
            else:
                print(f"⚠️ Google returned status {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Google search failed: {e}")
            
        return results
    
    def search(self, query: str, include_news: bool = True) -> Dict:
        """
        Main search function - PRIORITIZES FREE GOOGLE SCRAPING
        
        Args:
            query: Search query
            include_news: Whether to include recent news (default True for current events)
            
        Returns:
            Dict with search results and formatted context
        """
        all_results = []
        
        # PRIORITY 1: Try Google Direct (free scraping with answer extraction)
        print("🔍 PRIMARY: Trying Google Direct...")
        google_results = self.search_google_direct(query)
        all_results.extend(google_results)
        
        # PRIORITY 2: Only use DuckDuckGo if Google returns 0 results
        if not google_results:
            print("🔄 FALLBACK: Google returned 0 results, trying DuckDuckGo...")
            ddg_results = self.search_duckduckgo(query, max_results=5)
            all_results.extend(ddg_results)
        else:
            print(f"✅ Google returned {len(google_results)} results, skipping DuckDuckGo")
        
        # PRIORITY 3: News search (runs alongside if needed)
        if include_news:
            query_lower = query.lower()
            news_keywords = ['latest', 'recent', 'today', 'election', 'news', 'current', 'yesterday', 'breaking', '2025', '2024']
            actually_needs_news = any(keyword in query_lower for keyword in news_keywords)
            
            if actually_needs_news:
                print("📰 Adding news results...")
                news_results = self.search_news(query)
                all_results.extend(news_results)
        
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
