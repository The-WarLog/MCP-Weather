#!/usr/bin/env python3
"""
Search service using web scraping (no API keys required)
"""

import asyncio
import logging
import urllib.parse
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from models import SearchResult, SearchResponse, validate_search_query, sanitize_text

logger = logging.getLogger("puch.search")

class SearchService:
    def __init__(self, user_agent: str, timeout: int = 10):
        self.user_agent = user_agent
        self.timeout = timeout
        self.base_url = "https://www.google.com/search"
        
    async def search_google(self, query: str, num_results: int = 5) -> SearchResponse:
        """Perform Google search without API keys"""
        logger.info("Performing Google search", extra={"query": query[:50]})
        
        # Validate input
        validation_error = validate_search_query(query)
        if validation_error:
            logger.warning("Invalid search query", extra={"error": validation_error})
            return SearchResponse(
                ok=False,
                error="validation",
                detail=validation_error
            )
        
        # Sanitize and prepare query
        clean_query = sanitize_text(query.strip())
        num_results = min(max(1, num_results), 10)  # Clamp between 1-10
        
        try:
            results = await self._scrape_search_results(clean_query, num_results)
            
            # If no results found, provide fallback
            if not results:
                logger.info("No search results found, providing fallback results")
                results = [
                    SearchResult(
                        title=f"Search for '{clean_query}' - Limited Results",
                        snippet="Google search scraping is currently limited. For detailed information about this topic, try using the chat feature to ask the AI assistant.",
                        url="https://www.google.com/search?q=" + urllib.parse.quote(clean_query)
                    ),
                    SearchResult(
                        title=f"AI Alternative: Ask about '{clean_query}'",
                        snippet="The AI chat feature can provide comprehensive information about your search topic with detailed explanations and current knowledge.",
                        url="https://www.google.com"
                    )
                ]
            
            return SearchResponse(
                ok=True,
                results=results,
                query=clean_query
            )
            
        except Exception as e:
            logger.error("Error performing search", exc_info=True)
            
            # Fallback: provide mock results when scraping fails
            logger.info("Providing fallback search results due to scraping failure")
            fallback_results = [
                SearchResult(
                    title=f"Search results for '{clean_query}' - Scraping Limited",
                    snippet="Google search scraping is currently limited. This is a fallback result. For real-time search, consider using the chat feature to ask about your topic.",
                    url="https://www.google.com/search?q=" + urllib.parse.quote(clean_query)
                ),
                SearchResult(
                    title=f"Alternative: Ask the AI about '{clean_query}'",
                    snippet="You can use the chat feature to ask the AI assistant about your search topic for detailed information.",
                    url="https://www.google.com"
                )
            ]
            
            return SearchResponse(
                ok=True,
                results=fallback_results,
                query=clean_query
            )
    
    async def _scrape_search_results(self, query: str, num_results: int) -> List[SearchResult]:
        """Scrape Google search results"""
        params = {
            'q': query,
            'num': num_results,
            'hl': 'en'
        }
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Add a small delay to be respectful
            await asyncio.sleep(0.5)
            
            response = await client.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            
            return self._parse_search_page(response.text)
    
    def _parse_search_page(self, html: str) -> List[SearchResult]:
        """Parse Google search results from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Try multiple selectors as Google changes their HTML structure frequently
        search_selectors = [
            'div.g',  # Traditional selector
            'div[data-sokoban-container]',  # Alternative selector
            'div.tF2Cxc',  # Another common selector
            'div.MjjYud'  # Yet another selector
        ]
        
        search_results = []
        for selector in search_selectors:
            search_results = soup.select(selector)
            if search_results:
                logger.info(f"Found {len(search_results)} results using selector: {selector}")
                break
        
        if not search_results:
            # Fallback: look for any div with an h3 and a link
            logger.warning("Standard selectors failed, trying fallback approach")
            all_h3s = soup.find_all('h3')
            for h3 in all_h3s:
                parent = h3.parent
                while parent and parent.name != 'div':
                    parent = parent.parent
                if parent:
                    search_results.append(parent)
        
        for result in search_results:
            try:
                # Extract title - try multiple approaches
                title_elem = result.find('h3')
                if not title_elem:
                    # Try alternative selectors
                    title_elem = result.select_one('h3, .LC20lb, .DKV0Md')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract URL - try multiple approaches
                link_elem = result.find('a')
                if not link_elem:
                    link_elem = result.select_one('a[href]')
                
                if not link_elem or not link_elem.get('href'):
                    continue
                    
                url = link_elem['href']
                
                # Clean up URL if it's a Google redirect
                if url.startswith('/url?q='):
                    url = urllib.parse.unquote(url.split('/url?q=')[1].split('&')[0])
                elif url.startswith('/search?'):
                    continue  # Skip internal Google search links
                
                # Extract snippet - try multiple selectors
                snippet_selectors = [
                    '.aCOpRe', '.VwiC3b', '.s3v9rd', '.st', '.IsZvec'
                ]
                snippet = ""
                for selector in snippet_selectors:
                    snippet_elem = result.select_one(selector)
                    if snippet_elem:
                        snippet = snippet_elem.get_text(strip=True)
                        break
                
                # Validate URL
                if not url.startswith(('http://', 'https://')):
                    continue
                
                if title and url:
                    results.append(SearchResult(
                        title=sanitize_text(title),
                        snippet=sanitize_text(snippet) if snippet else "No description available",
                        url=url
                    ))
                    
            except Exception as e:
                logger.warning(f"Error parsing search result: {e}")
                continue
        
        logger.info(f"Parsed {len(results)} search results")
        return results