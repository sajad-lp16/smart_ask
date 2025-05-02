from elastic.clients import get_async_elastic_client

from core.config import (
    ELASTIC_QA_INDEX_NAME,
    ELASTIC_SUMMARY_INDEX_NAME
)


async def delete_llama_documents_by_source(source: str, source_id: int | str) -> bool:
    """
    At the moment MD and QA docs are indexed in one elastic index,
    If this changed in future then index arg should be configured dynamically.
    """
    try:
        async with get_async_elastic_client() as es_client:
            await es_client.delete_by_query(
                index=ELASTIC_QA_INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"metadata.source_id.keyword": source_id}},
                                {"term": {"metadata.source.keyword": source}}
                            ]
                        }
                    }
                }
            )
            return True
    except Exception as err:
        return False


async def delete_raw_documents_by_source(source_id: int) -> bool:
    try:
        async with get_async_elastic_client() as es_client:
            await es_client.delete(
                index=ELASTIC_SUMMARY_INDEX_NAME,
                id=str(source_id)
            )
            print(f"Deleted summary document for ticket {source_id}")
            return True
    except Exception as err:
        return False