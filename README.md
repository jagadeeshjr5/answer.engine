# answer.engine (answer dot engine)

**answer.engine** is an AI powered answer engine which answers users query by crawling through web in real time. It works in a series fashion by executing one component at a time.

**Key components:**
1. Search engine.
2. Web scraper.
3. Chunking & embedding.
4. Language model.

**1. Search engine:** The search engine component of answer.engine crawls through the web to find and rank the web pages that match the user's query. We are using Google Search to get the most relevant URLs.

**2. Web scraper:** The Web scraper then takes the URLs from the search engine and scrape the contents of the website
