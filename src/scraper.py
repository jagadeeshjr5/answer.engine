from googlesearch import search
import re
import aiohttp
import asyncio
import time
from bs4 import BeautifulSoup
 
 
async def fetch_page(session, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(url, headers=headers, ssl=False) as response:
            if response.status == 403:
                print(f"Access Forbidden for URL: {url}")
                return None
            if response.status == 429:
                print(f"Rate limit exceeded for URL: {url}. Retrying...")
                await asyncio.sleep(5)  # Retry delay
                return await fetch_page(session, url)
            html_content = await response.text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
    except Exception as e:
        print(f"An error occurred while fetching {url}: {e}")
        return None

async def scrape(query, num_urls):
    urls = []
    try:
        results = search(query, num_results=num_urls, lang="en")
        urls.extend(results)
    except Exception as e:
        print(f"An error occurred during search: {e}")

    scraped_content = ''
    if urls:
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_page(session, url) for url in urls]
            htmls = await asyncio.gather(*tasks)
    
        for url, soup in zip(urls, htmls):
            if soup:
                text_content = soup.get_text()
                scraped_content += text_content

        # Clean up the scraped content
        scraped_content = re.sub(r'\s{2,}', ' ', re.sub(r'\n+', '\n', str(scraped_content)))

        return scraped_content, urls
    else:
        return scraped_content, urls