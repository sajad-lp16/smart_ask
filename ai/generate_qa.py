import json
import asyncio
from asyncio import Semaphore

from ai.components.scripts import get_chunks
from ai.components.ai_clients import CustomAsyncOpenAI
from ai.components.fetching import fetch_ai_client

from ai.components.prompts import QA_COMBINATION_PROMPT


async def ai_fetch_for_qa(sem: Semaphore, qa_prompt, conversation_data: str, client: CustomAsyncOpenAI) -> list:
    async with sem:
        conversations = get_chunks(conversation_data)
        analysis_list = []

        tasks = [
            asyncio.create_task(fetch_ai_client(qa_prompt % conversation, client)) for conversation in conversations
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for d_task in done:
            if d_task.exception():
                [p.cancel() for p in pending]
                raise d_task.exception()
            task_result = d_task.result()

            if task_result:
                analysis_list.append(d_task.result())

        if not analysis_list:
            return []

        if len(analysis_list) > 1:
            final_result = await fetch_ai_client(QA_COMBINATION_PROMPT % json.dumps(analysis_list), client)
        else:
            final_result = analysis_list[0]
        return final_result
