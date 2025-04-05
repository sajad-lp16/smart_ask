import os
from contextlib import asynccontextmanager

from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI

from decouple import config

import uvicorn
from fastapi import FastAPI, Query

from elastic.clients import ElasticVectorStore

os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_KEY", cast=str))
QA_INDEX_NAME = config("QA_INDEX_NAME", cast=str)
ELASTIC_URL = config("ELASTIC_URL", cast=str)
ZAMMAD_TICKET_PREFIX = config("ZAMMAD_TICKET_PREFIX", cast=str)


async def query_documents(query_text: str, index: VectorStoreIndex):
    query_engine = index.as_query_engine()
    response = await query_engine.aquery(query_text)
    t_ids = [node.metadata.get("ticket_id") for node in response.source_nodes]
    reference_ids = list(filter(lambda t_id: t_id, t_ids))

    return {
        "question": query_text,
        "answer": str(response),
        "reference_ticket": [ZAMMAD_TICKET_PREFIX + reference_id for reference_id in reference_ids]
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with ElasticVectorStore() as vector_store:
        app.state.index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/support")
async def support(query: str = Query(..., description="The question to ask")):
    response = await query_documents(query, app.state.index)
    return response


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8089,
        loop="asyncio"
    )
