from asyncio import Semaphore

from ai.components.ai_clients import CustomAsyncOpenAI
from ai.components.fetching import fetch_ai_client


async def ai_fetch_for_md(sem: Semaphore, prompt: str, doc_source: str, client: CustomAsyncOpenAI) -> str:
    async with sem:
        return await fetch_ai_client(prompt % doc_source, client=client, parse_json=False)
