import os
import json
import time

import aiohttp
import asyncio
import requests
from asyncio import Semaphore

from decouple import config

from core import STEP_1_TICKETS_TARGET

ZAMMAD_BASE_URL = config("ZAMMAD_BASE_URL", cast=str)
ZAMMAD_TICKET_URL = ZAMMAD_BASE_URL + "/tickets?per_page=20&page={page_number}"
ZAMMAD_ARTICLES_URL = ZAMMAD_BASE_URL + "/ticket_articles/by_ticket/{ticket_id}"
ZAMMAD_ARTICLES_URLQ = ZAMMAD_BASE_URL + "/tickets/search?sort_by=id&order_by=asc&per_page=10"

HEADERS = {"Authorization": f'Bearer {config("ZAMMAD_API_KEY")}'}


def find_last_page():
    def _fetch(page):
        r = requests.get(ZAMMAD_TICKET_URL.format(page_number=page), headers=HEADERS)
        r.raise_for_status()

        return len(r.json()) > 0

    low = 1
    high = 1

    while True:
        data_exists = _fetch(high)
        if not data_exists:
            break

        low = high
        high *= 2

    last_valid_page = low
    while low <= high:
        mid = (low + high) // 2
        data_exists = _fetch(mid)
        if data_exists:
            last_valid_page = mid
            low = mid + 1
        else:
            high = mid - 1
    print(f"last page found was {last_valid_page}")
    return last_valid_page


async def fetch_api(session, url):
    async with session.get(url, headers=HEADERS) as response:
        return await response.json()


async def fetch_articles(session, ticket_id):
    # url = ZAMMAD_ARTICLES_URL.format(ticket_id=ticket_id)
    url = ZAMMAD_ARTICLES_URL
    return await fetch_api(session, url)


async def get_page_articles(sem, session, page):
    async with sem:
        url = ZAMMAD_TICKET_URL.format(page_number=page)

        tickets = await fetch_api(session, url)
        tasks = []
        for ticket in tickets:
            ticket_id = ticket["id"]
            tasks.append(asyncio.create_task(fetch_articles(session, ticket_id)))

        articles = {}
        done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        for task in done:
            article_set = task.result()
            print(article_set)
            articles[article_set[0]["ticket_id"]] = article_set

        print(articles)
        return articles


async def fetch_all_articles(sem: Semaphore):
    # last_page = find_last_page()
    step_1_target = STEP_1_TICKETS_TARGET

    os.makedirs(str(step_1_target), exist_ok=True)

    async with aiohttp.ClientSession() as session:
        # tasks = [asyncio.create_task(get_page_articles(sem, session, page)) for page in range(1, last_page + 1)]
        tasks = [asyncio.create_task(get_page_articles(sem, session, page)) for page in range(400, 401)]
        for done_task in asyncio.as_completed(tasks):
            task_data = await done_task
            for ticket_id, ticket_articles in task_data.items():
                if not ticket_articles:
                    continue
                
                # with open(f"{step_1_target}/{ticket_id}.json", "w") as file:
                #     json.dump(ticket_articles, file, indent=4, ensure_ascii=False)



if __name__ == "__main__":
    sem = Semaphore(100)
    asyncio.run(fetch_all_articles(sem))
