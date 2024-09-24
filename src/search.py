import asyncio
import aiohttp
from googlesearch import search
from time import time

async def fetch_search_results(query, num_results, lang):
    urls = []
    try:
        results = search(query, num_results=num_results, lang=lang)
        urls.extend(results)
    except Exception as e:
        print(f"An error occurred during search for query '{query}': {e}")
    return query, urls

async def google_search(queries, num_results, lang):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_search_results(query, num_results, lang) for query in queries]
        results = await asyncio.gather(*tasks)

        urls = [url for query, url in results]
    return urls