import os
import json
import asyncio
from asyncio import Semaphore

from ai.utils.scripts import get_chunks
from ai.utils.ai_clients import CustomAsyncOpenAI, AIClient
from ai.utils.fetch import fetch_ai_client
from core.log_config import ai_logger
from core import (
    STEP_2_TICKETS_TARGET,
)

from ai.utils.prompts import (
    QA_PROMPT,
    QA_COMBINATION_PROMPT
)
from elastic.ingest_2_elastic import ingest_qa_documents
from elastic.delete_from_elastic import delete_qa_documents


async def ai_fetch_4_qa(sem: Semaphore, conversation_data: str, client: CustomAsyncOpenAI) -> list:
    async with sem:
        conversations = get_chunks(conversation_data)
        analysis_list = []

        tasks = [
            asyncio.create_task(fetch_ai_client(QA_PROMPT % conversation, client)) for conversation in conversations
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for d_task in done:
            if d_task.exception():
                [p.cancel() for p in pending]
                ai_logger.error(d_task.exception())
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


async def bulk_ai_fetch_4_qa(sem, tickets_conversations: dict[int, str]) -> list[int]:
    tasks = pending = {}
    async with AIClient() as client:
        for ticket_id, conversations in tickets_conversations.items():
            task = asyncio.create_task(ai_fetch_4_qa(sem, conversations, client=client))
            tasks[task] = ticket_id

        successful_fetch = []
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                task_result = done_task.result()
                ticket_id = tasks[done_task]
                successful_fetch.append(ticket_id)
                if not task_result:
                    continue
                await delete_qa_documents(ticket_id)
                await ingest_qa_documents(task_result, ticket_id)
        return successful_fetch


async def generate_qa_for_all_tickets(sem):
    step_2_target = str(STEP_2_TICKETS_TARGET) + "_OK"

    tickets_conversations = {}

    all_files = set(os.listdir(step_2_target))
    for file_name in all_files:
        with open(f"{step_2_target}/{file_name}") as file:
            ticket_id = file_name.split(".")[0]
            ticket_data = json.load(file)
            tickets_conversations[ticket_id] = ticket_data["conversations"]
    await bulk_ai_fetch_4_qa(sem, tickets_conversations)
