async def query_documents(query_text: str):
    routing_prompt = ROUTER_PROMPT % query_text
    target_source = llm.complete(routing_prompt).text.strip().replace("`", "")

    print(target_source)

    if target_source.startswith("question"):
        return await qa_query(query_text)

    elif target_source.startswith("summary"):
        _, ticket_id = target_source.split(" ")
        return await get_document_by_id(ticket_id)
