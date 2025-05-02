import os
import json

import aiohttp
import asyncio
import logging
from asyncio import Semaphore
from aiohttp import ClientSession

from core import STEP_1_TICKETS_TARGET
from core.log_config import update_tickets_logger
from core.config import (
    ZAMMAD_TICKET_URL,
    ZAMMAD_HEADERS,
    ZAMMAD_ARTICLES_URL
)

logger = logging.getLogger()


async def find_last_page():
    async def _fetch(page):
        await asyncio.sleep(1)
        logger.info(f"Trying page {page}")
        async with session.get(ZAMMAD_TICKET_URL.format(page_number=page), headers=ZAMMAD_HEADERS) as response:
            response.raise_for_status()
            json_response = await response.json()
            return len(json_response) > 0

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


async def fetch_api(url: str, session: ClientSession) -> dict | None:
    for _ in range(3):
        try:
            async with session.get(url, headers=ZAMMAD_HEADERS) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch data. Status: {response.status}")
                return await response.json()
        except aiohttp.ServerTimeoutError:
            continue
        except aiohttp.ClientError as err:
            raise err


async def fetch_articles(ticket_ids, session: ClientSession = None):
    async def _trigger_fetch(_session):
        tasks = {}
        articles = {}
        for ticket_id in ticket_ids:
            url = ZAMMAD_ARTICLES_URL.format(ticket_id=ticket_id)
            tasks[asyncio.create_task(fetch_api(url, _session))] = ticket_id

        done, _ = await asyncio.wait(tasks.keys())
        for done_task in done:
            if done_task.exception() is not None:
                update_tickets_logger.error(done_task.exception())
                continue
            ticket_id = tasks[done_task]
            articles[ticket_id] = done_task.result()

        return articles

    if session is not None:
        return await _trigger_fetch(session)
    async with ClientSession() as new_session:
        return await _trigger_fetch(new_session)


async def get_page_articles(sem, session, page):
    async with sem:
        logger.info(f"Fetching page {page} Articles.")
        url = ZAMMAD_TICKET_URL.format(page_number=page)

        tickets = await fetch_api(url, session)
        ticket_ids = [ticket["id"] for ticket in tickets]
        logger.info(f"Page {page} Articles, were fetched successfully.")
        return await fetch_articles(ticket_ids, session)


async def fetch_all_articles(sem: Semaphore):
    logger.info(f"looking for the last page...")
    last_page = await find_last_page()
    logger.info(f"last page found was {last_page}")

    step_1_target = STEP_1_TICKETS_TARGET

    os.makedirs(str(step_1_target), exist_ok=True)

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(get_page_articles(sem, session, page)) for page in range(1, last_page + 1)]
        for done_task in asyncio.as_completed(tasks):
            task_data = await done_task
            for ticket_id, ticket_articles in task_data.items():
                if not ticket_articles:
                    continue

                with open(f"{step_1_target}/{ticket_id}.json", "w") as file:
                    json.dump(ticket_articles, file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    semaphore = Semaphore(100)
    asyncio.run(fetch_all_articles(semaphore))
