from typing import List

class PromptTemplate():

    """
    A class to generate templates for prompts used in question-answering and query enhancement tasks.
    
    Methods:
        - prompttemplate(query: str, context: str) -> str:
            Generates a prompt instructing the model to answer a given query based on a specific context.
        
        - answer_systeminstruction() -> str:
            Provides a system instruction that introduces the model as an answer engine, with additional details.

        - search_systeminstruction(query: str, history: List[str], enable_history: str) -> str:
            Generates a prompt to enhance search queries, taking into account the user's query and prior history if enabled.

        - related_queries(query: str, answer: str) -> str:
            Creates a list of related queries based on a given query and the corresponding answer.

    """

    def __init__(self):
        pass

    def prompttemplate(self, query : str, context : str) -> str:

        """

        Generates a prompt for answering a user query based on the provided context.

        Args:
            query (str): The user's question.
            context (str): The context to be used in generating the answer.

        Returns:
            str: A structured prompt asking the model to answer the query based on the context.

        """
        
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
    
    def answer_systeminstruction(self) -> str:

        """
        Provides a system instruction that introduces the model as an answer engine.

        Returns:
            str: The system instruction introducing the model's role and its creator.

        """
        return """You are an answer engine. your name is answer.engine. Your creator is Jagadeesh Reddy Nukareddy"""
    
    def search_systeminstruction(self, query : str, history : List, enable_history : str) -> str:

        """
        Generates a search query enhancement prompt based on the user's query and previous history.

        Args:
            query (str): The current user query.
            history (List[str]): A list of previous queries, if query history is enabled.
            enable_history (str): A flag indicating whether query history is enabled or not.

        Returns:
            str: A prompt instructing the model to improve the query for better search engine results.

        """

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
        

    def related_queries(self, query : str, answer : str) -> str:

        """
        Generates related queries based on the original query and its corresponding answer.

        Args:
            query (str): The original user query.
            answer (str): The answer generated for the query.

        Returns:
            str: A prompt that generates 3-5 related queries based on the original query and answer.

        """
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