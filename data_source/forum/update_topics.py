import asyncio
from asyncio import Semaphore
from core.redis_service import redis_gateway

from data_source.forum.qa import bulk_ai_fetch_for_qa
from core.log_config import update_tickets_logger as logger
from data_source.zammad.fetch import fetch_articles


async def _trigger_fetch_step(topic_ids):
    logger.info(f"Fetching tickets: {ticket_ids}")
    return await fetch_articles(ticket_ids)


def _trigger_cleanup_step(tickets_articles):
    clean_tickets = {}
    for ticket_id, articles in tickets_articles:
        conversations = message_2_md_parser(articles)
        clean_tickets[ticket_id] = conversations
    return clean_tickets


async def add_tickets_to_ai_source(ticket_ids):
    try:
        semaphore = Semaphore(100)
        logger.info(f"Processing ticket: {ticket_ids}")
        tickets_articles = await _trigger_fetch_step(ticket_ids)
        tickets_conversations = {}
        for ticket_id, ticket_articles in tickets_articles.items():
            tickets_conversations[ticket_id] = message_2_md_parser(ticket_articles)

        analyze_tickets = [
            asyncio.create_task(bulk_ai_fetch_for_qa(semaphore, tickets_conversations)),
            asyncio.create_task(bulk_ai_fetch_for_summarize(semaphore, tickets_conversations)),
        ]

        results = await asyncio.gather(*analyze_tickets)
        qa_ok, summary_ok = results
        successful_process = list(set(qa_ok) & set(summary_ok))
        redis_gateway.mark_completed("zammad", successful_process)

        logger.info(f"Successfully processed ticket {list(tickets_articles.keys())}")

    except Exception as e:
        logger.error(f"Error processing ticket {ticket_ids}: {str(e)}")


async def process_tickets_beat_task():
    """
    Async function that fetches tickets from SQLite and processes them.
    """
    while True:
        try:
            tickets = redis_gateway.get_pending_items("zammad")
            if not tickets:
                logger.info("No tickets to process")
            else:
                await add_tickets_to_ai_source(tickets)

        except Exception as e:
            logger.error(f"Error in process_tickets: {str(e)}")

        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(process_tickets_beat_task())
