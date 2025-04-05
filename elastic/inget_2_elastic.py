import os
import json
import asyncio

from decouple import config

from llama_index.core import VectorStoreIndex, StorageContext, Document

from elastic.clients import ElasticVectorStore

os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_KEY", cast=str))

QA_INDEX_NAME = config("QA_INDEX_NAME", cast=str)
ELASTIC_URL = config("ELASTIC_URL", cast=str)


def json_2_llama_index_document(json_data: dict, ticket_id: int):
    docs = []
    for item in json_data:
        docs.append(
            Document(text=item["problem"], metadata={"solution": item["solution"], "ticket_id": ticket_id})
        )
    return docs


async def ingest_documents(ready_documents):
    async with ElasticVectorStore() as vector_store:
        try:
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            VectorStoreIndex.from_documents(
                ready_documents, storage_context=storage_context
            )
            return True

        except Exception as e:
            print(f"Error during ingestion: {str(e)}")
            return False


if __name__ == "__main__":
    dir_name = input("dir name >>> ")
    files = os.listdir(dir_name)

    documents = []

    for file in files:
        with open(f"{dir_name}/{file}") as f:
            data = json.load(f)
            file_name = int(file.split(".json")[0])
            documents.extend(json_2_llama_index_document(data, file_name))

    asyncio.run(ingest_documents(documents))
