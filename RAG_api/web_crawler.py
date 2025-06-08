import httpx
from bs4 import BeautifulSoup
from typing import Set

async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"}
        response = await client.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_links(base_url: str, html: str) -> Set[str]:
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
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

async def crawl_all_pages(url: str) -> dict:
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

    return pages_content



async def crawl_webpage(url: str) -> dict:
    print(f"Starting to crawl: {url}")
    async with httpx.AsyncClient(follow_redirects=True) as client:  # <-- fix here
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; MyCrawler/1.0)"}
            response = await client.get(url, timeout=10, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print(f"Request error occurred while fetching {url}: {e}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        content = soup.get_text(separator="\n", strip=True)
        print(f"content to crawl: {content[:200]}...")  # limit log size
    return {url: content}

