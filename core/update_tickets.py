import asyncio
from asyncio import Semaphore

from ai.generate_summarize import bulk_ai_fetch_4_summarize
from ai.generate_qa import bulk_ai_fetch_4_qa
from db.sql import get_tickets_for_processing
from core.log_config import update_tickets_logger as logger
from parsing.html_2_md import message_2_md_parser
from zammad.fetch import fetch_articles

async def _trigger_fetch_step(ticket_ids):
    logger.info(f"Fetching tickets: {ticket_ids}")
    return await fetch_articles(ticket_ids)


def _trigger_cleanup_step(tickets_articles):
    clean_tickets = {}
    for ticket_id, articles in tickets_articles:
        conversations = message_2_md_parser(articles)
        clean_tickets[ticket_id] = conversations
    return clean_tickets


async def process_tickets_beat_task():
    """
    Async function that fetches tickets from SQLite and processes them.
    """
    while True:
        try:
            tickets = get_tickets_for_processing()

            if not tickets:
                logger.info("No tickets to process")
            else:
                ticket_ids = [ticket["ticket_id"] for ticket in tickets]
                try:
                    semaphore = Semaphore(100)
                    logger.info(f"Processing ticket: {ticket_ids}")
                    tickets_articles = await _trigger_fetch_step(ticket_ids)
                    tickets_conversations = {}
                    for ticket_id, ticket_articles in tickets_articles.items():
                        tickets_conversations[ticket_id] = message_2_md_parser(ticket_articles)

                    analyze_tickets = [
                        asyncio.create_task(bulk_ai_fetch_4_qa(semaphore, tickets_conversations)),
                        asyncio.create_task(bulk_ai_fetch_4_summarize(semaphore, tickets_conversations)),
                    ]

                    await asyncio.gather(*analyze_tickets)

                    logger.info(f"Successfully processed ticket {ticket_ids}")

                except Exception as e:
                    logger.error(f"Error processing ticket {ticket_ids}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in process_tickets: {str(e)}")

        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(process_tickets_beat_task())
