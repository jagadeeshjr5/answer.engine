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
        async with session.get(url, headers=headers) as response:
            html_content = await response.text(encoding='utf-8', errors='ignore')
            html_content = await response.text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
    except:
        pass
 
 
async def scrape(query, num_urls):

    #start_time = time.time()
    urls = []
    query = query
    try:
        results = search(query, num_results=num_urls, lang="en")
    except Exception as e:
        print(e)
    scraped_content = ''
    if results:
        urls.extend(results)
        async with aiohttp.ClientSession() as session:
            
    
            tasks = []
    
            for url in urls:
                tasks.append(fetch_page(session, url)) 
    
            htmls = await asyncio.gather(*tasks)
    
    
        for url, soup in zip(urls, htmls):
            try:
                #tags = soup.find_all(lambda tag: tag.name in ['p', 'title', 'div'] and tag.string)
                tags = soup.get_text()

                #for tag in tags:
                #    scraped_content = scraped_content + tag.get_text()
                scraped_content = scraped_content + tags
            except:
                pass

        
        scraped_content = re.sub(r'\s{2,}', ' ', re.sub(r'\n+', '\n', scraped_content))
        #end_time = time.time()
        #print(f"Time taken: {end_time - start_time} seconds")

        return scraped_content, urls
    else:
        return scraped_content, urls
