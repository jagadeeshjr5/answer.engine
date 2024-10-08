import subprocess
import tempfile

import json

import os
import streamlit as st

def fetch_urls_from_dynamodb(table) -> set:
    """
    Fetch all unique URLs from the provided DynamoDB table.

    Args:
        table (DynamoDB.Table): The DynamoDB table object to scan for URLs.

    Returns:
        set: A set of unique URLs found in the table.

    """
    url_set = set()
    response = table.scan()

    while True:
        items = response.get('Items', [])
        for item in items:
            url = item.get('url')
            if url:
                url_set.add(url)

        # Handle pagination
        response = table.scan(ExclusiveStartKey=response.get('LastEvaluatedKey')) if 'LastEvaluatedKey' in response else None
        if not response:
            break

    return url_set

def fetch_content_from_dynamodb(table, url_set: set) -> list:
    """

    Fetch content from DynamoDB for a provided set of URLs.

    Args:
        table (DynamoDB.Table): The DynamoDB table object to fetch content from.
        url_set (set): A set of URLs for which content needs to be fetched.

    Returns:
        list: A list of content corresponding to the URLs provided.
    
    """
    content_list = []
    url_batches = [list(url_set)[i:i + 100] for i in range(0, len(url_set), 100)]  # Creating batches of 100

    for batch in url_batches:
        request_keys = [{'url': url} for url in batch]
        response = table.meta.client.batch_get_item(RequestItems={table.name: {'Keys': request_keys}})

        while True:
            items = response.get('Responses', {}).get(table.name, [])
            content_list.extend(item.get('content') for item in items if item.get('content'))

            # Handle unprocessed keys
            if 'UnprocessedKeys' in response and response['UnprocessedKeys']:
                response = table.meta.client.batch_get_item(RequestItems=response['UnprocessedKeys'])
            else:
                break

    return content_list

def run_writecache_script(table_name: str, data_to_insert: dict, api_key : str):
    """

    Run an external write cache script to insert data into a cache.

    Args:
        table_name (str): The name of the DynamoDB table to which the data will be written.
        data_to_insert (dict): A dictionary containing the data to be written to the cache.
        api_key (str) : api key for Google Gemini

    Returns:
        subprocess.Popen: The process object for the running subprocess, which can be used to monitor the script execution.
    
    """
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as temp_file:
        json.dump(data_to_insert, temp_file)
        temp_file_path = temp_file.name

    # Pass the temporary file path as an argument to the subprocess
    process = subprocess.Popen(
        ['python', 'src/write_cache.py', '--table_name', table_name, '--data_file', temp_file_path, '--api_key', api_key],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    return process