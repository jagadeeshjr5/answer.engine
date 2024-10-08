import google.generativeai as genai
from sentence_transformers.util import cos_sim
#from sklearn.metrics.pairwise import cosine_similarity as cos_sim
import streamlit as st
import os
import multiprocessing

import numpy as np

import os
from typing import List, Any


api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = os.environ["API_KEY"] if "API_KEY1" in os.environ else st.secrets["API_KEY1"]
api_key2 = os.environ["API_KEY"] if "API_KEY2" in os.environ else st.secrets["API_KEY2"]
api_key3 = os.environ["API_KEY"] if "API_KEY3" in os.environ else st.secrets["API_KEY3"]

def create_chunks(text : str) -> List:
    """
    Creates overlapping chunks from a given text.

    Args:
        text (str): The input text to be divided into chunks.
    
    Returns
        list: A list of strings, where each string is a chunk of the original text.
    
    """
    tokens = text.split(' ')

    chunk_size = int(round(0.1 * len(tokens))) if len(tokens) < 3000 else 300
    overlap = int(round(0.1*chunk_size))

    step_size = chunk_size - overlap
    if step_size <= 0:
        step_size = 1
    chunks = [' '.join(tokens[i : i + chunk_size]) for i in range(0, len(tokens), step_size)]
    return chunks

def get_embeddings(text : List[str]) -> List:

    """
    Generates embeddings for a list of text chunks.

    Args:
        text (List[str]): A list of text chunks for which embeddings need to be generated.

    Returns:
        list: A list of embeddings, where each embedding corresponds to a text chunk.
    
    """
    genai.configure(api_key=api_key)
    embeddings = genai.embed_content(
    model="models/embedding-001",
    content=text,
    task_type="clustering", output_dimensionality=128)

    return embeddings['embedding']

def parallel_embeddings(text_chunks: List[str]) -> List[np.ndarray]:
    """
    Generates embeddings for a list of text chunks in parallel using multiprocessing.
    
    Args:
        text_chunks (List[str]): A list of text chunks for which embeddings will be generated.
    
    Returns:
        List[np.ndarray]: A list of embeddings, where each embedding corresponds to a text chunk. 
        Each embedding is represented as a NumPy array.
    
    """
    num_cores = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=num_cores) as pool:
        embeddings = pool.map(get_embeddings, text_chunks)
    return embeddings

def make_context(query : str, context : List[str], context_percentage : float) -> str:

    """
    Prepares the context for the Model to answer the user query.
    
    Args:
        query (str): The user's input query for which a response is required.
        context (List[str]): A list of context strings (chunks) to be ranked based on relevance to the query.
        context_percentage (float): The percentage of context (based on relevance) to include in the final output.

    Returns
        str: A string containing the most relevant chunks of context for the given query.
    
    """


    query_embedding = get_embeddings(query)
    context_embeddings = get_embeddings(context)

    similarities = cos_sim(query_embedding, context_embeddings)

    output_context = ''
    context_chunksize = round(context_percentage*len(context)) if len(context) < 20 else 10
    for i in reversed(similarities.argsort()[0][-context_chunksize:]):
        output_context = output_context + ' ' + (context[i.item()])

    return output_context