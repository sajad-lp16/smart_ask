import asyncio
from typing import Any

from typing_extensions import Unpack
from elasticsearch.exceptions import NotFoundError
from core.log_config import elastic_logger as logger
from data_source.zammad.update_tickets import add_tickets_to_ai_source

from elastic.clients import get_async_elastic_client
from core.config import ELASTIC_SUMMARY_INDEX_NAME
from elastic.query_factory import query_builder
from elastic.exceptions import (
    RelatedTicketIDNotFoundException,
    TicketsNotFoundException
)


class ElasticQueryManager:
    UNCLEAR_SUMMARY_QUERY_MESSAGE = ("I know you are requesting a summary, but I it's unclear for me."
                                     " Please make a change to your request and try again.")
    MISSING_SUMMARY_QUERY_MESSAGE = ("Working on it! 🤖 This ticket isn’t in my system yet, but I’ll grab it for you. "
                                     "Please ask me again in 2 minutes—thanks for waiting! 🙏")
    BOT_UNDER_MAINTENANCE_MESSAGE = "Sorry, The bot is under maintenance please try again later."
    REFERENCE_ARGS_ARE_NOT_FOUND = "Sorry, I couldn't find information based on provided arguments."
    BROAD_ERROR_MESSAGE = "An unexpected error occurred while processing your request. Please try again later."

    @classmethod
    async def get_related_elastic_hits(cls, **kwargs) -> str | list[dict[str, Any]]:

        async with get_async_elastic_client() as elastic_client:
            query = query_builder(**kwargs)
            try:
                response = await elastic_client.search(index=ELASTIC_SUMMARY_INDEX_NAME, body=query)
                hits = response["hits"]["hits"]
                if not hits:
                    logger.warning(f"No tickets found matching query for {kwargs}")
                    if kwargs["ticket_ids"]:
                        raise RelatedTicketIDNotFoundException
                    raise TicketsNotFoundException
                return hits

            except NotFoundError as err:
                logger.warning(err)
                return cls.BOT_UNDER_MAINTENANCE_MESSAGE
            except TicketsNotFoundException:
                return cls.REFERENCE_ARGS_ARE_NOT_FOUND
            except RelatedTicketIDNotFoundException:
                _ = asyncio.create_task(add_tickets_to_ai_source(kwargs["ticket_ids"]))
                return cls.MISSING_SUMMARY_QUERY_MESSAGE
            except Exception as err:
                logger.warning(err)
                return cls.BROAD_ERROR_MESSAGE
            finally:
                await elastic_client.close()

    @classmethod
    async def query_elastic_based_on_args(
            cls, **kwargs: Unpack[dict[str: list[str]]]
    ) -> str | list[str] | list[dict]:

        if not any(kwargs.values()):
            return cls.UNCLEAR_SUMMARY_QUERY_MESSAGE

        hits = await cls.get_related_elastic_hits(**kwargs)
        if isinstance(hits, str):
            return hits

        all_s = []
        for hit in hits:
            all_s.append(f"### Ticket ID {hit['_id']}\n\n" + hit["_source"]["summary"] + "\n---\n")

        logger.info(f"Successfully processed {len(all_s)} summaries")
        return all_s
