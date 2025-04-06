import os
import json
import asyncio
from asyncio import Semaphore

from ai.utils.scripts import get_chunks
from ai.clients import CustomAsyncOpenAI, AIClient
from core import (
    STEP_2_TICKETS_TARGET,
    STEP_4_TICKETS_TARGET, TooLongTextError,
)
from ai.fetch import fetch_ai_client

from ai.utils.prompts import (
    SUMMARIZE_PROMPT,
    SUMMARIZE_COMBINATION_PROMPT
)


async def ai_fetch_4_summarize(sem: Semaphore, conversation_data: str, lvl: int = 1,
                               client: CustomAsyncOpenAI = None) -> list:
    async with sem:
        conversations = get_chunks(conversation_data, lvl=lvl)
        try:
            analysis_list = []

            tasks = [
                asyncio.create_task(
                    fetch_ai_client(prompt=SUMMARIZE_PROMPT % conversation, client=client)
                ) for conversation in conversations
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

            for d_task in done:
                if d_task.exception():
                    [p.cancel() for p in pending]
                    raise d_task.exception()

                task_result = d_task.result()
                if task_result is None:
                    raise TooLongTextError

                analysis_list.append(task_result)

            if len(analysis_list) > 1:
                final_result = await fetch_ai_client(
                    SUMMARIZE_COMBINATION_PROMPT % json.dumps(analysis_list), client=client
                )
            else:
                final_result = analysis_list[0]

            return final_result

        except TooLongTextError:
            pass
        except json.JSONDecodeError:
            return

    lvl += 1
    return await ai_fetch_4_summarize(sem, conversation_data, lvl=lvl, client=client)


async def bulk_ai_fetch_4_summarize(sem):
    step_2_target = str(STEP_2_TICKETS_TARGET) + "_OK"
    step_4_target = STEP_4_TICKETS_TARGET

    os.makedirs(str(step_4_target), exist_ok=True)

    all_files = set(os.listdir(step_2_target))
    pre_processed = set(os.listdir(step_4_target))

    files_to_process = list(all_files - pre_processed)

    tasks = pending = {}
    async with AIClient() as client:
        for file_name in files_to_process:
            with open(f"{step_2_target}/{file_name}") as file:
                ticket_data = json.load(file)
                tasks[
                    asyncio.create_task(ai_fetch_4_summarize(sem, ticket_data["conversations"], client=client))
                ] = ticket_data

        while pending:
            done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                task_result = done_task.result()
                if not task_result:
                    continue
                ticket_data = tasks[done_task]
                with open(f"{step_4_target / ticket_data["ticket_id"]}.json", "w") as file:
                    json.dump(task_result, file, ensure_ascii=False, indent=4)
