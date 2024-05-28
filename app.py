import streamlit as st
import asyncio
from scraper import scrape
from utils import create_chunks, get_embeddings, make_context, Model

import time

async def run_scraper(query, num_urls):
    scraped_content, urls = await scrape(query, num_urls)
    return scraped_content, urls

st.title("answer.engine")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])


st.markdown(
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

    st.markdown(
            """
            <div class="sidebar-footer">
            Note: answer.engine might occasionally provides insufficient information. Use the reference links for additional information.
            </div>
            """,
            unsafe_allow_html=True
        )

if prompt := st.chat_input("Ask me!"):

    st.session_state.messages.append({"role": "user", "parts": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        messages = [
            {'role': 'user', 'parts': [prompt]}
        ]


        try:
            start_time = time.time()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraped_content, urls = loop.run_until_complete(run_scraper(prompt, num_urls))

            chunks = create_chunks(scraped_content)
            #context = loop.run_until_complete(amake_context(query=prompt, context=chunks, context_percentage=context_percentage))
            context = make_context(query=prompt, context=chunks, context_percentage=context_percentage)
            end_time = time.time()
            runtime = end_time - start_time
            st.write(f"Time taken to retreive the context: {runtime:.2f} seconds")
            model = Model()
            output = model.answer(query=prompt, context=context)
            st.markdown(output)
            with st.expander("See Reference Links"):
                for url in urls:
                    st.markdown(url, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "parts": output})
        except AttributeError as e:
            st.error("Error accessing the response content. Please check the response structure.")
            st.write(e)



