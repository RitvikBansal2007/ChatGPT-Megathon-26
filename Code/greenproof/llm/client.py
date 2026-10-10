import os
from dotenv import load_dotenv
from google import genai

env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path=env_path)

def init_llm_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env! Cannot initialize LLM client.")
        
    client = genai.Client(api_key=api_key)
    return client

llm_client = None

def get_client():
    global llm_client
    if llm_client is None:
        llm_client = init_llm_client()
    return llm_client
