import re
import aiohttp
import asyncio
import time
from bs4 import BeautifulSoup
import itertools

from pdfparser import process_pdf_url

import re
import html

from search import google_search

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
 
 
async def parse_pdf(url):
    # Assuming process_pdf_url is defined to handle PDF parsing
    pdf_text = await process_pdf_url(url)
    return pdf_text

async def fetch_page(session, url, retries=0):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries + 1):  # Allow retries
        try:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status == 403:
                    return None  # Forbidden access

                # Check if the URL ends with .pdf
                if url.lower().endswith('.pdf'):
                    return await parse_pdf(url)  # Call the PDF parser function

                # Get HTML content
                html_content = await response.text(encoding='utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup

        except Exception as e:
            pass

async def scrape(query, num_urls):
    try:
        urls = await google_search(query, num_results=num_urls, lang="en")
        urls = list(set(list(itertools.chain(*urls))))
        print(urls)
    except Exception as e:
        print(f"An error occurred during search: {e}")

    scraped_content = ''
    if urls:
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_page(session, url) for url in urls]
            contents = await asyncio.gather(*tasks)
    
        for url, content in zip(urls, contents):
            if content:
                if isinstance(content, str):
                    scraped_content += content
                    #print(content)
                else:
                    text_content = content.get_text()
                    scraped_content += text_content

        scraped_content = clean_web_data(scraped_content)

    return scraped_content, urls