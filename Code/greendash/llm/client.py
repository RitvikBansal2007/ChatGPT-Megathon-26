import os
from dotenv import load_dotenv
def init_llm_client():
    try:
        from google import genai
    except ImportError:
        raise ValueError("google-genai package is not installed! Cannot initialize LLM client.")
    # .env is loaded by config.settings, not into os.environ, so read both.
    from config.settings import settings
    api_key = os.environ.get("GEMINI_API_KEY") or settings.llm_api_key
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
