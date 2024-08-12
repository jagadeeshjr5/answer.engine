import streamlit as st
import asyncio
from scraper import scrape
from utils import create_chunks, get_embeddings, make_context, load_urls
from model import Model, get_models
import time
import nest_asyncio

import os

from utils import youtube_search

nest_asyncio.apply()

api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = os.environ["API_KEY1"] if "API_KEY1" in os.environ else st.secrets["API_KEY1"]
api_key2 = os.environ["API_KEY2"] if "API_KEY2" in os.environ else st.secrets["API_KEY2"]
api_key3 = os.environ["API_KEY3"] if "API_KEY3" in os.environ else st.secrets["API_KEY3"]

urls = load_urls(r'src/urls.txt')

models = get_models()
default_model = 'gemini-1.5-flash'
default_index = models.index(default_model)

async def run_scraper(query, num_urls):
    scraped_content, urls = await scrape(query, num_urls)
    return scraped_content, urls

async def process_query(prompt, num_urls, context_percentage, model, history):
    model = Model(operation='search', model=model, api_key=api_key1)
    for _ in range(3):
        search_query = model.search(query=prompt, history=history, enable_history=enable_history)
        scraped_content, urls = await run_scraper(search_query, num_urls)
        if scraped_content.strip():
            break
    chunks = create_chunks(scraped_content)
    context = await make_context(query=prompt, context=chunks, context_percentage=context_percentage)
    
    return search_query, context, urls

st.set_page_config(
        page_title="answer.engine", page_icon=f"{urls['pageicon']}")

answer_color = "#c32148"

st.markdown(f"<h1><span style='color:{answer_color};'>answer</span>.engine</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

history = []

for message in st.session_state.messages:
    if message['role'] in ['user', 'assistant']:
        with st.chat_message(message["role"], avatar= f"{urls['user']}" if message["role"] == 'user' else f"{urls['pageicon']}"):
            st.markdown(message["parts"])
    elif message["role"] == 'youtube_urls':
        num_videos = len(message['youtube_urls'])
        cols = st.columns(num_videos)
        
        for i, col in enumerate(cols):
            with col:
                st.video(message['youtube_urls'][i], autoplay=False, muted=True)
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
    st.subheader("No. of references")
    num_urls = st.slider(" ", min_value=1, max_value=10, value=5)
    st.subheader("Percentage of context to be used")
    context_percentage = st.slider(" ", min_value=0.1, max_value=1.0, value=0.5)

    st.markdown("---")

    enable_history = st.toggle("Enable history:", )

    selected_model = st.sidebar.selectbox('**Choose a model:**', models, index=default_index)

    text_contents = ''
    
    for message in st.session_state.messages:
        if message['role'] in ['user']:
            text_contents += 'Query:\n' + message["parts"] + '\n\n'
        elif message['role'] in ['assistant']:
            text_contents += 'Response:\n' + message["parts"] + '\n\n'
        elif message['role'] == 'reference_links':
                for url in message['reference_links']:
                    text_contents += 'Reference Links:\n' + url
    

    st.download_button("Download chat", text_contents, type='primary', file_name='chat.txt',)

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

if prompt := st.chat_input("Ask me!"):

    history.append(prompt)

    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user", avatar=f"{urls['user']}"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=f"{urls['pageicon']}",):
        try:
            with st.spinner("Processing..."):
                start_time = time.time()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                search_query, context, reference_urls = loop.run_until_complete(process_query(prompt, num_urls, context_percentage, model=selected_model, history=history))

                model = Model(operation='answer', model=selected_model, api_key=api_key2)

                end_time = time.time()
                runtime = end_time - start_time

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

                #related = []
                #try:
                    #model = Model(operation='related_queries', model=selected_model, api_key=api_key3)
                    #related = model.related_queries(query=prompt, answer=output_str)
                #    with st.expander("Related"):
                #        if related:
                #            for rel in related:
                #                st.markdown(rel)
                #        else:
                #            st.markdown('none')
                #except Exception as e:
                #    pass      

            st.session_state.messages.append({"role": "assistant", "parts": output_str})
            if video_urls:
                st.session_state.messages.append({"role": "youtube_urls", "youtube_urls": video_urls})
            st.session_state.messages.append({"role": "reference_links", "reference_links": reference_urls})
            #if related:
            #    st.session_state.messages.append({"role": "related_queries", "related_queries": related})
            st.session_state.messages.append({'role' : 'history', 'history' : history})
            #st.write(history)
        except Exception as e:
            #st.error("Error accessing the response content. Please check the response structure.")
            st.write("I'm sorry! I cannot answer the query at the moment. Try again later or choose another model.")
            st.write(e)
