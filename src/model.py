import google.generativeai as genai
import os

import streamlit as st

from utils import PromptTemplate

import json

api_key = os.environ["API_KEY"] if "API_KEY" in os.environ else st.secrets["API_KEY"]
api_key1 = "AIzaSyBHu3EJUtRPeWZXh0rgZFPs7Sqk0nzAuDY"
api_key2 = "AIzaSyCk0rWSuGaXImcVBjVTo4wqFwZ7fyX_BY0"

pt = PromptTemplate()

def get_models():
    genai.configure(api_key=api_key)
    models = [model.name for model in genai.list_models() if 'generateContent' in model.supported_generation_methods]
    models = [model[7:] for model in models]
    return models
    

class Model():
    def __init__(self, operation : str, model : str):

        self.operation = operation
        self.model = model

        self.response_type = "application/json" if self.operation == 'related_queries' else None

        self.system_instruction = (
            pt.answer_systeminstruction() if self.operation == 'answer' 
            else None if self.operation == 'search' 
            else None
        )

        genai.configure(api_key=api_key1)
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=2000,
            temperature=1.0, response_mime_type=self.response_type
        )
        self.model = genai.GenerativeModel(
            self.model,
            generation_config=generation_config,
            safety_settings=[
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
            ],
            system_instruction=self.system_instruction
        )
        
    def search(self, query, history):
        """
        query : str
        context : str
        """
        messages = [{'role': 'user', 'parts': [pt.search_systeminstruction(query=query, history=history)]}]
        response = self.model.generate_content(messages)
        return response.text
    

    def answer(self, query, context):
        messages = [
            {
                'role': 'user',
                'parts': [pt.prompttemplate(query, context)]
            }
        ]
        for response in self.model.generate_content(messages, stream=True):
            for token in response:
                yield token.text
    
    def related_queries(self, query, answer):
        messages = [
            {
                'role': 'user',
                'parts': [pt.related_queries(query=query, answer=answer)]
            }
        ]
        response = self.model.generate_content(messages)
        response = json.loads(response.text)
        return response