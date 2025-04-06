from elasticsearch import AsyncElasticsearch
import json
import os
import asyncio

async def main():
    client = AsyncElasticsearch(
        hosts=['http://127.0.0.1:9200',]
    )
    # await client.indices.delete(index="avicenna_tickets_summary")

    for file in os.listdir("ready"):
        with open(f"ready/{file}") as ff:
            data = json.load(ff)
        _id, _ = file.split(".")
        await client.index(id=_id, index="avicenna_tickets_summary", body=data)

    await client.close()

asyncio.run(main())