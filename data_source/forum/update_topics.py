import asyncio
from asyncio import Semaphore
from core.redis_service import redis_gateway
from data_source.forum.parsing.topic_parser import json_topic_2_conversation

from data_source.forum.qa import bulk_ai_fetch_for_qa
from core.log_config import update_tickets_logger as logger
from data_source.forum.fetch import get_topics_conversation


async def _trigger_fetch_step(sem, topic_ids):
    logger.info(f"Fetching topics: {topic_ids}")
    return await get_topics_conversation(sem, topic_ids)


def _trigger_cleanup_step(topic_conversations):
    clean_tickets = {}
    for topic_id, conversation_data in topic_conversations:
        conversations = json_topic_2_conversation(conversation_data)
        clean_tickets[topic_id] = conversations
    return clean_tickets


async def add_topics_to_ai_source(topic_ids):
    try:
        semaphore = Semaphore(100)
        logger.info(f"Processing ticket: {topic_ids}")
        topics_conversations = await _trigger_fetch_step(semaphore, topic_ids)

        not_fetched_topics = set(topic_ids) - set(topics_conversations.keys())
        await asyncio.create_task(redis_gateway.mark_completed("forum", not_fetched_topics))

        analyze_topics = [
            asyncio.create_task(bulk_ai_fetch_for_qa(semaphore, topics_conversations)),
        ]

        results = await asyncio.gather(*analyze_topics)
        qa_ok = results
        successful_process = list(set(qa_ok))

        await redis_gateway.mark_completed("forum", successful_process)

        logger.info(f"Successfully processed topics {qa_ok}")

    except Exception as e:
        logger.exception(f"Error processing topic {topic_ids}: {str(e)}", exc_info=True, stack_info=True)


async def process_topics_beat_task():
    while True:
        try:
            topics = await redis_gateway.get_pending_items("forum")
            if not topics:
                logger.info("No topics to process")
            else:
                await add_topics_to_ai_source(topics)

        except Exception as e:
            logger.error(f"Error in process_topics: {str(e)}")

        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(process_topics_beat_task())
