from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter


def md_learn_doc_2_llama_index_document(document_content, source_id: str) -> list[Document]:
    text_splitter = SentenceSplitter(
        chunk_size=200,
        chunk_overlap=50
    )
    split_text = text_splitter.split_text(document_content)
    documents = []
    for index, text in enumerate(split_text):
        document = Document(
            text=text,
            metadata={
                "solution": "",
                "source_id": source_id,
                "source": "avicenna_learn",
                "chunk_index": index,
                "total_chunks": len(split_text)
            }
        )
        documents.append(document)

    return documents
