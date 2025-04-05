from ai.llama_index_clients import VectorStoreEngine


async def qa_query(query_text):
    async with VectorStoreEngine() as query_engine:
        response = await query_engine.aquery(query_text)
        t_ids = [node.metadata.get("ticket_id") for node in response.source_nodes]
        reference_ids = list(filter(lambda t_id: t_id, t_ids))

        reference_str = "**reference_ticket**:\n"
        for reference_id in reference_ids:
            reference_str += f"- {ZAMMAD_TICKET_PREFIX + reference_id}\n"

        return f"{response}\n\n" + reference_str
