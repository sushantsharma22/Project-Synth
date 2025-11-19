#!/usr/bin/env python3
"""
Live Tools - Zero-Latency Specialized Tools for Instant Answers

These tools handle specific queries INSTANTLY and FOR FREE, bypassing general web search.
Each tool has RICH DOCSTRINGS so the LLM knows EXACTLY when to use them.

Tools:
- Weather: wttr.in API (rain, umbrella, temperature questions)
- Stock Prices: yfinance (stock/crypto price queries)
- Wikipedia: wikipedia API (definitions, history, people)
- Definitions: dictionaryapi.dev (word definitions)
- Website Status: direct HTTP check (is site down?)
- Reddit Opinions: Targeted search (reviews, human opinions)

All tools use robust error handling and never crash.
"""

import requests
from typing import Any
from langchain.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get live weather, temperature, and conditions for any city in the world.
    
    **USE THIS TOOL FOR:**
    - "What's the weather in [city]?"
    - "Do I need an umbrella in [city]?"
    - "Is it raining in [city]?"
    - "Temperature in [city]?"
    - "Should I wear a jacket in [city]?"
    - "Weather forecast [city]"
    
    **INSTANT & FREE** - No API key required (wttr.in).
    
    Args:
        city: City name (e.g., "London", "Tokyo", "New York", "Windsor")
        
    Returns:
        Current weather with conditions, temperature (feels like), and wind speed
        
    Example:
        >>> get_weather("London")
        "Weather in London: Partly cloudy +12°C (feels like +10°C) Wind: 15 km/h"
    """
    try:
        # wttr.in format: %C=condition %t=temp %f=feels_like %w=wind
        url = f"https://wttr.in/{city}?format=%C+%t+(feels+like+%f)+Wind:+%w&m"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        weather = response.text.strip()
        
        if weather and "Unknown location" not in weather:
            return f"Weather in {city}: {weather}"
        else:
            return f"Could not find weather for '{city}'. Please check the city name."
            
    except requests.Timeout:
        return f"Weather service timed out for '{city}'. Please try again."
    except requests.RequestException as e:
        return f"Weather service error for '{city}': {str(e)}"
    except Exception as e:
        return f"Unexpected error getting weather: {str(e)}"


@tool
def get_stock_price(ticker: str) -> str:
    """Get real-time stock prices, cryptocurrency prices, and forex rates.
    
    **USE THIS TOOL FOR:**
    - "What's the price of [stock ticker]?" (e.g., AAPL, TSLA, GOOGL)
    - "Bitcoin price" or "Ethereum price"
    - "How much is [company] stock worth?"
    - "Current price of [crypto]"
    - "Stock market [ticker]"
    
    **INSTANT & FREE** - No API key required (yfinance).
    **AUTO-CONVERTS:** "bitcoin" → BTC-USD, "ethereum" → ETH-USD
    
    Args:
        ticker: Stock ticker (e.g., "AAPL", "TSLA") OR crypto name ("bitcoin", "ethereum")
        
    Returns:
        Current price formatted with currency symbol
        
    Example:
        >>> get_stock_price("AAPL")
        "AAPL: $182.45 USD"
        >>> get_stock_price("bitcoin")
        "BTC-USD: $43,250.12 USD"
    """
    try:
        import yfinance as yf
        
        # Convert common crypto names to ticker format
        ticker_upper = ticker.upper()
        crypto_map = {
            "BITCOIN": "BTC-USD",
            "ETHEREUM": "ETH-USD",
            "ETH": "ETH-USD",
            "BTC": "BTC-USD"
        }
        
        if ticker_upper in crypto_map:
            ticker = crypto_map[ticker_upper]
        
        # Fetch ticker data
        stock = yf.Ticker(ticker)
        
        # Try fast_info first (faster)
        try:
            price = stock.fast_info['last_price']
        except:
            # Fallback to info (slower but more reliable)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if price:
            # Format with commas and 2 decimal places
            formatted_price = f"${price:,.2f}"
            return f"{ticker}: {formatted_price} USD"
        else:
            return f"Could not find price for ticker '{ticker}'. Please verify the ticker symbol."
            
    except ImportError:
        return "Error: yfinance package not installed. Please run: pip install yfinance"
    except Exception as e:
        return f"Error getting stock price for '{ticker}': {str(e)}"


@tool
def search_wikipedia(query: str) -> str:
    """Get authoritative definitions, historical facts, and biographical information from Wikipedia.
    
    **USE THIS TOOL FOR:**
    - "Who is [person]?" (e.g., "Who is Albert Einstein?")
    - "What is [concept]?" (e.g., "What is quantum computing?")
    - "History of [topic]" (e.g., "History of Python programming")
    - "Tell me about [subject]"
    - "Definition of [term]" (general topics, not single words)
    
    **INSTANT & FREE** - No API key required (Wikipedia API).
    **AUTHORITATIVE** - Returns concise 4-sentence summaries from Wikipedia.
    
    Args:
        query: Topic to search (e.g., "Python programming", "Albert Einstein", "World War II")
        
    Returns:
        Wikipedia summary (4 sentences) or disambiguation options if multiple pages exist
        
    Example:
        >>> search_wikipedia("Python programming")
        "Wikipedia: Python is a high-level programming language..."
    """
    try:
        import wikipedia
        
        # Set language to English
        wikipedia.set_lang("en")
        
        # Get summary (4 sentences)
        summary = wikipedia.summary(query, sentences=4, auto_suggest=True)
        
        return f"Wikipedia: {summary}"
        
    except ImportError:
        return "Error: wikipedia package not installed. Please run: pip install wikipedia"
    except Exception as e:
        # Handle DisambiguationError and PageError
        error_str = str(e)
        if "DisambiguationError" in error_str or "may refer to" in error_str:
            # Extract options if available
            try:
                import wikipedia
                # Try to get options from the error
                return f"Multiple Wikipedia pages found for '{query}'. Please be more specific. Try adding more context to your query."
            except:
                return f"Multiple Wikipedia pages found for '{query}'. Please be more specific."
        elif "PageError" in error_str or "page does not exist" in error_str.lower():
            return f"No Wikipedia page found for '{query}'. Please try a different search term."
        else:
            return f"Wikipedia search error for '{query}': {error_str}"


@tool
def get_definition(word: str) -> str:
    """Get the dictionary definition of a single word with part of speech and examples.
    
    **USE THIS TOOL FOR:**
    - "Define [word]" (e.g., "Define ephemeral")
    - "What does [word] mean?"
    - "Meaning of [word]"
    - "Definition of [word]"
    - Single-word lookups only (for concepts/topics, use search_wikipedia instead)
    
    **INSTANT & FREE** - No API key required (dictionaryapi.dev).
    
    Args:
        word: Single word to define (e.g., "ephemeral", "serendipity", "ubiquitous")
        
    Returns:
        Definition with part of speech and optional example sentence
        
    Example:
        >>> get_definition("ephemeral")
        "ephemeral (adjective): Lasting for a very short time."
    """
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            entry = data[0]
            
            # Get first meaning
            if 'meanings' in entry and len(entry['meanings']) > 0:
                meaning = entry['meanings'][0]
                part_of_speech = meaning.get('partOfSpeech', 'unknown')
                
                # Get first definition
                if 'definitions' in meaning and len(meaning['definitions']) > 0:
                    definition = meaning['definitions'][0].get('definition', '')
                    
                    # Get example if available
                    example = meaning['definitions'][0].get('example', '')
                    
                    result = f"{word} ({part_of_speech}): {definition}"
                    
                    if example:
                        result += f"\nExample: \"{example}\""
                    
                    return result
        
        return f"No definition found for '{word}'."
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return f"Word '{word}' not found in dictionary."
        return f"Dictionary API error: {str(e)}"
        
    except requests.Timeout:
        return "Dictionary service timed out. Please try again."
        
    except Exception as e:
        return f"Error getting definition for '{word}': {str(e)}"


@tool
def is_website_down(url: str) -> str:
    """Check if a website is online, offline, or experiencing issues.
    
    **USE THIS TOOL FOR:**
    - "Is [website] down?"
    - "Is [website] working?"
    - "Can you check if [website] is online?"
    - "[Website] status check"
    - "Is [website] having issues?"
    
    **INSTANT & FREE** - Direct HTTP check (no API required).
    
    Args:
        url: Website URL (e.g., "google.com", "https://example.com", "github.com")
        
    Returns:
        Status message: "UP" (working), "DOWN" (offline), or "ISSUES" (errors)
        
    Example:
        >>> is_website_down("google.com")
        "✅ google.com is UP (Status: 200)"
    """
    try:
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Quick HEAD request (faster than GET)
        response = requests.head(url, timeout=5, allow_redirects=True)
        
        status_code = response.status_code
        
        # Status codes < 400 are generally "UP"
        if status_code < 400:
            return f"✅ {url} is UP (Status: {status_code})"
        else:
            return f"⚠️  {url} returned status {status_code} - may be having issues"
            
    except requests.Timeout:
        return f"❌ {url} is DOWN (Timeout - server not responding)"
        
    except requests.ConnectionError:
        return f"❌ {url} is DOWN (Connection refused - server unreachable)"
        
    except requests.RequestException as e:
        return f"❌ {url} is DOWN (Error: {str(e)})"
        
    except Exception as e:
        return f"Error checking {url}: {str(e)}"


@tool
def search_reddit_opinions(topic: str) -> str:
    """Find real human opinions, reviews, and discussions from Reddit communities.
    
    **USE THIS TOOL FOR:**
    - "What do people think about [product]?"
    - "Is [product/service] good?"
    - "Best [category] 2025 Reddit" (e.g., "Best laptops 2025 Reddit")
    - "[Product] reviews from real users"
    - "Reddit opinions on [topic]"
    - "Should I buy [product]?"
    
    **TARGETED SEARCH** - Searches Reddit specifically for authentic user experiences.
    **USE CASE:** When you need real-world opinions vs marketing material.
    
    Args:
        topic: Topic to search on Reddit (e.g., "iPhone 15 review", "best VPN", "M3 MacBook")
        
    Returns:
        Reddit search results with community discussions and opinions
        
    Example:
        >>> search_reddit_opinions("best programming laptop 2025")
        "Reddit opinions on 'best programming laptop 2025': [results from r/programming, r/laptops...]"
    """
    try:
        from src.rag.web_search import WebSearchRAG
        
        # Initialize web search
        rag = WebSearchRAG()
        
        # Search Reddit specifically
        search_query = f"{topic} site:reddit.com"
        
        print(f"🔍 Searching Reddit for: {topic}")
        
        # Perform search (without news)
        results = rag.search(search_query, include_news=False)
        
        if results['sources_count'] > 0:
            # Return formatted context
            context = results['context']
            return f"Reddit opinions on '{topic}':\n\n{context}"
        else:
            return f"No Reddit discussions found for '{topic}'. Try a different search term."
            
    except ImportError as e:
        return f"Error: WebSearchRAG not available - {str(e)}"
        
    except Exception as e:
        return f"Error searching Reddit for '{topic}': {str(e)}"


# Export all tools
__all__ = [
    'get_weather',
    'get_stock_price',
    'search_wikipedia',
    'get_definition',
    'is_website_down',
    'search_reddit_opinions'
]


# Quick test
if __name__ == "__main__":
    print("Testing Live Tools...\n")
    
    # Test weather
    print("1. Weather:")
    print(get_weather.invoke({"city": "Windsor"}))
    print()
    
    # Test stock
    print("2. Stock Price:")
    print(get_stock_price.invoke({"ticker": "AAPL"}))
    print()
    
    # Test Wikipedia
    print("3. Wikipedia:")
    result = search_wikipedia.invoke({"query": "Python programming"})
    print(result[:200] + "..." if len(result) > 200 else result)
    print()
    
    # Test definition
    print("4. Definition:")
    print(get_definition.invoke({"word": "ephemeral"}))
    print()
    
    # Test website
    print("5. Website Status:")
    print(is_website_down.invoke({"url": "google.com"}))
    print()
    
    print("✅ All tools tested!")
