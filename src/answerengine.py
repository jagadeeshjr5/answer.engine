import asyncio
from scraper import scrape
from utils import create_chunks, make_context
from model import Model
import time

async def run_scraper(query, num_urls):
    scraped_content, urls = await scrape(query, num_urls)
    return scraped_content, urls

async def main():
    model = Model(operation='search')
    prompt = input("Ask me! : ")
    num_urls = 3
    context_percentage = 0.5
    start_time = time.time()

    try:
        for _ in range(3):
            search_query = model.search(query=prompt)
            print(search_query)     
            scraped_content, urls = await run_scraper(search_query, num_urls)
            if scraped_content.strip():
                break
        chunks = create_chunks(scraped_content)
        context = await make_context(query=prompt, context=chunks, context_percentage=context_percentage)
        end_time = time.time()
        runtime = end_time - start_time
        
        model = Model(operation='answer')
        for token in model.answer(query=prompt, context=context):
            print(token, end='')
        #print(answer)
    except Exception as e:
        #print(e)
        pass

if __name__ == "__main__":
    asyncio.run(main())
