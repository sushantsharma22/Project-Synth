#!/usr/bin/env python3
"""
RAG - Web Search Module (Ultimate Hybrid Search Strategy)
3-Tier Waterfall: Google (free) → DuckDuckGo (free) → Tavily (premium)
Searches the web and retrieves relevant information for AI context
"""

import requests
import os
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
    Web Search RAG with Ultimate Hybrid Strategy
    
    3-Tier Waterfall Architecture:
    ┌─────────────────────────────────────┐
    │ TIER 1: Google Direct (Free)       │ ← Fast, 2s timeout
    │ ↓ If 0 results                      │
    │ TIER 2: DuckDuckGo (Free)          │ ← Reliable fallback
    │ ↓ If 0 results OR deep research    │
    │ TIER 3: Tavily (Premium)           │ ← Unblockable safety net
    └─────────────────────────────────────┘
    
    Goal: Free 90% of the time, Unblockable 100% of the time
    """
    
    def __init__(self):
        self.timeout = 8  # Default timeout
        
        # Session for Google/DuckDuckGo (helps avoid blocks)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        # Tavily client (lazy initialization)
        self._tavily_client = None
        self._tavily_available = False
        
        # Try to initialize Tavily
        try:
            from tavily import TavilyClient
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                self._tavily_client = TavilyClient(api_key=tavily_api_key)
                self._tavily_available = True
                print("🔑 Tavily initialized (Premium Tier available)")
            else:
                print("⚠️  Tavily API key not found (Premium Tier unavailable)")
        except Exception as e:
            print(f"⚠️  Tavily initialization failed: {e}")
            self._tavily_available = False
    
    def search_tavily(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        TIER 3: Premium search using Tavily API
        
        The "Unblockable" safety net - activated when free tiers fail
        or for deep research queries.
        
        Args:
            query: Search query
            max_results: Maximum number of results (default 5)
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        if not self._tavily_available:
            print("❌ Tavily unavailable (API key not configured)")
            return results
        
        try:
            print(f"🔍 TIER 3 (Premium): Tavily search for '{query}'...")
            
            # Perform Tavily search with basic depth (faster, cheaper)
            response = self._tavily_client.search(
                query=query,
                search_depth="basic",  # "basic" is faster/cheaper than "advanced"
                max_results=max_results
            )
            
            # Convert Tavily results to our standard format
            if response and 'results' in response:
                for item in response['results']:
                    results.append(SearchResult(
                        title=item.get('title', 'Untitled'),
                        url=item.get('url', ''),
                        snippet=item.get('content', '')[:500],  # Limit snippet length
                        source='Tavily (Premium)'
                    ))
                
                print(f"✅ Tavily returned {len(results)} results")
            else:
                print("⚠️  Tavily returned no results")
                
        except Exception as e:
            print(f"❌ Tavily search error: {e}")
            # Never crash - just return empty list
        
        return results
        
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
        TIER 1: Search Google directly (free scraping with answer extraction)
        
        Uses BeautifulSoup for reliable parsing of Google search results.
        Stealthy headers to avoid detection.
        Fast timeout (2s) - fails fast if blocked.
        """
        results = []
        try:
            import re
            from urllib.parse import quote
            from bs4 import BeautifulSoup
            
            # Google search URL with multiple parameters to look more legitimate
            search_url = f"https://www.google.com/search?q={quote(query)}&num=10&hl=en"
            
            # STEALTH HEADERS - Mimic real Chrome 122 on Mac (harder to detect)
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
            
            # Fast timeout (2s) - fail fast if Google blocks us
            response = self.session.get(search_url, headers=headers, timeout=2)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # STEP 1: Try to extract Google Answer Box / Knowledge Graph
                # Method A: Regex extraction for BNeawe class (direct answers)
                answer_box_pattern = r'<div[^>]*class="[^"]*BNeawe[^"]*"[^>]*>([^<]+)</div>'
                answer_matches = re.findall(answer_box_pattern, html)
                
                if answer_matches:
                    # Clean and combine answer matches
                    direct_answer = ' '.join([match.strip() for match in answer_matches[:3]])
                    direct_answer = ' '.join(direct_answer.split())  # Clean whitespace
                    
                    if direct_answer and len(direct_answer) > 10:
                        results.append(SearchResult(
                            title='📍 Direct Answer',
                            url='',
                            snippet=direct_answer[:500],
                            source='Google Answer Box'
                        ))
                        print(f"✅ Google Answer Box (Regex): {direct_answer[:80]}...")
                
                # Method B: BeautifulSoup extraction as fallback
                if not answer_matches:
                    answer_divs = soup.find_all('div', class_=re.compile(r'BNeawe.*'))
                    if answer_divs and len(answer_divs) > 0:
                        direct_answer = ' '.join([div.get_text() for div in answer_divs[:3]])
                        direct_answer = ' '.join(direct_answer.split())  # Clean whitespace
                        
                        if direct_answer and len(direct_answer) > 10:
                            results.append(SearchResult(
                                title='📍 Direct Answer',
                                url='',
                                snippet=direct_answer[:500],
                                source='Google Answer Box'
                            ))
                            print(f"✅ Google Answer Box (BS4): {direct_answer[:80]}...")
                
                # STEP 2: Extract regular search results using BeautifulSoup
                # Find all search result containers
                search_divs = soup.find_all('div', class_='g')
                
                for div in search_divs[:8]:  # Top 8 results
                    try:
                        # Extract title (h3 tag)
                        h3 = div.find('h3')
                        title = h3.get_text() if h3 else None
                        
                        # Extract snippet (various possible classes)
                        snippet_div = div.find('div', class_=re.compile(r'VwiC3b|IsZvec|s3v9rd'))
                        snippet = snippet_div.get_text() if snippet_div else None
                        
                        # Extract URL (from anchor tag)
                        link = div.find('a', href=True)
                        url = str(link['href']) if link and link.get('href') else ''
                        
                        if title and snippet:
                            results.append(SearchResult(
                                title=title[:200],
                                url=url[:300],
                                snippet=snippet[:400],
                                source='Google'
                            ))
                    except Exception as e:
                        continue  # Skip malformed results
                
                print(f"✅ Google (BeautifulSoup): Extracted {len(results)} results")
            else:
                print(f"⚠️  Google returned status {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️  Google search failed: {e}")
            
        return results
    
    def search(self, query: str, include_news: bool = True) -> Dict:
        """
        ULTIMATE HYBRID SEARCH - 3-Tier Waterfall Strategy
        
        Architecture:
        ┌──────────────────────────────────────────────────┐
        │ TIER 1: Google Direct (Free, 2s timeout)        │
        │   ↓ If 0 results or blocked                     │
        │ TIER 2: DuckDuckGo (Free, reliable fallback)    │
        │   ↓ If BOTH fail OR deep research query         │
        │ TIER 3: Tavily (Premium, unblockable)          │
        └──────────────────────────────────────────────────┘
        
        Goal: Free 90% of the time, Unblockable 100% of the time
        
        Args:
            query: Search query
            include_news: Whether to include recent news (default True)
            
        Returns:
            Dict with search results and formatted context
        """
        all_results = []
        tier_used = []
        
        # Check if this is a "deep research" query (needs premium)
        query_lower = query.lower()
        deep_research_keywords = [
            'report', 'comprehensive', 'analysis', 'detailed study',
            'in-depth', 'research paper', 'full analysis', 'complete report'
        ]
        needs_premium = any(keyword in query_lower for keyword in deep_research_keywords)
        
        # ═══════════════════════════════════════════════════════════
        # TIER 1: Google Direct (Free & Fast)
        # ═══════════════════════════════════════════════════════════
        print("🔍 TIER 1 (Free): Trying Google Direct...")
        google_results = self.search_google_direct(query)
        
        if google_results and len(google_results) > 0:
            print(f"✅ TIER 1 SUCCESS: Google returned {len(google_results)} results")
            all_results.extend(google_results)
            tier_used.append("Google (Free)")
            
            # Check if we have a Direct Answer - if so, we're golden!
            has_direct_answer = any('📍 Direct Answer' in r.title for r in google_results)
            if has_direct_answer:
                print("🎯 Direct Answer found - stopping here!")
                # Skip other tiers, we have what we need
            else:
                # Good results but no direct answer - continue if query needs deep research
                if not needs_premium:
                    print("✅ Sufficient results from Google - stopping here")
        else:
            # ═══════════════════════════════════════════════════════════
            # TIER 2: DuckDuckGo (Free Fallback)
            # ═══════════════════════════════════════════════════════════
            print("⚠️  TIER 1 FAILED: Google blocked/empty (0 results)")
            print("🔍 TIER 2 (Free): Switching to DuckDuckGo...")
            
            ddg_results = self.search_duckduckgo(query, max_results=5)
            
            if ddg_results and len(ddg_results) > 0:
                print(f"✅ TIER 2 SUCCESS: DuckDuckGo returned {len(ddg_results)} results")
                all_results.extend(ddg_results)
                tier_used.append("DuckDuckGo (Free)")
                
                # If not deep research, stop here
                if not needs_premium:
                    print("✅ Sufficient results from DuckDuckGo - stopping here")
            else:
                print("⚠️  TIER 2 FAILED: DuckDuckGo also returned 0 results")
        
        # ═══════════════════════════════════════════════════════════
        # TIER 3: Tavily (Premium Safety Net)
        # ═══════════════════════════════════════════════════════════
        # Activate Tavily if:
        # 1. BOTH Google and DuckDuckGo failed (0 results), OR
        # 2. Query explicitly needs deep research
        
        should_use_tavily = (
            (len(all_results) == 0) or  # Both free tiers failed
            (needs_premium and len(all_results) < 3)  # Deep research needs more
        )
        
        if should_use_tavily:
            if len(all_results) == 0:
                print("🚨 TIER 3 ACTIVATION: Both free tiers failed - activating Premium Fallback...")
            else:
                print(f"🔬 TIER 3 ACTIVATION: Deep research query detected - supplementing with Premium results...")
            
            tavily_results = self.search_tavily(query, max_results=5)
            
            if tavily_results and len(tavily_results) > 0:
                print(f"✅ TIER 3 SUCCESS: Tavily returned {len(tavily_results)} results")
                all_results.extend(tavily_results)
                tier_used.append("Tavily (Premium)")
            else:
                print("⚠️  TIER 3 FAILED: Even Tavily returned 0 results (rare!)")
        
        # ═══════════════════════════════════════════════════════════
        # OPTIONAL: News Search (runs alongside if needed)
        # ═══════════════════════════════════════════════════════════
        if include_news:
            news_keywords = [
                'latest', 'recent', 'today', 'election', 'news', 
                'current', 'yesterday', 'breaking', '2025', '2024'
            ]
            needs_news = any(keyword in query_lower for keyword in news_keywords)
            
            if needs_news:
                print("📰 Adding news results...")
                news_results = self.search_news(query)
                if news_results:
                    all_results.extend(news_results)
                    tier_used.append("News Feed")
        
        # ═══════════════════════════════════════════════════════════
        # FINALIZE: Deduplicate and format
        # ═══════════════════════════════════════════════════════════
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result.title.lower()[:50], result.url)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Format context for AI
        context = self.format_context(unique_results)
        
        # Summary message
        tier_summary = " → ".join(tier_used) if tier_used else "No tiers used"
        print(f"\n📊 SEARCH COMPLETE: {len(unique_results)} unique results")
        print(f"🔄 Tiers used: {tier_summary}")
        
        return {
            'query': query,
            'results': unique_results,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'sources_count': len(unique_results),
            'tiers_used': tier_used  # Track which tiers were activated
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
