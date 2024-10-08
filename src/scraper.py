from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from googlesearch import search
import concurrent.futures

from typing import List, Tuple
from selenium.webdriver.chrome.webdriver import WebDriver
import threading

class WebScraper():
    _instance = None  # Class-level attribute to store the single instance
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WebScraper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, retries : int = 1, delay : int = 2):

        """
        Initialize the WebScraper with the specified number of retries and delay between requests.

        Args:
            retries (int): Number of retries for loading a page.
            delay (int): Delay in seconds between retries.
        """

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        #chrome_options.binary_location = "/usr/bin/google-chrome"
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--log-level=3")

        self.delay = delay
        self.retries = retries
        
        self.contents = []
        self.lock = threading.Lock()
        
        #self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
  
    def quit_driver(self):
        """Quit the Selenium WebDriver instance."""
        self.driver.quit()
    
    def load_page_with_retries(self, url : str, driver : WebDriver):
        """

        Load a page with retries and wait until it's fully loaded.

        Args:
            url (str): The URL to load.
            driver (WebDriver): The Selenium WebDriver instance.

        Returns:
            str: The page source if loaded successfully, else None.

        """
        for _ in range(self.retries):
            try:
                driver.get(url)
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                return driver.page_source
            except Exception as e:
                #print(f"Attempt {attempt + 1} failed for {url}: {e}")
                time.sleep(self.delay)
            
        #print(f"Failed to load {url} after {self.retries} retries.")
        return None
        
    def scrape_url(self, url : str, driver : WebDriver):
        """

        Scrape the content from a URL.

        Args:
            url (str): The URL to scrape.
            driver (WebDriver): The Selenium WebDriver instance.

        Returns:
            str: The scraped content from the URL.

        """
        self.contents = []
        if url.endswith(".pdf"):
            #print(f"Skipping PDF: {url}")
            return None
    
        html = self.load_page_with_retries(url, driver)
        content = ''
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'meta', 'noscript']):
                tag.decompose()
            content = '\n'.join(tag.get_text(strip=True) for tag in soup.find_all(True))

        with self.lock:
            if content:  # Only add if content is not empty
                self.contents.append({url: content})
    
        #return content
        
    def scrape_multiple_urls(self, urls : List, driver : WebDriver) -> List:
        """

        Scrape multiple URLs concurrently using threads.

        Args:
            urls (List[str]): List of URLs to scrape.
            driver (WebDriver): The Selenium WebDriver instance.

        Returns:
            List[dict]: List of dictionaries containing scraped content indexed by URL.

        """
        
        #results = []
        #for url in urls:
        #    content = self.scrape_url(url, driver)
        #    results.append(content)

        threads = []
    
        # Create and start a thread for each URL
        for url in urls:
            thread = threading.Thread(target=self.scrape_url, args=(url, driver))
            threads.append(thread)
            thread.start()
    
        # Wait for all threads to finish
        for thread in threads:
            thread.join()
 
        return self.contents

    def fetch_search_results(self, query : str, num_results : int, lang : str) -> Tuple[str, List[str]]:
        """

        Fetch search results for a given query.

        Args:
            query (str): The search query.
            num_results (int): The number of search results to fetch.
            lang (str): The language for search results.

        Returns:
            Tuple[str, List[str]]: The query and list of URLs from search results.

        """
        urls = []
        try:
            results = search(query, num_results=num_results, lang=lang)
            urls.extend(results)
        except Exception as e:
            pass
            #print(f"An error occurred during search for query '{query}': {e}")
        return query, urls
        
    def google_search(self, queries : List, num_results : int, lang='en') -> List:
        """

        Perform Google searches for multiple queries concurrently.

        Args:
            queries (List[str]): List of search queries.
            num_results (int): Number of results per query.
            lang (str): Language for search results.

        Returns:
            List[str]: List of URLs from the search results.

        """
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.fetch_search_results, query, num_results, lang='en'): query for query in queries}
            for future in concurrent.futures.as_completed(futures):
                query = futures[future]
                try:
                    result = future.result()  # Remove 'await' because it doesn't work with ThreadPoolExecutor
                    results.append(result)
                except Exception as e:
                    pass
                    #print(f"Error processing query '{query}': {e}")
        urls = [url for query, url_list in results for url in url_list]
        return urls
        
    def scrape_content(self, urls : List, driver : WebDriver) -> Tuple[str, List[str]]:
        """

        Scrape content from a list of URLs.

        Args:
            urls (List[str]): List of URLs to scrape.
            driver (WebDriver): The Selenium WebDriver instance.

        Returns:
            List[dict]: List of dictionaries containing scraped content indexed by URL.

        """
        if not isinstance(urls, List):
            raise TypeError(f"Expected List, got {type(urls).__name__}")
        
        #start_time = time.time()
        #urls = self.google_search(queries, num_urls)  # Pass driver if needed
        #print(f"Scraping the following URLs: {urls}")

        scraped_content = self.scrape_multiple_urls(urls, driver)

        #scraped_content = '\n\n'.join(scraped_content[0].values())
        #scraped_content = [text for text in scraped_content if text is not None]
        #scraped_content = '\n'.join(scraped_content)
        #end_time = time.time()
        #print(end_time - start_time)

        return scraped_content

#if __name__ == "__main__":
#    c1 = Scraper()
#    queries = ["who is the PM of India"]
#    content, urls = c1.scrape_content(queries, 1)
#    #print(content[0:1000])