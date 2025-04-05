import os
import json
import asyncio
from asyncio import Semaphore

from ai.utils import get_chunks
from ai.clients import CustomAsyncOpenAI, AIClient
from ai.fetch import fetch_ai_client
from core import (
    STEP_2_TICKETS_TARGET,
    STEP_3_TICKETS_TARGET, TooLongTextError
)

from ai.prompts import (
    QA_PROMPT,
    QA_COMBINATION_PROMPT
)


async def ai_fetch_4_qa(sem: Semaphore, conversation_data: str, lvl: int = 1, client: CustomAsyncOpenAI = None) -> list:
    async with sem:
        conversations = get_chunks(conversation_data, lvl=lvl)
        try:
            analysis_list = []

            tasks = [
                asyncio.create_task(fetch_ai_client(QA_PROMPT % conversation, client)) for conversation in conversations
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

            for d_task in done:
                if d_task.exception():
                    [p.cancel() for p in pending]
                    raise d_task.exception()
                task_result = d_task.result()
                if task_result is None:
                    raise TooLongTextError

                if task_result:
                    analysis_list.append(d_task.result())

            if not analysis_list:
                return []

            if len(analysis_list) > 1:
                final_result = await fetch_ai_client(QA_COMBINATION_PROMPT % json.dumps(analysis_list), client)
            else:
                final_result = analysis_list[0]
            return final_result
        except TooLongTextError:
            pass

    lvl += 1
    return await ai_fetch_4_qa(sem, conversation_data, lvl=lvl, client=client)


async def bulk_ai_fetch_4_qa(sem):
    step_2_target = str(STEP_2_TICKETS_TARGET) + "_OK"
    step_3_target = STEP_3_TICKETS_TARGET

    os.makedirs(str(step_3_target), exist_ok=True)

    tasks = pending = {}
    async with AIClient() as client:
        for file_name in os.listdir(step_2_target):
            with open(f"{step_2_target}/{file_name}") as file:
                ticket_data = json.load(file)
                tasks[
                    asyncio.create_task(ai_fetch_4_qa(sem, ticket_data["conversations"], client=client))
                ] = ticket_data

        while pending:
            done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                task_result = done_task.result()
                if not task_result:
                    continue
                ticket_data = tasks[done_task]
                with open(f"{step_3_target / ticket_data["ticket_id"]}.json", "w") as file:
                    json.dump(task_result, file, ensure_ascii=False, indent=4)
