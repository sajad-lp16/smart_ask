import os
import asyncio

from llama_index.core import VectorStoreIndex, Document

from ai.utils.llama_index_clients import VectorStorageContext
from elastic.clients import get_async_elastic_client
from core.log_config import elastic_logger as logger
from config import (
    ELASTIC_SUMMARY_INDEX_NAME,
    OPENAI_KEY
)

os.environ.setdefault("OPENAI_API_KEY", OPENAI_KEY)


def qa_json_2_llama_index_document(json_data: list[dict[str, str]], source_id: int):
    docs = []
    for item in json_data:
        docs.append(
            Document(text=item["problem"], metadata={"solution": item["solution"], "source_id": source_id, "source": "zammad"})
        )
    return docs


async def ingest_qa_documents(json_data: list[dict[str, str]], source_id: int):
    ready_documents = qa_json_2_llama_index_document(json_data, source_id)

    async with VectorStorageContext(index="qa") as storage_context:
        try:
            VectorStoreIndex.from_documents(
                ready_documents, storage_context=storage_context
            )
            logger.info(f"{len(ready_documents)} documents ingested to qa index")
            return True

        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
            return False


async def ingest_summary_documents(ready_documents: list[dict], es_client=None) -> None:
    async def _ingest(doc_id, doc_body, _es_client):
        try:
            response = await _es_client.index(
                index=ELASTIC_SUMMARY_INDEX_NAME,
                id=doc_id,
                body=doc_body
            )
            logger.info(f"Indexed {doc_id}: {response['result']}")
        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
        finally:
            await es_client.close()

    if es_client is None:
        es_client = get_async_elastic_client()

    tasks = []
    for doc in ready_documents:
        tasks.append(asyncio.create_task(_ingest(doc["source_id"], doc["body"], es_client)))

    await asyncio.wait(tasks)
