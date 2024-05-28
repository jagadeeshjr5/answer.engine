import asyncio
from scraper import scrape  # Import your scraper function
from utils import create_chunks, get_embeddings, make_context, Model

import time

async def run_scraper(query, num_urls):
    scraped_content, urls = await scrape(query, num_urls)
    return scraped_content, urls



try:
    prompt  = str(input("Ask me! : "))
    num_urls = 5
    context_percentage = 0.5
    start_time = time.time()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    scraped_content, urls = loop.run_until_complete(run_scraper(prompt, num_urls))

    chunks = create_chunks(scraped_content)
    context = make_context(query=prompt, context=chunks, context_percentage=context_percentage)
    end_time = time.time()  # Record end time
    runtime = end_time - start_time
    print(f"Time taken to retreive the context: {runtime:.2f} seconds")
    model = Model()
    output = model.answer(query=prompt, context=context)
    print(output)

except Exception as e:

    print(Exception)





