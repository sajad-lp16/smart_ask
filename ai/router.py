from llama_index.core import VectorStoreIndex

from ai.llama_index_clients import VectorStoreEngine
from elastic.clients import ElasticVectorStore
from prompts import ROUTER_PROMPT

async def get_route(prompt):
    async with VectorStoreEngine() as vector_store:
        response = await query_engine.aquery(prompt)
        t_ids = [node.metadata.get("ticket_id") for node in response.source_nodes]
        reference_ids = list(filter(lambda t_id: t_id, t_ids))

        reference_str = "**reference_ticket**:\n"
        for reference_id in reference_ids:
            reference_str += f"- {ZAMMAD_TICKET_PREFIX + reference_id}\n"

        return f"{response}\n\n" + reference_str