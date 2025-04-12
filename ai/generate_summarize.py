import os
import json
import asyncio
from asyncio import Semaphore

from core.log_config import ai_logger
from ai.utils.scripts import get_chunks
from ai.utils.ai_clients import CustomAsyncOpenAI, AIClient
from ai.utils.fetch import fetch_ai_client
from elastic.ingest_2_elastic import ingest_summary_documents
from elastic.delete_from_elastic import delete_summary_documents
from ai.utils.prompts import (
    SUMMARIZE_PROMPT,
    SUMMARIZE_COMBINATION_PROMPT
)
from core.utils.fetch_avicenna_ids import (
    get_person_ids_from_email,
    get_deal_ids_from_ticket_id
)
from core import (
    STEP_2_TICKETS_TARGET,
)


async def ai_fetch_4_summarize(sem: Semaphore, conversation_data: str, client: CustomAsyncOpenAI) -> list:
    async with sem:
        conversations = get_chunks(conversation_data)
        analysis_list = []

        tasks = [
            asyncio.create_task(
                fetch_ai_client(prompt=SUMMARIZE_PROMPT % conversation, client=client)
            ) for conversation in conversations
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for d_task in done:
            if d_task.exception():
                ai_logger.error(d_task.exception())
                [p.cancel() for p in pending]
                raise d_task.exception()

            task_result = d_task.result()

            analysis_list.append(task_result)

        if len(analysis_list) > 1:
            final_result = await fetch_ai_client(
                SUMMARIZE_COMBINATION_PROMPT % json.dumps(analysis_list), client=client
            )
        else:
            final_result = analysis_list[0]

        return final_result


async def bulk_ai_fetch_4_summarize(sem, tickets_conversations: dict[int, str]) -> list[int]:
    tasks = pending = {}
    async with AIClient() as client:
        for ticket_id, conversations in tickets_conversations.items():
            tasks[
                asyncio.create_task(ai_fetch_4_summarize(sem, conversations, client=client))
            ] = ticket_id

        successful_fetch = []
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                task_result = done_task.result()
                if not task_result:
                    continue
                ticket_id = tasks[done_task]
                emails = task_result["emails"]
                id_tasks = [
                    asyncio.create_task(get_person_ids_from_email(emails)),
                    asyncio.create_task(get_deal_ids_from_ticket_id([ticket_id])),
                ]
                results = await asyncio.gather(*id_tasks)
                person_ids = results[0]
                '''
                THIS NEEDS MODIFICATION !!!!!!!!!!!
                deal_ids = results[1] WHEN CONNECTED TO AVICENNA
                '''
                deal_ids = results[1]
                task_result["person_ids"] = person_ids
                task_result["deal_ids"] = deal_ids

                await delete_summary_documents(ticket_id)
                await ingest_summary_documents([{"ticket_id": ticket_id, "body": task_result}])
                successful_fetch.append(ticket_id)
        return successful_fetch


async def generate_summary_for_all_tickets(sem: Semaphore):
    step_2_target = str(STEP_2_TICKETS_TARGET) + "_OK"

    tickets_conversations = {}

    all_files = set(os.listdir(step_2_target))
    for file_name in all_files:
        with open(f"{step_2_target}/{file_name}") as file:
            ticket_id = file_name.split(".")[0]
            ticket_data = json.load(file)
            tickets_conversations[ticket_id] = ticket_data["conversations"]
    await bulk_ai_fetch_4_summarize(sem, tickets_conversations)
