from googlesearch import search
import re
import aiohttp
import asyncio
import time
from bs4 import BeautifulSoup
 
 
async def fetch_page(session, url): 
    try:
        async with session.get(url) as response:
            html_content = await response.text(encoding='utf-8', errors='ignore')
            html_content = await response.text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
    except:
        pass
 
 
async def scrape(query, num_urls):

    start_time = time.time()
    urls = []
    query = query
    results = search(query, num_results=num_urls, lang="en")
    for url in results:
        urls.append(url)
 
    async with aiohttp.ClientSession() as session:
        scraped_content = ''
 
        tasks = []
 
        for url in urls:
            tasks.append(fetch_page(session, url)) 
 
        htmls = await asyncio.gather(*tasks)
 
 
    for url, soup in zip(urls, htmls):
        keywords = ['weather', 'India']
        try:
            #tags_with_keywords = soup.find_all(lambda tag: tag.name in ['p', 'title', 'div'] and tag.string)
            tags_with_keywords = soup.get_text()

            #for tag in tags_with_keywords:
             #   scraped = scraped + tag.get_text()
            scraped_content = scraped_content + tags_with_keywords
        except:
            pass

    
    scraped_content = re.sub(r'\s{2,}', ' ', re.sub(r'\n+', '\n', scraped_content))
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")

    return scraped_content, urls
