import streamlit as st
import asyncio
from utils import create_chunks, get_embeddings, make_context, load_urls
from model import Model, get_models
import time
import nest_asyncio
import subprocess
from scraper import scrape
from playwright_scraper import scrape_all_queries

import os

from utils import youtube_search
import shutil

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
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

st.set_page_config(
        page_title="answer.engine", page_icon=f"{urls['pageicon']}")

def install_playwright():
    """Function to install Playwright browser dependencies."""
    if 'playwright_installed' not in st.session_state:
        # Run installation only if it hasn't been marked as done in the session state
        subprocess.run(["playwright", "install"], check=True)
        st.session_state['playwright_installed'] = True
        #st.write("Playwright installed.")
        pass
    else:
        pass
        #st.write("Playwright installation already completed.")

# Place this at the start of your app to ensure it runs when the app is first loaded
install_playwright()

os.system('playwright install-deps')
os.system('playwright install')

import subprocess

def install_packages():
    # List of packages to install
    packages = [
        "libxslt1.1",
        "libwoff2-1",
        "libevent-2.1-7",
        "libopus0",
        "libwebp6",
        "libharfbuzz0b",
        "libenchant-2-2",
        "libsecret-1-0",
        "libhyphen0",
        "libgstreamer1.0-0",
        "libgstreamer-plugins-base1.0-0",
        "libflite1",
        "libegl1",
        "libgl1",
        "libgles2",
        "libx264-160"
    ]

    # Update package list
    subprocess.run(["sudo", "apt", "update"], check=True)

    # Install packages
    subprocess.run(["sudo", "apt", "install", "-y"] + packages, check=True)

try:
    install_packages()
except subprocess.CalledProcessError as e:
    print(f"An error occurred while installing packages: {e}")


answer_color = "#c32148"

st.markdown(f"<h1><span style='color:{answer_color};'>a</span>.E</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

history = []

for message in st.session_state.messages:
    if message['role'] in ['user', 'assistant']:
        with st.chat_message(message["role"], avatar= f"{urls['user']}" if message["role"] == 'user' else f"{urls['pageicon']}"):
            st.markdown(message["parts"])
    #elif message["role"] == 'youtube_urls':
    #    num_videos = len(message['youtube_urls'])
    #    cols = st.columns(num_videos)
    #    
    #    for i, col in enumerate(cols):
    #        with col:
    #            st.video(message['youtube_urls'][i], autoplay=False, muted=True)
    elif message['role'] == 'reference_links':
        with st.expander("See Reference Links"):
            for url in message['reference_links']:
                st.markdown(url, unsafe_allow_html=True)
    elif message['role'] == 'history':
        history = message['history'][-5:]
    #elif message['role'] == 'related_queries':
    #    with st.expander("Related"):
    #        if message['related_queries']:
    #            for rel in message['related_queries']:
    #                st.markdown(rel)
    #        else:
    #            st.markdown('none')
    

        

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
    #st.subheader("No. of references")
    #num_urls = st.slider(" ", min_value=1, max_value=10, value=5)
    num_urls = 1
    st.subheader("Percentage of context to be used")
    context_percentage = st.slider(" ", min_value=0.1, max_value=1.0, value=0.75)

    st.markdown("---")

    #enable_history = st.toggle("Enable memory:", )
    enable_history = False

    selected_scraper = st.radio(
        "**Select scraper**",
        ["Basic", "Advanced"],
        captions=[
            "Uses beautifulsoup",
            "Uses playwright"
        ],
    )

    #selected_model = st.sidebar.selectbox('**Choose a model:**', models, index=default_index)
    selected_model = 'gemini-1.5-flash'

    text_contents = ''
    
    for message in st.session_state.messages:
        if message['role'] in ['user']:
            text_contents += 'Query:\n' + message["parts"] + '\n\n'
        elif message['role'] in ['assistant']:
            text_contents += 'Response:\n' + message["parts"] + '\n\n'
        elif message['role'] == 'reference_links':
                for url in message['reference_links']:
                    text_contents += 'Reference Links:\n' + url
    

    #st.download_button("Download chat", text_contents, type='primary', file_name='chat.txt',)

    st.markdown("---")

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

import concurrent.futures

def run_scraper(query, num_urls):
    local_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        if selected_scraper == 'Basic':
            scraped_content, urls = scrape(query, num_urls)
        elif selected_scraper == 'Advanced':
            scraped_content, urls = scrape_all_queries(query, num_urls, driver=local_driver)
            
    finally:
        local_driver.quit()  # Ensure the local driver is closed
    return scraped_content, urls

def process_query(prompt, num_urls, model, history):
    model = Model(operation='search', model=model, api_key=api_key1)
    
    for _ in range(1):
        search_query = model.search(query=prompt, history=history, enable_history=enable_history)
        
        # Use ThreadPoolExecutor to run the scraper in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_scraper, search_query, num_urls)
            scraped_content, urls = future.result()  # Wait for the result

        if scraped_content.strip():
            break
            
    chunks = create_chunks(scraped_content)
    
    return search_query, chunks, urls

async def prepare_context(prompt, chunks, context_percentage=context_percentage):
    context = await make_context(query=prompt, context=chunks, context_percentage=context_percentage)
    return context


if prompt := st.chat_input("Ask me!"):

    history.append(prompt)

    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user", avatar=f"{urls['user']}"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=f"{urls['pageicon']}",):
        try:
            start_time = time.time()
            with st.status("Processing..."):
                

                #loop = asyncio.ProactorEventLoop()
                #asyncio.set_event_loop(loop)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                st.write("Processing query")
                st.write("Searching google")
                search_query, chunks, reference_urls = process_query(prompt, num_urls, model=selected_model, history=history)

                context = loop.run_until_complete(prepare_context(search_query, chunks, context_percentage=context_percentage))
            

                model = Model(operation='answer', model=selected_model, api_key=api_key2)

                end_time = time.time()
                runtime = end_time - start_time
                st.write("Answering query")

            st.write(f"{runtime:.2f} seconds")
            output = model.answer(query=prompt, context=context)
            output_str = st.write_stream(output, )

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
            #if video_urls:
                #st.session_state.messages.append({"role": "youtube_urls", "youtube_urls": video_urls})
            st.session_state.messages.append({"role": "reference_links", "reference_links": reference_urls})
            #if related:
            #    st.session_state.messages.append({"role": "related_queries", "related_queries": related})
            st.session_state.messages.append({'role' : 'history', 'history' : history})
            #st.write(history)
        except Exception as e:
            #st.error("Error accessing the response content. Please check the response structure.")
            #st.write("I'm sorry! I cannot answer the query at the moment. Try again later or choose another model.")
            st.write(e)