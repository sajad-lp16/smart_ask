from decouple import config

from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

ai_2_model = {
    "deepseek": config("DEEPSEEK_MODEL"),
    "openai": config("OPENAI_MODEL")
}

ai_2_apikey = {
    "deepseek": config("DEEPSEEK_API_KEY"),
    "openai": config("OPENAI_KEY")
}

ai_2_base_url = {
    "deepseek": config("DEEPSEEK_BASE_URL"),
    "openai": config("OPENAI_BASE_URL")
}

response_model: str = config("AI_FOR_RESPONSE", cast=str)

llm = OpenAI(model=ai_2_model[response_model])  # llama index only supports OpenAI
Settings.llm = llm
