import os
import json
import asyncio
from asyncio import Semaphore

from core import BASE_DIR
from ai.generate_qa import ai_fetch_for_qa
from ai.components.ai_clients import AIClient
from ai.components.prompts import FORUM_QA_PROMPT
from data_source.forum.parsing.topic_parser import json_topic_2_conversation
from elastic.ingest_to_elastic import ingest_documents
from elastic.delete_from_elastic import delete_llama_documents_by_source
from data_source.forum.prepare_to_ingest import qa_topic_2_llama_index_document


async def bulk_ai_fetch_for_qa(sem, topic_conversations: dict[str, str]):
    tasks = pending = {}
    async with AIClient() as client:
        for topic_id, conversation in topic_conversations.items():
            task = asyncio.create_task(ai_fetch_for_qa(sem, FORUM_QA_PROMPT, conversation, client=client))
            tasks[task] = topic_id

        successful_fetch = []

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                task_result = done_task.result()
                if not task_result:
                    continue
                topic_id = tasks[done_task]
                successful_fetch.append(topic_id)
                ready_docs = qa_topic_2_llama_index_document(task_result, topic_id)

                await delete_llama_documents_by_source("forum", topic_id)
                await ingest_documents(ready_docs)
        return successful_fetch


async def generate_qa_for_all_forum_topics():
    sem = Semaphore(10)
    forum_source = str(BASE_DIR / "data_source" / "forum" / "source")

    topics_conversation = {}

    all_files = set(os.listdir(forum_source))
    for file_name in all_files:
        with open(f"{forum_source}/{file_name}") as file:
            topic_id = file_name.split(".")[0]
            topic_json = json.load(file)
            topics_conversation[topic_id] = json_topic_2_conversation(topic_json)
    await bulk_ai_fetch_for_qa(sem, topics_conversation)
