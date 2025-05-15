from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.core.chat_engine import (
    SimpleChatEngine,
    CondenseQuestionChatEngine,
)
from llama_index.core.postprocessor.types import BaseNodePostprocessor

from elastic.clients import get_elasticsearch_store


class FullContextChatEngine:
    def __init__(
            self,
            index: str,
            response_synthesizer=None,
            similarity_top_k=5,
            memory=None,
            node_postprocessors: list[BaseNodePostprocessor] = None
    ):
        self.elasticsearch_store = get_elasticsearch_store(index)
        self.memory = memory
        self.query_engine_config = {
            "response_synthesizer": response_synthesizer,
            "similarity_top_k": similarity_top_k,
            "node_postprocessors": node_postprocessors or []
        }

    async def __aenter__(self) -> CondenseQuestionChatEngine:
        index = VectorStoreIndex.from_vector_store(vector_store=self.elasticsearch_store)
        query_engine = index.as_query_engine(**self.query_engine_config)
        chat_engine = CondenseQuestionChatEngine.from_defaults(query_engine=query_engine, memory=self.memory)

        return chat_engine

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elasticsearch_store.close()


class ContextAwareChatEngine:
    def __init__(
            self,
            elastic_hits=None,
            similarity_top_k=5,
            memory=None,
            response_synthesizer=None
    ):
        self.query_engine_config = {"response_synthesizer": response_synthesizer, "similarity_top_k": similarity_top_k}
        self.elastic_hits = elastic_hits
        self.memory = memory

    async def __aenter__(self):
        docs = []
        if self.elastic_hits:
            for item in self.elastic_hits:
                docs.append(
                    Document(
                        metadata={
                            "ticket_id": item["_id"],
                            "person_ids": item["_source"]["person_ids"],
                            "deal_ids": item["_source"]["deal_ids"],
                        },
                        text=item["_source"]["summary"]
                    )
                )
        index = VectorStoreIndex.from_documents(docs)
        query_engine = index.as_query_engine(**self.query_engine_config)
        chat_engine = CondenseQuestionChatEngine.from_defaults(query_engine=query_engine, memory=self.memory)

        return chat_engine

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class BasicChatEngine:
    def __init__(
            self,
            memory=None
    ):
        self.memory = memory

    async def __aenter__(self) -> SimpleChatEngine:
        chat_engine = SimpleChatEngine.from_defaults(memory=self.memory)
        return chat_engine

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class VectorStorageContext:
    def __init__(self, index: str):
        self.elasticsearch_store = get_elasticsearch_store(index)

    async def __aenter__(self) -> StorageContext:
        storage_context = StorageContext.from_defaults(vector_store=self.elasticsearch_store)
        return storage_context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elasticsearch_store.close()
