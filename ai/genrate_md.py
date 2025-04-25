from asyncio import Semaphore

from ai.utils.ai_clients import CustomAsyncOpenAI
from ai.utils.fetch import fetch_ai_client
from ai.utils.prompts import AVICENNA_LEARN_PROMPT


async def ai_fetch_for_summarize(sem: Semaphore, doc_source: str, client: CustomAsyncOpenAI) -> str:
    async with sem:
        return await fetch_ai_client(prompt=AVICENNA_LEARN_PROMPT % doc_source, client=client)
