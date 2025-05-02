import os
import json
import asyncio
import aiohttp

from core.log_config import logging
from core import BASE_DIR
from core.config import (
    FORUM_HEADERS,
    FORUM_BASE_URL,
    FORUM_TOPIC_URL
)

logger = logging.getLogger()


async def find_last_page():
    async def _fetch(page):
        await asyncio.sleep(1)
        logger.info(f"Trying page {page}")
        async with session.get(f"{FORUM_BASE_URL}/latest.json?page={page}", headers=FORUM_HEADERS) as response:
            response.raise_for_status()
            json_response = await response.json()
            return len(json_response["topic_list"]["topics"]) > 0

    async with aiohttp.ClientSession() as session:
        low = 1
        high = 1

        while True:
            data_exists = await _fetch(high)
            if not data_exists:
                break

            low = high
            high *= 2

        last_valid_page = low
        while low <= high:
            mid = (low + high) // 2
            data_exists = await _fetch(mid)
            if data_exists:
                last_valid_page = mid
                low = mid + 1
            else:
                high = mid - 1
        return last_valid_page


async def get_topic_ids(sem, session, p):
    async with sem:
        url = f"{FORUM_BASE_URL}/latest.json?page={p}"
        logger.info(f"Fetching topics from page {p}")
        async with session.get(url, headers=FORUM_HEADERS) as response:
            response.raise_for_status()
            r = await response.json()
            topics = r["topic_list"]["topics"]
            return [topic["id"] for topic in topics]


async def get_topic(sem, session, topic_id):
    async with sem:
        url = f"{FORUM_TOPIC_URL}{topic_id}.json"
        try:
            await asyncio.sleep(1)
            async with session.get(url, headers=FORUM_HEADERS) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching topic {topic_id}: {str(e)}")


async def ai_fetch_all_topics():
    sem = asyncio.Semaphore(1)
    forum_source = str(BASE_DIR / "data_source" / "forum" / "source")

    os.makedirs(forum_source, exist_ok=True)

    fetched = set(int(num.split(".")[0]) for num in os.listdir(forum_source))

    logger.info(f"looking for the last page...")
    last_page = await find_last_page()
    logger.info(f"last page found was {last_page}")

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(get_topic_ids(sem, session, p)) for p in range(0, last_page + 1)]
        all_ids = await asyncio.gather(*tasks)

        topic_ids = set([id_ for sublist in all_ids for id_ in sublist])

        logger.info(f"Found {len(topic_ids)} topics")

        topic_ids = topic_ids - fetched

        topic_tasks = pending = {asyncio.create_task(get_topic(sem, session, tid)): tid for tid in topic_ids}
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for d_task in done:
                if d_task.exception():
                    raise d_task.exception()
                topic_id = topic_tasks[d_task]
                with open(f"{forum_source}/{topic_id}.json", "w") as file:
                    json.dump(d_task.result(), file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(ai_fetch_all_topics())
