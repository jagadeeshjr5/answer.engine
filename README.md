# answer.engine (answer dot engine)

**answer.engine** is an AI powered answer engine which answers users query by crawling through web in real time. It works in a series fashion by executing one component at a time.

**Key components:**
1. Search engine.
2. Web scraper.
3. Chunking & embedding.
4. Language model.

**Things happening under the hood**

The search engine component of answer.engine crawls through the web to find and rank the web pages that match the user's query. We are using Google Search to get the most relevant URLs. The web scraper then takes these URLs and scrapes the contents of the websites asynchronously. The scraped raw text is often noisy and might contain junk data. To remove this junk data and pass the relevant content to the language model, we chunk the text with some overlap and create embeddings of each chunk. We then use these embeddings to calculate the cosine similarity and get the most relevant chunks for the user's query. Finally, we pass only a certain number of top N chunks as context to the language model, which uses that context to answer the user's query. Chunking and embedding also help reduce the input prompt tokens, which enhances the input prompt cost-efficiency.

**How to use this**

**streamlit app:** 

[![GitHub](https://drive.google.com/uc?export=view&id=1KDxCwWOzvi7JftyOd1LWHhFFtzgNbVhO)](https://github.com/jagadeeshjr5)
