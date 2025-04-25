import copy
import asyncio

from elasticsearch.exceptions import NotFoundError
from typing import List, Optional, Union
from core.log_config import elastic_logger as logger
from data_source.zammad.update_tickets import add_tickets_to_ai_source

from elastic.clients import get_async_elastic_client
from config import ELASTIC_SUMMARY_INDEX_NAME


class TicketsNotFoundException(BaseException):
    pass


class RelatedTicketIDNotFoundException(BaseException):
    pass


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


async def query_elastic(
        ticket_ids: list[str] | None = None,
        emails: list[str] | None = None,
        person_ids: list[str] | None = None,
        deal_ids: list[str] | None = None,
        return_hits: bool = False
) -> str | list[str] | list[dict]:
    if not any([ticket_ids, emails, person_ids, deal_ids]):
        return "I know you are requesting a summary, but I don't understand what you mean. Please make a change to your request and try again."

    async with get_async_elastic_client() as elastic_client:
        query = query_builder(ticket_ids, emails, person_ids, deal_ids)

        try:
            response = await elastic_client.search(index=ELASTIC_SUMMARY_INDEX_NAME, body=query)
            hits = response["hits"]["hits"]
            if not hits:
                logger.warning(
                    f"No tickets found matching query ticket_ids={ticket_ids},"
                    f" emails={emails}, person_ids={person_ids}, deal_ids={deal_ids}")
                if ticket_ids:
                    raise RelatedTicketIDNotFoundException
                raise TicketsNotFoundException

            if return_hits:
                return prepare_llama_source(hits)

            all_s = []
            for hit in hits:
                all_s.append(f"### Ticket ID {hit['_id']}\n\n" + hit["_source"]["summary"] + "\n---\n")

            logger.info(f"Successfully processed {len(all_s)} summaries")
            return all_s

        except NotFoundError as err:
            return "Sorry, The bot is under maintenance please try again later."
        except TicketsNotFoundException:
            return "Sorry, I couldn't find tickets based on your message"
        except RelatedTicketIDNotFoundException:
            asyncio.create_task(add_tickets_to_ai_source(ticket_ids))
            return "Working on it! 🤖 This ticket isn’t in my system yet, but I’ll grab it for you. Please ask me again in 2 minutes—thanks for waiting! 🙏"
        except Exception as err:
            return "An unexpected error occurred while processing your request. Please try again later."
        finally:
            await elastic_client.close()
            logger.debug("Elasticsearch client closed")
