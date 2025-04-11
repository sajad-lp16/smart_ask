import asyncio
import os
from decouple import config

from llama_index.core import VectorStoreIndex, Document

from ai.llama_index_clients import VectorStorageContext
from elastic.clients import get_async_elastic_client
from core import (
    STEP_3_TICKETS_TARGET,
    STEP_4_TICKETS_TARGET
)

os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_KEY", cast=str))

QA_INDEX_NAME = config("QA_INDEX_NAME", cast=str)
SUMMARY_INDEX_NAME = config("SUMMARY_INDEX_NAME", cast=str)
ELASTIC_URL = config("ELASTIC_URL", cast=str)


def qa_json_2_llama_index_document(json_data: dict, ticket_id: int):
    docs = []
    for item in json_data:
        docs.append(
            Document(text=item["problem"], metadata={"solution": item["solution"], "ticket_id": ticket_id})
        )
    return docs


async def ingest_qa_documents(json_data: dict, ticket_id: int):
    ready_documents = qa_json_2_llama_index_document(json_data, ticket_id)

    async with VectorStorageContext(index="qa") as storage_context:
        try:
            VectorStoreIndex.from_documents(
                ready_documents, storage_context=storage_context
            )
            print(f"{len(ready_documents)} documents ingested")
            return True

        except Exception as e:
            print(f"Error during ingestion: {str(e)}")
            return False


async def ingest_summary_documents(ready_documents: list[dict], es_client=None) -> None:
    async def _ingest(doc_id, doc_body, _es_client):
        try:
            response = await _es_client.index(
                index=SUMMARY_INDEX_NAME,
                id=doc_id,
                body=doc_body
            )
            print(f"Indexed {doc_id}: {response['result']}")
        except Exception as e:
            print(f"Error during ingestion: {str(e)}")

    if es_client is None:
        es_client = get_async_elastic_client()

    tasks = []
    for doc in ready_documents:
        tasks.append(asyncio.create_task(_ingest(doc["ticket_id"], doc["body"], es_client)))

    await asyncio.wait(tasks)


async def ingest_all_documents():
    qa_target = str(STEP_3_TICKETS_TARGET) + "_OK"
    summary_target = str(STEP_4_TICKETS_TARGET) + "_OK"

    qa_files = set(os.listdir(qa_target))
    summary_files = set(os.listdir(summary_target))
