import os
import asyncio
from asyncio import Semaphore

from ai.genrate_md import ai_fetch_for_md
from ai.components.ai_clients import AIClient
from ai.components.prompts import AVICENNA_LEARN_PROMPT
from core.config import AVICENNA_BLOG_CRAWL_STORING_DIRECTORY
from core.log_config import ai_logger as logger
from elastic.delete_from_elastic import delete_llama_documents_by_source
from elastic.ingest_to_elastic import ingest_documents
from data_source.avicenna_blog.prepare_to_ingest import md_blog_doc_2_llama_index_document


async def bulk_ai_fetch_for_md(sem: Semaphore, doc_source: dict[str: str]) -> None:
    tasks = pending = {}
    async with AIClient() as client:
        for source_id, source_body in doc_source.items():
            task = asyncio.create_task(ai_fetch_for_md(sem, AVICENNA_LEARN_PROMPT, source_body, client=client))
            tasks[task] = source_id

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                if done_task.exception():
                    logger.exception(exception=done_task.exception())
                    continue

                task_result = done_task.result()
                source_id = tasks[done_task]

                ready_docs = md_blog_doc_2_llama_index_document(task_result, source_id)

                await delete_llama_documents_by_source("avicenna_blog", source_id)
                await ingest_documents([ready_docs])


async def process_all_avicenna_blog_source():
    sem = Semaphore(10)

    target_dir = AVICENNA_BLOG_CRAWL_STORING_DIRECTORY
    url_2_source_mapping = {}
    for filename in os.listdir(target_dir):
        with open(target_dir + filename) as file:
            url_2_source_mapping[filename] = file.read()

    await bulk_ai_fetch_for_md(sem, url_2_source_mapping)


if __name__ == "__main__":
    asyncio.run(process_all_avicenna_blog_source())
