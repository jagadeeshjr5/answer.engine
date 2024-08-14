from playwright.async_api import async_playwright
from googlesearch import search
import re
import asyncio
import time
import html
import requests
from bs4 import BeautifulSoup
import concurrent.futures


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

async def handle_request(route):
    if route.request.resource_type in ["image", "stylesheet", "font", "style"]:
        await route.abort()  # Abort image, stylesheet, and font requests to speed up loading
    else:
        await route.continue_()

async def fetch_page_text_playwright(browser, context, url):
    page = await context.new_page()
    await page.route("**/*", handle_request)
    try:
        await page.goto(url, timeout=10000, wait_until="domcontentloaded")
        try:
            full_text = await page.locator('body').inner_text()
        except:
            full_text = await page.locator('body#app').inner_text()
    except Exception as e:
        full_text = ''
    finally:
        await page.close()
        
    return full_text

def fetch_page_text_requests(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page {url}: {e}")
        return ''

async def fetch_all_pages(urls):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, chromium_sandbox=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        tasks = []
        for url in urls:
            if url.lower().endswith(('.html', '.htm')):
                tasks.append(asyncio.to_thread(fetch_page_text_requests, url))
            elif not url.lower().endswith('.pdf'):
                tasks.append(fetch_page_text_playwright(browser, context, url))
        
        results = await asyncio.gather(*tasks)
        await context.close()
        await browser.close()
        
    results = '\n'.join(results)
    return results

async def scrape(query, num_urls):
    start_time = time.time()
    urls = []
    
    try:
        results = search(query, num_results=num_urls, lang="en")  # Assuming you have a search function defined elsewhere
    except Exception as e:
        print(e)
        
    if results:
        urls.extend(results)
    
    scraped_content = await fetch_all_pages(urls)

    scraped_content = clean_web_data(scraped_content)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} sec")

    if scraped_content:
        return scraped_content, urls
    else:
        return '', urls