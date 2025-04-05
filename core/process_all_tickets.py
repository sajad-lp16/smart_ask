import os
import shutil

import asyncio
from asyncio import Semaphore

from ai.generate_qa import bulk_ai_fetch_4_qa
from ai.generae_summarize import bulk_ai_fetch_4_summarize
from core import (
    STEP_1_TICKETS_TARGET,
    STEP_2_TICKETS_TARGET,
    STEP_3_TICKETS_TARGET,
    STEP_4_TICKETS_TARGET,
)
from zammad.fetch import fetch_all_articles
from parsing.html_2_md import parse_all_tickets_md


def get_step_directory(step):
    step_2_target = {
        "step_1": STEP_1_TICKETS_TARGET,
        "step_2": STEP_2_TICKETS_TARGET,
        "step_3": STEP_3_TICKETS_TARGET,
        "step_4": STEP_4_TICKETS_TARGET,
    }
    return step_2_target[step]


def get_step_action(step):
    step_2_action = {
        "step_1": fetch_all_articles,
        "step_2": parse_all_tickets_md,
        "step_3": bulk_ai_fetch_4_qa,
        "step_4": bulk_ai_fetch_4_summarize,
    }

    return step_2_action[step]


def step_ok(step):
    target = get_step_directory(step)
    try:
        os.rename(target, str(target) + "_OK")
    except FileExistsError:
        shutil.rmtree(target + "_OK")
        os.rename(target, str(target) + "_OK")


def remove_directory(step):
    directory = get_step_directory(step)
    ok_directory = f"{directory}_OK"

    for target in [directory, ok_directory]:
        try:
            shutil.rmtree(target)
        except FileNotFoundError:
            pass


def trigger_step(step: str, start_over=False):
    if start_over:
        remove_directory(step)
    else:
        if os.path.exists(f"{get_step_directory(step)}_OK"):
            return

    action = get_step_action(step)
    action()

    step_ok(step)


async def async_trigger_step(steps: list[str], sem: Semaphore, start_over=False):
    steps_to_trigger = steps[:]
    if start_over:
        [remove_directory(step) for step in steps]
    else:
        for step in steps:
            if os.path.exists(f"{get_step_directory(step)}_OK"):
                steps_to_trigger.remove(step)

    if not steps_to_trigger:
        return

    concurrent_tasks = {}

    for step in steps:
        action = get_step_action(step)
        concurrent_tasks[asyncio.create_task(action(sem))] = step

    done, _ = await asyncio.wait(concurrent_tasks.keys())
    for done_task in done:
        step = concurrent_tasks[done_task]
        step_ok(step)


async def main(start_over=False):
    sem = Semaphore(100)

    # STEP_1 =======================================================================================================
    print("Triggering Step 1 Action [Fetching ZammadTickets]")
    await async_trigger_step(["step_1"], sem, start_over)
    #
    # # STEP_2 =======================================================================================================
    print("Triggering Step 2 Action [Parsing Tickets]")
    trigger_step("step_2", start_over)

    # STEP_3 =======================================================================================================
    # STEP_4 =======================================================================================================
    print("Triggering Step 3 and 4 Actions [Generating QA, Summary from Tickets]")
    # await async_trigger_step(["step_3", "step_4"], sem, start_over)
    await async_trigger_step(["step_4"], sem, start_over)


if __name__ == "__main__":
    asyncio.run(main(start_over=False))
