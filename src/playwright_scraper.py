from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import itertools
import concurrent.futures

# Set up Selenium Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.binary_location = "/usr/bin/google-chrome" 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--log-level=3")

# Global variable to hold the ChromeDriver instance
driver = None

def init_driver():
    global driver
    if driver is None:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=chrome_options)

def quit_driver():
    global driver
    if driver is not None:
        driver.quit()
        driver = None

def load_page_with_retries(url, driver, retries=3, delay=5):  # Add driver as a parameter
    for attempt in range(retries):
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            return driver.page_source
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay)
    print(f"Failed to load {url} after {retries} retries.")
    return None

def scrape_url(url, driver):
    if url.endswith(".pdf"):
        print(f"Skipping PDF: {url}")
        return None

    html = load_page_with_retries(url, driver)  # Ensure you pass the driver
    content = ''
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(['nav', 'header', 'footer', 'aside', 'script', 'style', 'meta', 'noscript']):
            tag.decompose()
        content = '\n'.join(tag.get_text(strip=True) for tag in soup.find_all(True))

    return content

def scrape_in_parallel(urls, driver):
    results = []
    for url in urls:
        content = scrape_url(url, driver)  # Pass the driver to scrape_url
        results.append(content)
    return results

def fetch_search_results(query, num_results, lang):
    from googlesearch import search
    urls = []
    try:
        results = search(query, num_results=num_results, lang=lang)
        urls.extend(results)
    except Exception as e:
        print(f"An error occurred during search for query '{query}': {e}")
    return query, urls

def google_search(queries, num_results, lang):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(fetch_search_results, query, num_results, lang): query for query in queries}
        for future in concurrent.futures.as_completed(futures):
            query = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing query '{query}': {e}")
    urls = [url for query, url_list in results for url in url_list]
    return urls

def scrape_content(query, num_urls, driver):
    urls = google_search(query, num_results=num_urls, lang="en")  # Pass driver if needed
    print(f"Scraping the following URLs: {urls}")
    scraped_content = scrape_in_parallel(urls, driver)  # Pass driver to the scraping function
    scraped_content = [text for text in scraped_content if text is not None]
    scraped_content = '\n'.join(scraped_content)
    #scraped_content = '\n'.join(list(set(scraped_content.split('\n'))))
    #scraped_content = [text for text in scraped_content if text is not None]
    return scraped_content, urls

def scrape_all_queries(queries, num_urls, driver):
    start_time = time.time()
   
    content, urls = scrape_content(queries, num_urls, driver)  # Pass the driver to scrape_content
    
    end_time = time.time()
    print(end_time - start_time)
    
    return content, urls

# Example usage
#queries = ["PM of India"]
#content, urls = scrape_all_queries(queries, 1)
#print(urls)
