from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter


def md_learn_doc_2_llama_index_document(document_content, source_id: str):
    text_splitter = SentenceSplitter(
        chunk_size=200,
        chunk_overlap=50
    )
    nodes = text_splitter.get_nodes_from_text(document_content)

    documents = []
    for index, node in enumerate(nodes):
        document = Document(
            text=node.text,
            metadata={
                "solution": "",
                "source_id": source_id,
                "source": "avicenna_learn",
                "chunk_index": index,
                "total_chunks": len(nodes)
            }
        )
        documents.append(document)

    return documents
