from llama_index.core import VectorStoreIndex, StorageContext

from elastic.clients import get_elasticsearch_store


class VectorStoreEngine:
    def __init__(self, index: str):
        self.elasticsearch_store = get_elasticsearch_store(index)

    async def __aenter__(self):
        index = VectorStoreIndex.from_vector_store(vector_store=self.elasticsearch_store)
        query_engine = index.as_query_engine()
        return query_engine

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elasticsearch_store.close()


class VectorStorageContext:
    def __init__(self, index: str):
        self.elasticsearch_store = get_elasticsearch_store(index)

    async def __aenter__(self):
        storage_context = StorageContext.from_defaults(vector_store=self.elasticsearch_store)
        return storage_context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elasticsearch_store.close()
