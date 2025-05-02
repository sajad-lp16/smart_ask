from llama_index.core import Document


def md_learn_doc_2_llama_index_document(document_content, source_id: str) -> Document:
    document = Document(
        text=document_content,
        metadata={"solution": "", "source_id": source_id, "source": "avicenna_blog"}
    )
    return document
