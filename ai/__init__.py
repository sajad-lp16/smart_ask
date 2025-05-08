import os
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

from core.config import (
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_KEY,

    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_API_KEY,

    GEMINI_BASE_URL,
    GEMINI_MODEL,
    GEMINI_API_KEY,

    AI_FOR_RESPONSE
)

os.environ.setdefault("OPENAI_API_KEY", OPENAI_KEY)

ai_2_model = {
    "deepseek": DEEPSEEK_MODEL,
    "openai": OPENAI_MODEL,
    "gemini": GEMINI_MODEL
}

ai_2_apikey = {
    "deepseek": DEEPSEEK_API_KEY,
    "openai": OPENAI_KEY,
    "gemini": GEMINI_API_KEY
}

ai_2_base_url = {
    "deepseek": DEEPSEEK_BASE_URL,
    "openai": OPENAI_BASE_URL,
    "gemini": GEMINI_BASE_URL
}

response_model: str = AI_FOR_RESPONSE

llm = OpenAI(model=ai_2_model[response_model])  # llama index only supports OpenAI
Settings.llm = llm

# embed_model = OllamaEmbedding(
#     model_name="nomic-embed-text:latest",
#     base_url="http://127.0.0.1:11434",
# )
# llm = Ollama(
#     model="llama3.2:3b",
#     base_url="http://127.0.0.1:11434",
#     temperature=0.1
# )
# Settings.llm = llm
# Settings.embed_model = embed_model
