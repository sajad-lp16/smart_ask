from openai import AsyncOpenAI

from core.config import AI_FOR_PROCESS

from ai import (
    ai_2_model,
    ai_2_apikey,
    ai_2_base_url
)


class CustomAsyncOpenAI(AsyncOpenAI):
    def get_template(self, prompt: str) -> dict:
        ai = AI_FOR_PROCESS
        ai_model = ai_2_model[ai]

        return {
            "model": ai_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            "stream": False
        }


class AIClient:
    def __init__(self):
        self.client = None
        self.ai = AI_FOR_PROCESS

    async def __aenter__(self):
        self.client = CustomAsyncOpenAI(api_key=ai_2_apikey[self.ai], base_url=ai_2_base_url[self.ai])
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
