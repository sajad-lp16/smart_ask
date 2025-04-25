from llama_index.core import Document


def qa_ticket_2_llama_index_document(json_data: list[dict[str, str]], ticket_id: int):
    docs = []
    for item in json_data:
        docs.append(
            Document(
                text=item["problem"],
                metadata={"solution": item["solution"], "source_id": ticket_id, "source": "zammad"})
        )
    return docs
