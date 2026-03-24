"""
web_crawler_service.py

Web crawling service for extracting content from URLs.
Handles async HTTP requests and HTML content extraction.
"""

import httpx
import logging
from bs4 import BeautifulSoup
from typing import Set, Dict
from config.settings import settings

logger = logging.getLogger(__name__)


async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    """
    Fetch HTML content from a URL using async HTTP client.
    
    Args:
        client: Async HTTP client
        url: URL to fetch
        
    Returns:
        str: HTML content or empty string on error
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"}
        response = await client.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""


def extract_links(base_url: str, html: str) -> Set[str]:
    """
    Extract all links from HTML content.
    
    Args:
        base_url: Base URL for resolving relative links
        html: HTML content to parse
        
    Returns:
        Set[str]: Set of absolute URLs
    """
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            links.add(href)
        elif href.startswith("/"):
            links.add(base_url.rstrip("/") + href)
    return links


def extract_text(html: str) -> str:
    """
    Extract clean text content from HTML.
    
    Args:
        html: HTML content to parse
        
    Returns:
        str: Clean text content
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


async def crawl_all_pages(url: str) -> Dict[str, str]:
    """
    Crawl a webpage and all linked pages from the same domain.
    
    Args:
        url: Starting URL to crawl
        
    Returns:
        Dict[str, str]: Mapping of URLs to their text content
    """
    logger.info(f"Starting comprehensive crawl of: {url}")
    base_url = url.rstrip("/")
    async with httpx.AsyncClient() as client:
        main_html = await fetch_html(client, url)
        if not main_html:
            return {}

        pages_content = {base_url: extract_text(main_html)}
        links = extract_links(base_url, main_html)

        for link in links:
            html = await fetch_html(client, link)
            if html:
                pages_content[link] = extract_text(html)

    logger.info(f"✅ Crawled {len(pages_content)} pages successfully")
    return pages_content


async def crawl_webpage(url: str) -> Dict[str, str]:
    """
    Crawl a single webpage and extract its content.
    
    Args:
        url: URL to crawl
        
    Returns:
        Dict[str, str]: Mapping of URL to its text content
    """
    logger.info(f"Starting to crawl: {url}")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"}
            response = await client.get(url, timeout=10, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Request error occurred while fetching {url}: {e}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        content = soup.get_text(separator="\n", strip=True)
        logger.info(f"Extracted content ({len(content)} chars): {content[:200]}...")
        
    return {url: content}