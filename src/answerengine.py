import streamlit as st
from context import make_context
from model import Model, get_models
import time
from scraper import WebScraper

from cache_utils import fetch_urls_from_dynamodb, fetch_content_from_dynamodb, run_writecache_script

import os

import boto3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import concurrent.futures

from typing import List

table_name = 'adote-webdoccache' #os.environ["TABLE_NAME"] if "TABLE_NAME" in os.environ else st.secrets["TABLE_NAME"]
api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]

# Initialize the WebScraper in session state if it doesn't already exist
scraper = WebScraper()

num_urls = 1
context_percentage = 0.75
enable_history = False

selected_model = 'gemini-1.5-flash'

def run_scraper(urls : List):
    local_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    #local_driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=chrome_options)
    try:
        # Use the scraper from session state
        scraped_content = scraper.scrape_content(urls, driver=local_driver)
    finally:
        local_driver.quit()
    return scraped_content

def process_query(prompt, model, history):
    model = Model(operation='search', model=model, api_key=api_key1)
    
    search_query = model.search(query=prompt, history=history, enable_history=enable_history)
    
    return search_query

def run_scraper_conc(urls : List):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_scraper, urls)
        scraped_content = future.result()
            
    #chunks = create_chunks(scraped_content)

    return scraped_content

def prepare_context(prompt, chunks, context_percentage=context_percentage):
    context = make_context(query=prompt, context=chunks, context_percentage=context_percentage)
    return context


def main(urls, table_name):
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    #table_name = 'adote-webdoccache'
    table = dynamodb.Table(table_name)

    # Fetch cached URLs
    cached_urls = fetch_urls_from_dynamodb(table)

    data_to_insert = {}
    fetch_from_cache = []
    scrape_url = []

    output = []
    print("Urls: ", urls)

    for url in set(urls):
        if not url.endswith(".pdf"):
            if url in cached_urls:
                fetch_from_cache.append(url)
            else:
                scrape_url.append(url)

    if fetch_from_cache:
        print("cached_urls: ", fetch_from_cache)
        fetched_content = fetch_content_from_dynamodb(table, fetch_from_cache)
        output.append(fetched_content)
        print("Data fetched from cache")

    if scrape_url:
        print("scrape_urls: ", scrape_url)
        scraped_content = run_scraper_conc(scrape_url)
        data_to_insert = {k: '\n'.join(set(v.split('\n'))) for d in scraped_content for k, v in d.items()}
        output.append(data_to_insert)
        print("Scraped content")

    # Insert all new items into the cache at once
    if data_to_insert:
        run_writecache_script(table_name, data_to_insert, api_key)
        print('Writing to cache')

    return [item for sublist in output for item in (sublist if isinstance(sublist, list) else sublist.values())]


# Set up Selenium Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--log-level=3")


api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = os.environ["API_KEY1"] if "API_KEY1" in os.environ else st.secrets["API_KEY1"]
api_key2 = os.environ["API_KEY2"] if "API_KEY2" in os.environ else st.secrets["API_KEY2"]
api_key3 = os.environ["API_KEY3"] if "API_KEY3" in os.environ else st.secrets["API_KEY3"]


models = get_models()
default_model = 'gemini-1.5-flash'
default_index = models.index(default_model)

history = []


if __name__ == "__main__":
    if prompt := input("Ask me!"):
        try:
            start_time = time.time()
                
            search_query = process_query(prompt, model=selected_model, history=history)

            urls = scraper.google_search(search_query, 2)

            #scrped_content = run_scraper_conc(urls)

            #context = prepare_context(search_query, chunks, context_percentage=context_percentage)

            context = main(urls, table_name)

            context = '\n'.join(context)
            
            model = Model(operation='answer', model=selected_model, api_key=api_key2)

            end_time = time.time()
            runtime = end_time - start_time

            print(f"{runtime:.2f} seconds")
            output = model.answer(query=prompt, context=context)
            for i in output:
                print(i)
            
        except Exception as e:
            print(e)
