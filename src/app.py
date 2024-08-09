import streamlit as st
import asyncio
from scraper import scrape
from utils import create_chunks, get_embeddings, make_context, load_urls
from model import Model, get_models
import time
import nest_asyncio

nest_asyncio.apply()

urls = load_urls(r'src/urls.txt')

models = get_models()
default_model = 'gemini-1.5-pro-exp-0801'
default_index = models.index(default_model)

async def run_scraper(query, num_urls):
    scraped_content, urls = await scrape(query, num_urls)
    return scraped_content, urls

async def process_query(prompt, num_urls, context_percentage, model):
    model = Model(operation='search', model=model)
    for _ in range(3):
        search_query = model.search(query=prompt)
        scraped_content, urls = await run_scraper(search_query, num_urls)
        if scraped_content.strip():
            break
    chunks = create_chunks(scraped_content)
    context = await make_context(query=prompt, context=chunks, context_percentage=context_percentage)
    
    return context, urls

st.set_page_config(
        page_title="answer.engine", page_icon=f"{urls['pageicon']}")

answer_color = "#c32148"

st.markdown(f"<h1><span style='color:{answer_color};'>answer</span>.engine</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message['role'] in ['user', 'assistant']:
        with st.chat_message(message["role"], avatar= f"{urls['user']}" if message["role"] == 'user' else f"{urls['pageicon']}"):
            st.markdown(message["parts"])
    else:
        with st.expander("See Reference Links"):
            for url in message['reference_links']:
                st.markdown(url, unsafe_allow_html=True)

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

    selected_model = st.sidebar.selectbox("Choose a model:", models, index=default_index)

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

    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user", avatar=f"{urls['user']}"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=f"{urls['pageicon']}"):
        try:
            with st.spinner("Processing..."):
                start_time = time.time()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                context, reference_urls = loop.run_until_complete(process_query(prompt, num_urls, context_percentage, model=selected_model))

                model = Model(operation='answer', model=selected_model)

                end_time = time.time()
                runtime = end_time - start_time

                st.write(f"{runtime:.2f} seconds")
                output = model.answer(query=prompt, context=context)
                output_str = st.write_stream(output)
                
                with st.expander("See Reference Links"):
                    for url in reference_urls:
                        st.markdown(url, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "parts": output_str})
            st.session_state.messages.append({"role": "reference_links", "reference_links": reference_urls})
        except Exception as e:
            #st.error("Error accessing the response content. Please check the response structure.")
            st.write("I'm sorry! I cannot answer the query at the moment. Try again later or choose another model.")
            #st.write(e)
