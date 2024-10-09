from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from googlesearch import search
import concurrent.futures

from typing import List, Tuple
from selenium.webdriver.chrome.webdriver import WebDriver
from threading import Lock
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

class WebScraper():    
    def __init__(self, retries: int = 1, delay: int = 2):
        self.retries = retries
        self.delay = delay
        self.contents = Queue()
        self.lock = Lock()
        self.driver = self.get_driver()  # Initialize driver once
    
    def get_driver(self) -> WebDriver:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--log-level=3")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), 
            options=chrome_options
        )
        return driver

    def quit_driver(self):
        self.driver.quit()
    
    def load_page_with_retries(self, url: str) -> str:
        for _ in range(self.retries):
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                return self.driver.page_source
            except Exception as e:
                time.sleep(self.delay)
        return None
        
    def scrape_url(self, url: str):
        if url.endswith(".pdf"):
            return None

        html = self.load_page_with_retries(url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'meta', 'noscript']):
                tag.decompose()
            content = '\n'.join(tag.get_text(strip=True) for tag in soup.find_all(True))
            
            if content:
                self.contents.put({url: content})  # Use thread-safe queue

    def scrape_multiple_urls(self, urls: List[str]) -> List:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.scrape_url, urls)

        scraped_data = []
        while not self.contents.empty():
            scraped_data.append(self.contents.get())
        return scraped_data

    def fetch_search_results(self, query: str, num_results: int, lang: str) -> Tuple[str, List[str]]:
        urls = []
        try:
            results = search(query, num_results=num_results, lang=lang)
            urls.extend(results)
        except Exception as e:
            pass
        return query, urls
        
    def google_search(self, queries: List[str], num_results: int, lang='en') -> List:
        results = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.fetch_search_results, query, num_results, lang): query for query in queries}
            for future in concurrent.futures.as_completed(futures):
                query = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    pass
        return [url for _, urls in results for url in urls]
        
    def scrape_content(self, urls: List[str]) -> List[dict]:
        start_time = time.time()
        scraped_content = self.scrape_multiple_urls(urls)
        end_time = time.time()
        print(f"Scraping completed in {end_time - start_time:.2f} seconds.")
        return scraped_content


#if __name__ == "__main__":
#    c1 = WebScraper()
#    urls = [
#        "https://www.reuters.com/world/india/indias-lok-sabha-election-2024-main-political-parties-candidates-2024-04-19/", 
#        "https://www.aljazeera.com/news/2024/5/6/india-lok-sabha-election-2024-phase-3-who-votes-and-whats-at-stake", 
#        "https://www.aljazeera.com/news/2024/5/19/india-lok-sabha-election-2024-phase-5-who-votes-and-whats-at-stake", 
#        "https://apnews.com/article/india-election-modi-bjp-democracy-8998fe6aba5fa26debc0f82c4e2ccf69"
#    ]
#    content = c1.scrape_content(urls)
#    print(content[:1])  # Print a preview of the first result
