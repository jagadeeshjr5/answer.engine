import streamlit as st
import asyncio
from utils import create_chunks, make_context, load_urls
from model import Model, get_models
import time
import nest_asyncio
from scraper import WebScraper

import os

from utils import youtube_search

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.support.ui import WebDriverWait
import time
import concurrent.futures

# Initialize the WebScraper in session state if it doesn't already exist
scraper = WebScraper()

num_urls = 1
context_percentage = 0.75
enable_history = False

selected_model = 'gemini-1.5-flash'

def run_scraper(query, num_urls):
    local_driver = webdriver.Chrome(service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=chrome_options)
    #local_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        # Use the scraper from session state
        scraped_content, urls = scraper.scrape_content(query, num_urls, driver=local_driver)
    finally:
        local_driver.quit()
    return scraped_content, urls

def process_query(prompt, model, history):
    model = Model(operation='search', model=model, api_key=api_key1)
    
    search_query = model.search(query=prompt, history=history, enable_history=enable_history)
    
    return search_query

def run_scraper_conc(search_query, num_urls):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_scraper, search_query, num_urls)
        scraped_content, urls = future.result()
            
    chunks = create_chunks(scraped_content)

    return chunks, urls

def prepare_context(prompt, chunks, context_percentage=context_percentage):
    context = make_context(query=prompt, context=chunks, context_percentage=context_percentage)
    return context

# Set up Selenium Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--log-level=3")

nest_asyncio.apply()

api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = os.environ["API_KEY1"] if "API_KEY1" in os.environ else st.secrets["API_KEY1"]
api_key2 = os.environ["API_KEY2"] if "API_KEY2" in os.environ else st.secrets["API_KEY2"]
api_key3 = os.environ["API_KEY3"] if "API_KEY3" in os.environ else st.secrets["API_KEY3"]

urls = load_urls(r'src/urls.txt')

models = get_models()
default_model = 'gemini-1.5-flash'
default_index = models.index(default_model)


if __name__ == "__main__":
    st.set_page_config(
            page_title="answer.engine", page_icon=f"{urls['pageicon']}")

    answer_color = "#c32148"

    st.markdown(f"<h1><span style='color:{answer_color};'>a</span>.E</h1>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    history = []

    for message in st.session_state.messages:
        if message['role'] in ['user', 'assistant']:
            with st.chat_message(message["role"], avatar= f"{urls['user']}" if message["role"] == 'user' else f"{urls['pageicon']}"):
                st.markdown(message["parts"])
        elif message['role'] == 'reference_links':
            with st.expander("See Reference Links"):
                for url in message['reference_links']:
                    st.markdown(url, unsafe_allow_html=True)
        elif message['role'] == 'history':
            history = message['history'][-5:]

    st.caption(
        """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            color: #333;
            text-align: center;
            padding: 10px;
            font-size: 12px;
            z-index: 1000;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.caption(
                """
                <div class="sidebar-footer">
                Note: answer.engine might occasionally provides insufficient information. Use the reference links for additional information.
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("---")

        st.markdown(
            f'<div style="margin-top: 0.75em;"><a href="https://www.linkedin.com/in/jagadeeshreddyjr5" target="_blank"><img src="{urls["linkedin"]}" alt="LinkedIn" height="25" width="25"></a></div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div style="margin-top: 0.75em;"><a href="https://www.github.com/jagadeeshjr5" target="_blank"><img src="{urls["github"]}" alt="GitHub" height="25" width="25"></a></div>',
            unsafe_allow_html=True
        )




    if prompt := st.chat_input("Ask me!"):
        history.append(prompt)

        st.session_state.messages.append({"role": "user", "parts": prompt})
        with st.chat_message("user", avatar=f"{urls['user']}"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=f"{urls['pageicon']}"):
            try:
                start_time = time.time()
                with st.status("Processing..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    st.write("Processing query")
                    
                    search_query = process_query(prompt, model=selected_model, history=history)

                    st.write("Scraping content")

                    chunks, reference_urls = run_scraper_conc(search_query=search_query, num_urls=num_urls)

                    st.write("Preparing")

                    context = prepare_context(search_query, chunks, context_percentage=context_percentage)
                
                    model = Model(operation='answer', model=selected_model, api_key=api_key2)

                    end_time = time.time()
                    runtime = end_time - start_time
                    st.write("Answering")

                st.write(f"{runtime:.2f} seconds")
                output = model.answer(query=prompt, context=context)
                output_str = st.write_stream(output)

                video_urls = []
                try:
                    results = youtube_search(search_query)

                    if results:
                        video_urls = [result['url'] for result in results]

                        num_videos = len(video_urls)
                        cols = st.columns(num_videos)

                        # Display videos in dynamically created columns
                        for i, col in enumerate(cols):
                            with col:
                                st.video(video_urls[i], autoplay=True, muted=True)
                except:
                    pass
                    
                with st.expander("See Reference Links"):
                    for url in reference_urls:
                        st.markdown(url, unsafe_allow_html=True)

                related = []
                try:
                    model = Model(operation='related_queries', model=selected_model, api_key=api_key3)
                    related = model.related_queries(query=prompt, answer=output_str)
                    with st.expander("Related"):
                        if related:
                            for rel in related:
                                st.markdown(rel)
                        else:
                            st.markdown('none')
                except Exception as e:
                    pass      

                st.session_state.messages.append({"role": "assistant", "parts": output_str})

                st.session_state.messages.append({"role": "reference_links", "reference_links": reference_urls})

                st.session_state.messages.append({'role' : 'history', 'history' : history})
            except Exception as e:
                st.write(e)
