import boto3
import json
import argparse

import google.generativeai as genai
import concurrent.futures


def insert_into_cache(table_name : str, data : dict):
    """

    Inserts items into a DynamoDB table in batch mode.

    Args:
        table_name (str): The name of the DynamoDB table where the items will be inserted.
        data (dict): A dictionary containing the items to insert, where keys are URLs and values are their corresponding content.

    Returns:
        None: This function does not return any value. It performs insertion into DynamoDB.

    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    if not data:
        return
    with table.batch_writer() as batch:
        for keys, values in data.items():
            batch.put_item(Item={'url': keys, 'content': values})
            #print(f'Inserted item: {keys}')

def transform(content : str, api_key : str) -> str:
    """

    Transforms the provided content into clean, plain text suitable for storage.

    Args:
        content (str): The raw content to be transformed.
        api_key (str) : api key for Google Gemini

    Returns:
        str: The transformed clean text content. If the transformation fails, returns an empty string.

    """
    genai.configure(api_key=api_key)
    generation_config=genai.types.GenerationConfig(
        max_output_tokens=5000,
            temperature=1.0)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config, safety_settings=[
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
            ], system_instruction="""Extract the **main plain text content** from the webpage, ensuring the following:
    Capture the main theme of the webpage effectively.
    1. **Remove**:
        - Ads, pop-ups, and promotional content.
        - Navigation bars, sidebars, and footer information.
        - Social media links, share buttons, and comment sections.
        - Unrelated sections like "Related Articles," "Popular Posts," or "You might also like."
    
    2. **Keep**:
        - The primary article or body text.
        - Titles and subtitles relevant to the main content.
        - Structured paragraphs and bullet points (if part of the main content).
    
    3. **Output**: Clean, plain text suitable for storage, with no extraneous formatting or links.
    """)
    messages = [
        {'role':'user',
         'parts': [f"""
                    Content: {content}"""]}
    ]
    response = model.generate_content(messages)
    #output = response.text
    for candidate in response.candidates:
        return ''.join([part.text for part in candidate.content.parts])
    
if __name__ == "__main__":

    """
    Main script to insert URL and content into a DynamoDB table.

    Command-line arguments:
        --table_name: Name of the DynamoDB table to insert data into.
        --data_file: Path to the JSON file containing the data to be processed.
    """

    parser = argparse.ArgumentParser(description="Insert URL and content into DynamoDB")
    parser.add_argument('--table_name', type=str, required=True, help="DynamoDB table name")
    parser.add_argument('--data_file', type=str, required=True, help="Data in dict")
    parser.add_argument('--api_key', type=str, required=True, help="Gemini api key")
    args = parser.parse_args()
    try:
        with open(args.data_file, 'r') as file:
            data_dict = json.load(file)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_key = {executor.submit(transform, v, args.api_key): k for k, v in data_dict.items()}
            data_dict = {}
            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    transformed_value = future.result()
                    data_dict[key] = transformed_value
                except Exception as e:
                    pass

        insert_into_cache(args.table_name, data_dict)
    except Exception as e:
        pass

