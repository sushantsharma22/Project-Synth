"""
Web Tools - External Data Access for AI Agent
Provides robust web search, Wikipedia access, and modern web page reading
"""

import time
from typing import List, Dict, Optional


class RobustSearch:
    """Robust web search with backend fallback strategy"""
    
    def __init__(self):
        """Initialize search tool"""
        pass
    
    def search(self, query: str, max_results: int = 5) -> str:
        """
        Search the web with backend-switching logic for reliability.
        Tries 'api' backend first, then 'html', then 'lite' if previous fails.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Formatted string of search results with titles, snippets, and URLs
        """
        from duckduckgo_search import DDGS
        
        backends = ['api', 'html', 'lite']
        results = []
        
        for backend in backends:
            try:
                print(f"🔍 Trying DuckDuckGo backend: {backend}")
                
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(
                        query, 
                        backend=backend,
                        max_results=max_results
                    ))
                    
                    if search_results:
                        results = search_results
                        print(f"✅ Success with {backend} backend - found {len(results)} results")
                        break
                        
            except Exception as e:
                print(f"❌ {backend} backend failed: {e}")
                if backend == backends[-1]:
                    # Last backend failed
                    return f"Search failed: {str(e)}"
                continue
        
        if not results:
            return "No search results found."
        
        # Format results
        formatted = f"🔍 Search Results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            snippet = result.get('body', 'No description')
            url = result.get('href', 'No URL')
            
            formatted += f"{i}. {title}\n"
            formatted += f"   {snippet}\n"
            formatted += f"   URL: {url}\n\n"
        
        return formatted
    
    def get_top_urls(self, query: str, num_urls: int = 3) -> List[str]:
        """
        Get just the URLs from search results
        
        Args:
            query: Search query
            num_urls: Number of URLs to return
            
        Returns:
            List of URLs
        """
        from duckduckgo_search import DDGS
        
        backends = ['api', 'html', 'lite']
        
        for backend in backends:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, backend=backend, max_results=num_urls))
                    
                    if results:
                        return [r.get('href', '') for r in results if r.get('href')]
                        
            except Exception as e:
                print(f"❌ {backend} failed: {e}")
                continue
        
        return []


class WikiTool:
    """Wikipedia access with error handling"""
    
    def __init__(self):
        """Initialize Wikipedia tool"""
        import wikipedia
        self.wikipedia = wikipedia
    
    def get_summary(self, topic: str, sentences: int = 5) -> str:
        """
        Get Wikipedia summary with graceful error handling
        
        Args:
            topic: Topic to search for
            sentences: Number of sentences to return
            
        Returns:
            Wikipedia summary or error message
        """
        try:
            print(f"📖 Searching Wikipedia for: {topic}")
            summary = self.wikipedia.summary(topic, sentences=sentences, auto_suggest=True)
            print(f"✅ Found Wikipedia article")
            return f"📖 Wikipedia Summary:\n\n{summary}"
            
        except self.wikipedia.exceptions.DisambiguationError as e:
            # Multiple topics match - return options
            options = e.options[:5]  # First 5 options
            return f"Multiple topics found. Did you mean:\n" + "\n".join(f"- {opt}" for opt in options)
            
        except self.wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{topic}'"
            
        except Exception as e:
            return f"Wikipedia error: {str(e)}"


class WebReader:
    """
    CRITICAL FIX: Uses Playwright browser automation instead of requests
    This ensures modern JavaScript-heavy websites are read correctly
    """
    
    def __init__(self):
        """Initialize web reader"""
        self.timeout = 15000  # 15 seconds timeout
    
    def read_url(self, url: str, max_chars: int = 8000) -> str:
        """
        Read webpage content using Playwright browser automation.
        This is THE CRITICAL FIX - uses headless browser to handle JavaScript.
        
        Args:
            url: URL to read
            max_chars: Maximum characters to return
            
        Returns:
            Extracted text content from webpage
        """
        from playwright.sync_api import sync_playwright
        
        try:
            print(f"🌐 Reading URL with Playwright: {url}")
            
            with sync_playwright() as p:
                # Launch headless Chromium browser
                browser = p.chromium.launch(headless=True)
                
                try:
                    # Create new page
                    page = browser.new_page()
                    
                    # Navigate to URL and wait for page to load
                    page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    
                    # Wait a bit for JavaScript to execute
                    page.wait_for_timeout(2000)  # 2 seconds
                    
                    # Extract text from body tag
                    body_text = page.inner_text('body')
                    
                    # Close browser
                    browser.close()
                    
                    # Truncate if too long
                    if len(body_text) > max_chars:
                        body_text = body_text[:max_chars] + "..."
                    
                    print(f"✅ Successfully read {len(body_text)} characters")
                    return body_text
                    
                except Exception as e:
                    browser.close()
                    raise e
                    
        except Exception as e:
            error_msg = f"Failed to read URL: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def read_multiple_urls(self, urls: List[str], max_chars_per_url: int = 4000) -> str:
        """
        Read multiple URLs and combine their content
        
        Args:
            urls: List of URLs to read
            max_chars_per_url: Max characters per URL
            
        Returns:
            Combined text from all URLs
        """
        combined_text = ""
        
        for i, url in enumerate(urls, 1):
            print(f"\n📄 Reading URL {i}/{len(urls)}: {url}")
            content = self.read_url(url, max_chars=max_chars_per_url)
            
            combined_text += f"\n\n=== SOURCE {i}: {url} ===\n"
            combined_text += content
            
            # Small delay between requests
            if i < len(urls):
                time.sleep(1)
        
        return combined_text
