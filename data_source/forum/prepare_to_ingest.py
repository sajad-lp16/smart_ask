from llama_index.core import Document


def qa_topic_2_llama_index_document(json_data: list[dict[str, str]], topic_id: int):
    docs = []
    for item in json_data:
        docs.append(
            Document(
                text=item["problem"],
                metadata={"solution": item["solution"], "source_id": topic_id, "source": "zammad"}
            )
        )
    return docs
