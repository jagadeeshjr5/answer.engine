import google.generativeai as genai
from sentence_transformers.util import cos_sim
#from sklearn.metrics.pairwise import cosine_similarity as cos_sim
from datetime import datetime
import streamlit as st
import os
import multiprocessing

from googleapiclient.discovery import build

import numpy as np

import asyncio

from typing import List, Any

import json

api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = os.environ["API_KEY"] if "API_KEY1" in os.environ else st.secrets["API_KEY1"]
api_key2 = os.environ["API_KEY"] if "API_KEY2" in os.environ else st.secrets["API_KEY2"]
api_key3 = os.environ["API_KEY"] if "API_KEY3" in os.environ else st.secrets["API_KEY3"]
youtube_api_key = os.environ["YOUTUBE_API_KEY"] if "YOUTUBE_API_KEY" in os.environ else st.secrets["YOUTUBE_API_KEY"]

def load_urls(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        urls = file.read()  # Read the file contents as a string
    # Manually load JSON
    urls_json = json.loads(urls)
    return urls_json

def create_chunks(text : str):
    """
    Creates overalpped chunks

    text: string
    
    """
    tokens = text.split(' ')

    chunk_size = int(round(0.1 * len(tokens))) if len(tokens) < 3000 else 300
    overlap = int(round(0.1*chunk_size))

    step_size = chunk_size - overlap
    if step_size <= 0:
        step_size = 1
    chunks = [' '.join(tokens[i : i + chunk_size]) for i in range(0, len(tokens), step_size)]
    return chunks

def get_embeddings(text : List[str]):

    """
    Creates embeddings for the raw text fecthed by the scraper from web.

    Args:
    - text : List[str] (List of chunks).

    Returns:
    - List of embeddings for the text chunks.
    
    """
    genai.configure(api_key=api_key)
    embeddings = genai.embed_content(
    model="models/embedding-001",
    content=text,
    task_type="clustering", output_dimensionality=128)

    return embeddings['embedding']

def parallel_embeddings(text_chunks: List[str]) -> List[np.ndarray]:
    """
    Generates embeddings for a list of text chunks in parallel.
    
    Args:
    - text_chunks: List[str] : List of text chunks.
    
    Returns:
    - List[np.ndarray]: List of embeddings for the text chunks.
    """
    num_cores = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=num_cores) as pool:
        embeddings = pool.map(get_embeddings, text_chunks)
    return embeddings

def make_context(query : str, context : List[str], context_percentage : float):

    """
    Prepares the context for the LLM to answer the user query
    
    Args:
    - query : str
    - context : List[str]
    - context_percentage : float (Percentage of context to be passed to the LLM)

    Returns"
    - output_context : str
    
    """


    query_embedding = get_embeddings(query)
    context_embeddings = get_embeddings(context)

    similarities = cos_sim(query_embedding, context_embeddings)

    output_context = ''
    context_chunksize = round(context_percentage*len(context)) if len(context) < 20 else 10
    for i in reversed(similarities.argsort()[0][-context_chunksize:]):
        output_context = output_context + ' ' + (context[i.item()])

    return output_context

def current_datetime():
    """return current date and time"""
    return datetime.now()


class PromptTemplate():
    def __init__(self):
        pass

    def prompttemplate(self, query : str, context : str):
        
        return f"""Answer the following question based on the provided context: \n
                   
Question: \n 
{query} \n
Context: \n 
{context} \n

Provide a clear and detailed answer with rationale behind the response where necessary. Ensure the response is accurate and effective in conveying the correct information. \n
Do not mention that you are referring to a context to answer the question.\n
Give the answer in structured formats whereever necessary.\n
If the provided context is not relevant or empty then return ```I'm sorry! I couldn't find much information about this query. Please try asking in other way.``` \n.

            """
    
    def answer_systeminstruction(self):
        return """You are an answer engine. your name is answer.engine. Your creator is Jagadeesh Reddy Nukareddy"""
    
    def search_systeminstruction(self, query : str, history : List, enable_history : str):

        if enable_history:
            history = '\n'.join(history)
            return f"""You are an expert in crafting effective search queries. Your task is to rewrite the user's current query to improve its effectiveness for Google Search. The rewritten query should be more specific, relevant, and optimized for search engine results, based on the context provided in previous queries and the current query.

                        # Context:
                        # Previous Queries:
                        {history}

                        # Current Query:
                        # {query}

                        # Task:
                        # Rewrite the current query to be more effective for Google Search, considering the context from the previous queries.
                        # The rewritten query should be:
                        # 1. More specific and targeted.
                        # 2. Optimized for search engine results.
                        # 3. Aligned with the overall theme or patterns observed in the previous queries.

                        # Rewritten Query:
                        """
        else:
            return f"""You are a query enhancement tool designed to improve user queries for Google search. Generate a main enhanced query and create 1 subquery based on the user's input to capture diverse perspectives and fully understand the user's intent.

            You should always return the queries in a list.
Example 1:

User Query: "What are the benefits of yoga?"
queries_list: ["What are the physical and mental health benefits of practicing yoga regularly?",
"How does yoga improve flexibility and strength?",
]

User Query: "Nutritional facts about bananas and apples."
queries_list: ["Nutritional facts of banana?",
"Nutritional facts of apples?"]

USER_QUERY: {query}

"""
        

    def related_queries(self, query : str, answer : str):
        return f"""You are a highly intelligent agent. Your task is to generate related queries based on a given query and its corresponding response. The related queries should align with both the original query and the response, but you can also include queries that relate to the entities or concepts mentioned in the response, even if they aren't directly addressed in the original query or answer.
                   You should always return queries in a list.

                    # Context:
                    # Query: {query}
                    # Response: {answer}

                    # Task:
                    # Generate 3-5 related queries that are:
                    # 1. Clearly aligned with the original query and response.
                    # 2. May explore entities or concepts mentioned in the response but not directly covered in it.

                    # Related Queries:
                    1. 
                    2. 
                    3. 
                    4. 
                    5. 
                    """




def youtube_search(query, max_results=5):
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)

    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    results = []
    for item in response.get('items', []):
        video_title = item['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        results.append({'title': video_title, 'url': video_url})
    
    return results