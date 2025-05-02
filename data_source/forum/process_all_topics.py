import asyncio

from data_source.forum.fetch import ai_fetch_all_topics
from data_source.forum.qa import generate_qa_for_all_forum_topics


async def main():
    await ai_fetch_all_topics()
    await generate_qa_for_all_forum_topics()


if __name__ == '__main__':
    asyncio.run(main())
