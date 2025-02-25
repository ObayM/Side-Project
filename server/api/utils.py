import os
import subprocess
from api.config import settings
from google import genai
from time import sleep
from api.pinecone_utils import pinecone_index
from google.genai import types

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

def run_commands(command: str):
    """Executes system commands securely."""
    try:
        if command.startswith("python"):
            subprocess.run(command.split(), check=True)
        else:
            print("Unknown command")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

def gemini_embed_text(text: str):
    """Generates an embedding using Gemini API."""
    try:
        result = client.models.embed_content(model="models/text-embedding-004", contents=text)
        return result.embeddings[0].values

    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def process_query(query: str):
    """Processes user query, generates embeddings, and searches Pinecone."""
    if not query:
        return None

    query_embedding = gemini_embed_text(query)
    results = pinecone_index.query(
        vector=query_embedding, 
        top_k=5, 
        namespace=settings.PINECONE_NAMESPACE, 
        include_metadata=True
    )

    contexts = [item['metadata']['example'] for item in results.to_dict().get('matches', [])]

    message = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[:10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query
    return message

def get_llm_response(msg: str, system_prompt: str = None):
    """Gets a response from Gemini LLM."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt),
        contents=[msg]
    )
    return response.text

