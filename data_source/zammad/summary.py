import os
import json
import asyncio
from asyncio import Semaphore

from ai.components.ai_clients import AIClient
from ai.generate_summarize import ai_fetch_for_summarize

from elastic.ingest_to_elastic import ingest_raw_documents
from elastic.delete_from_elastic import delete_raw_documents_by_source
from core import STEP_2_TICKETS_TARGET
from core.utils.fetch_avicenna_ids import (
    get_person_ids_from_email,
    get_deal_ids_from_ticket_id
)


async def bulk_ai_fetch_for_summarize(sem, tickets_conversations: dict[int, str]):
    tasks = pending = {}
    async with AIClient() as client:
        for ticket_id, conversations in tickets_conversations.items():
            tasks[
                asyncio.create_task(ai_fetch_for_summarize(sem, prompt, conversations, client=client))
            ] = ticket_id

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
                deal_ids = results[1]
                task_result["person_ids"] = person_ids
                task_result["deal_ids"] = deal_ids

                await delete_raw_documents_by_source(ticket_id)
                await ingest_raw_documents([{"source_id": ticket_id, "body": task_result}])


async def generate_summary_for_all_tickets(sem: Semaphore):
    step_2_target = str(STEP_2_TICKETS_TARGET) + "_OK"

    tickets_conversations = {}

    all_files = set(os.listdir(step_2_target))
    for file_name in all_files:
        with open(f"{step_2_target}/{file_name}") as file:
            ticket_id = file_name.split(".")[0]
            ticket_data = json.load(file)
            tickets_conversations[ticket_id] = ticket_data["conversations"]
    await bulk_ai_fetch_for_summarize(sem, tickets_conversations)
