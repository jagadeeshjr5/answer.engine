from playwright.async_api import async_playwright
from googlesearch import search
import re
import asyncio
import time
import html

def clean_web_data(raw_data):
    decoded_data = html.unescape(raw_data)

    # Remove binary data and non-UTF characters
    cleaned_data = re.sub(r'[^\x00-\x7F]+', ' ', decoded_data)
    
    # Replace multiple spaces, newlines, and tabs with a single space
    cleaned_data = re.sub(r'\s+', ' ', cleaned_data)

    # Remove common web-related text patterns (like "Terms of Use", etc.)
    patterns_to_remove = [
        r'Terms of Use', r'Privacy Statement', r'Report Vulnerability', 
        r'Contact Us', r'Feedback', r'Created with Built by .*', r'Last Updated .*'
    ]
    for pattern in patterns_to_remove:
        cleaned_data = re.sub(pattern, '', cleaned_data, flags=re.IGNORECASE)

    # Remove leftover PDF-related garbage text
    cleaned_data = re.sub(r'%PDF-[\d\.]+', '', cleaned_data)
    cleaned_data = re.sub(r'endstream endobj', '', cleaned_data, flags=re.IGNORECASE)

    # Remove any remaining excessive special characters
    cleaned_data = re.sub(r'[^\w\s,.?!\-]', '', cleaned_data)

    # Strip leading and trailing spaces
    cleaned_data = cleaned_data.strip()

    cleaned_data = re.sub(r'\s{2,}', ' ', re.sub(r'\n+', '\n', str(cleaned_data)))

    return cleaned_data

async def fetch_page_text(url):
    #start_time = time.time()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        page = await context.new_page()
        try:
            # Navigate quickly with a short timeout and wait until "domcontentloaded"
            await page.goto(url, timeout=10000, wait_until="domcontentloaded")
            try:
                full_text = await page.locator('body').inner_text()
            except:
                full_text = await page.locator('body#app').inner_text()
        except Exception as e:
            full_text = ''
        finally:
            await page.close()
            await context.close()
            await browser.close()
        #end_time = time.time()
        #print(f"Time taken: {end_time - start_time} seconds")
        
        return full_text

async def fetch_all_pages(urls):
    tasks = [fetch_page_text(url) for url in urls]
    results = await asyncio.gather(*tasks)
    results = '\n'.join(results)
    return results

async def scrape(query, num_urls):
    urls = []
    
    try:
        results = search(query, num_results=num_urls, lang="en")  # Assuming you have a search function defined elsewhere
    except Exception as e:
        #print(e)
        pass
    
    if results:
        urls.extend(results)
    
    scraped_content = await fetch_all_pages(urls)

    if scraped_content:
    
        return scraped_content, urls
    else:
        return '', urls
