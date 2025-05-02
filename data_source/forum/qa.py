import os
import json
import asyncio
from asyncio import Semaphore

from core import STEP_2_TICKETS_TARGET
from ai.generate_qa import ai_fetch_for_qa
from ai.components.ai_clients import AIClient
from ai.components.prompts import ZAMMAD_QA_PROMPT
from elastic.ingest_to_elastic import ingest_documents
from elastic.delete_from_elastic import delete_llama_documents_by_source


async def bulk_ai_fetch_for_qa(sem, tickets_conversations: dict[int, str]):
    tasks = pending = {}
    async with AIClient() as client:
        for ticket_id, conversations in tickets_conversations.items():
            task = asyncio.create_task(ai_fetch_for_qa(sem, ZAMMAD_QA_PROMPT, conversations, client=client))
            tasks[task] = ticket_id

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                task_result = done_task.result()
                if not task_result:
                    continue
                ticket_id = tasks[done_task]
                await delete_llama_documents_by_source(ticket_id)
                await ingest_documents(task_result, ticket_id)


async def generate_qa_for_all_zammad_tickets(sem: Semaphore):
    step_2_target = str(STEP_2_TICKETS_TARGET) + "_OK"

    tickets_conversations = {}

    all_files = set(os.listdir(step_2_target))
    for file_name in all_files:
        with open(f"{step_2_target}/{file_name}") as file:
            ticket_id = file_name.split(".")[0]
            ticket_data = json.load(file)
            tickets_conversations[ticket_id] = ticket_data["conversations"]
    await bulk_ai_fetch_for_qa(sem, tickets_conversations)
