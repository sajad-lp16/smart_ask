from elastic.clients import get_async_elastic_client

from config import (
    ELASTIC_QA_INDEX_NAME,
    ELASTIC_SUMMARY_INDEX_NAME
)


async def delete_qa_documents(source_id: int):
    try:
        async with get_async_elastic_client() as es_client:
            await es_client.delete_by_query(
                index=ELASTIC_QA_INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"metadata.source_id.keyword": source_id}},
                                {"term": {"metadata.source.keyword": "zammad"}}
                            ]
                        }
                    }
                }
            )
            return True
    except Exception as err:
        return False


async def delete_summary_documents(source_id: int):
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