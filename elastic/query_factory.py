import copy
import asyncio

from elasticsearch.exceptions import NotFoundError
from typing import List, Optional, Union
from core.log_config import elastic_logger as logger
from data_source.zammad.update_tickets import add_tickets_to_ai_source

from elastic.clients import get_async_elastic_client
from core.config import ELASTIC_SUMMARY_INDEX_NAME


def get_terms(key: str, value: Union[List, str]) -> dict:
    """Create a terms query for Elasticsearch."""
    return {
        "terms": {
            key: value
        }
    }


def get_email_term(value: Union[List, str]) -> dict:
    """Create a terms query for email field."""
    return {
        "terms": {
            "emails.keyword": value
        }
    }


def get_ids_term(ids: List[str]) -> dict:
    """Create an ids query for Elasticsearch."""
    return {
        "ids": {
            "values": ids
        }
    }


def query_builder(
        ticket_ids: Optional[List[str]] = None,
        emails: Optional[List[str]] = None,
        person_ids: Optional[List[str]] = None,
        deal_ids: Optional[List[str]] = None
) -> dict:
    """Build an Elasticsearch query based on provided parameters."""
    query = {
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        }
    }

    query_c = copy.deepcopy(query)

    if emails:
        query_c["query"]["bool"]["must"].append(get_email_term(emails))
    if person_ids:
        query_c["query"]["bool"]["must"].append(get_terms("person_ids", person_ids))
    if deal_ids:
        query_c["query"]["bool"]["must"].append(get_terms("deal_ids", deal_ids))
    if ticket_ids:
        query_c["query"]["bool"]["filter"].append(get_ids_term(ticket_ids))

    return query_c


def build_query_hint(
        ticket_ids: Optional[List[str]] = None,
        emails: Optional[List[str]] = None,
        person_ids: Optional[List[str]] = None,
        deal_ids: Optional[List[str]] = None
) -> str:
    """Build a human-readable query hint."""
    result = ""
    if ticket_ids:
        result += f"    - Ticket_IDs={str(ticket_ids)} "
    if emails:
        result += f"    - Emails={str(emails)} "
    if person_ids:
        result += f"    - Person_IDs={str(person_ids)} "
    if deal_ids:
        result += f"    - Deal_IDs={str(deal_ids)} "
    return result


def prepare_llama_source(hits: List[dict]) -> List[dict]:
    """Prepare Elasticsearch hits for Llama processing."""
    try:
        for hit in hits:
            hit["ticket_id"] = hit["_id"]
            del hit["_id"]
            hit.update(hit["_source"])
            del hit["_source"]

        logger.debug(f"Prepared {len(hits)} documents for Llama processing")
        return hits
    except Exception as e:
        logger.error(f"Error preparing Llama source: {str(e)}", exc_info=True)
        raise
