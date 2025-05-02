from llama_index.core import Document


def md_blog_doc_2_llama_index_document(document_content, source_id: str):
    document = Document(
        text=document_content,
        metadata={"solution": "", "source_id": source_id, "source": "avicenna_learn"}
    )
    return document
