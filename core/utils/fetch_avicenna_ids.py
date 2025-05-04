import json
import asyncio

import aiohttp
from aiohttp import ClientSession

from core import BASE_DIR


async def get_person_ids_from_email(emails: list[str]) -> list[int]:
    # async with ClientSession() as session:
    #     ...
    #     # TODO Avicenna fetch
    #

    # TODO REMOVE ASAP
    persons = []
    with open(BASE_DIR / "core" / "utils" / "email_person_mapper.json") as file:
        cache_data = json.load(file)
        for email in emails:
            if email in cache_data:
                persons.append(cache_data.get(email))
    return persons


async def get_deal_ids_from_ticket_id(ticket_ids: list[int | str]) -> list[int]:
    # async with ClientSession() as session:
    #     ...
    #     # TODO Avicenna fetch
    #

    # TODO REMOVE ASAP
    deals = []
    with open(BASE_DIR / "core" / "utils" / "ticket_deal_mapper.json") as file:
        cache_data = json.load(file)
        for ticket_id in ticket_ids:
            _ticket_id = str(ticket_id)
            if _ticket_id in cache_data:
                deals.append(cache_data.get(_ticket_id))
    return deals
