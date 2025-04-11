from elastic.clients import get_async_elastic_client

from constants import (
    ELASTIC_QA_INDEX_NAME,
    ELASTIC_SUMMARY_INDEX_NAME
)


async def delete_qa_documents(ticket_id: int):
    try:
        async with get_async_elastic_client() as es_client:
            response = await es_client.delete_by_query(
                index=ELASTIC_QA_INDEX_NAME,
                body={
                    "query": {
                        "term": {
                            "metadata.ticket_id": ticket_id
                        }
                    }
                }
            )
            print(f"Deleted {response['deleted']} QA documents for ticket {ticket_id}")
            return True
    except Exception as err:
        return False


async def delete_summary_documents(ticket_id: int):
    try:
        async with get_async_elastic_client() as es_client:
            await es_client.delete(
                index=ELASTIC_SUMMARY_INDEX_NAME,
                id=str(ticket_id)
            )
            print(f"Deleted summary document for ticket {ticket_id}")
            return True
    except Exception as err:
        return False
