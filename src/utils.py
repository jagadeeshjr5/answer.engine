import google.generativeai as genai
from sentence_transformers.util import cos_sim
from datetime import datetime
import streamlit as st
import os
import multiprocessing

import numpy as np

import asyncio

from typing import List, Any

import json

api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]

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
    chunks = [' '.join(tokens[i : i + chunk_size]) for i in range(0, len(tokens), chunk_size - overlap)]
    return chunks

def get_embeddings(text : List):

    """
    Creates embeddings for the raw text fecthed by the scraper from web.

    text : List (List of chunks)
    
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

def make_context(query : str, context : List, context_percentage : float):

    """
    Prepares the context for the LLM to answer the user query

    query : str
    context : List
    context_percentage : float (Percentage of context to be passed to the LLM)
    
    """


    query_embedding = get_embeddings(query)
    context_embeddings = parallel_embeddings(context)

    similarities = cos_sim([query_embedding], context_embeddings)

    output_context = ''
    context_chunksize = round(context_percentage*len(context)) if len(context) < 20 else 10
    for i in reversed(similarities.argsort()[0][-context_chunksize:]):
        output_context = output_context + ' ' + (context[i.item()])

    return output_context

def current_datetime():
    """return current date and time"""
    return datetime.now()


class Model():
    def __init__(self):
        genai.configure(api_key=api_key)
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=3000,
                temperature=1.0)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest', generation_config=generation_config, safety_settings=[
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
])
    
    def answer(self, query, context):

        """
        query : str
        context : str

        """
        
        messages = [
        {'role':'user',
         'parts': [f"""Answer the following question based on the provided context: 
                   
                       Question: {query} 
                       Context: {context} 
                       
                       Provide a clear and detailed answer with rationale behind the response where necessary. Ensure the response is accurate and effective in conveying the correct information.
                       Do not mention that you are referring to a context to answer the question.
                
         
                      Question: {query}
                      Context: 
                      {context}
                      """]}
        ]
        response = self.model.generate_content(messages)
    
        return response.text