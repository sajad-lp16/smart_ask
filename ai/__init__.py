import os
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.llms.gemini import Gemini

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

ai_2_client = {
    "openai": lambda: OpenAI(model=OPENAI_MODEL),
    "gemini": lambda: Gemini(model=GEMINI_MODEL),
}

response_model: str = AI_FOR_RESPONSE

llm = ai_2_client[response_model]()
Settings.llm = llm
