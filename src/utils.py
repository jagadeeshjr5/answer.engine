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

    step_size = chunk_size - overlap
    if step_size <= 0:
        step_size = 1
    chunks = [' '.join(tokens[i : i + chunk_size]) for i in range(0, len(tokens), step_size)]
    return chunks

async def get_embeddings(text : List[str]):

    """
    Creates embeddings for the raw text fecthed by the scraper from web.

    Args:
    - text : List[str] (List of chunks).

    Returns:
    - List of embeddings for the text chunks.
    
    """
    genai.configure(api_key=api_key)
    embeddings = await genai.embed_content_async(
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

async def make_context(query : str, context : List[str], context_percentage : float):

    """
    Prepares the context for the LLM to answer the user query
    
    Args:
    - query : str
    - context : List[str]
    - context_percentage : float (Percentage of context to be passed to the LLM)

    Returns"
    - output_context : str
    
    """


    query_embedding = await get_embeddings(query)
    context_embeddings = await get_embeddings(context)

    similarities = cos_sim([query_embedding], context_embeddings)

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
        
        return f"""Answer the following question based on the provided context: 
                   
Question: {query} 
Context: {context} 

Provide a clear and detailed answer with rationale behind the response where necessary. Ensure the response is accurate and effective in conveying the correct information.
Do not mention that you are referring to a context to answer the question. If the provided context is not relevant or empty then return ```I'm sorry! I couldn't find much information about this query. Please try asking in other way.```
            """
    
    def answer_systeminstruction(self):
        return """You are an answer engine. your name is answer.engine"""
    
    def search_systeminstruction(self):

        return """You are a Google search engine query optimizer. Your task is to transform the user's input into an optimized Google search query that will yield the most relevant and accurate results. Ensure that the query is clear, concise, and includes key terms that directly pertain to the user's intent.
You should return only a single sentence."""