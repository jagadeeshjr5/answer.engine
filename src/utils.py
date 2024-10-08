from datetime import datetime
import streamlit as st
import os

from googleapiclient.discovery import build
import os
from typing import List

import json

api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = os.environ["API_KEY"] if "API_KEY1" in os.environ else st.secrets["API_KEY1"]
api_key2 = os.environ["API_KEY"] if "API_KEY2" in os.environ else st.secrets["API_KEY2"]
api_key3 = os.environ["API_KEY"] if "API_KEY3" in os.environ else st.secrets["API_KEY3"]
youtube_api_key = os.environ["YOUTUBE_API_KEY"] if "YOUTUBE_API_KEY" in os.environ else st.secrets["YOUTUBE_API_KEY"]

def load_urls(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        urls = file.read()
    urls_json = json.loads(urls)
    return urls_json


def current_datetime():
    """return current date and time"""
    return datetime.now()


def youtube_search(query : str, max_results : int = 5) -> List[dict]:

    """
    Searches YouTube for videos matching the query and returns the video titles and URLs.

    Args:
        query (str): The search query for YouTube.
        max_results (int): The maximum number of video results to return (default is 5).

    Returns:
        List[dict]: A list of dictionaries containing video titles and URLs.

    """
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