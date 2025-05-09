import time
import pickle

import redis.asyncio as redis

from llama_index.core.memory import ChatMemoryBuffer
from core.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB
)


class RedisGateway:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.raw_redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=False)
        self.processing_timeout = 5 * 60

    async def queue_items(self, source_name: str, item_ids: list[str]) -> None:
        async with self.redis_client.pipeline() as pipe:
            current_time = int(time.time())
            for item_id in item_ids:
                key = f"{source_name}_update_{item_id}"
                value = f"pending_{current_time}"
                await pipe.set(key, value)
            await pipe.execute()

    async def mark_processing(self, source_name: str, item_ids: list[str]) -> None:
        async with self.redis_client.pipeline() as pipe:
            current_time = int(time.time())
            for item_id in item_ids:
                key = f"{source_name}_update_{item_id}"
                value = f"processing_{current_time}"
                await pipe.set(key, value)
            await pipe.execute()

    async def mark_completed(self, source_name: str, item_ids: list[str]) -> None:
        async with self.redis_client.pipeline() as pipe:
            for item_id in item_ids:
                key = f"{source_name}_update_{item_id}"
                await pipe.delete(key)
            await pipe.execute()

    async def get_pending_items(self, source_name: str) -> list[dict[str, str]]:
        pattern = f"{source_name}_update_*"
        pending_ids = []
        current_time = int(time.time())

        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern)

            for key in keys:
                value = await self.redis_client.get(key)
                if value:
                    status, timestamp = value.split("_")
                    timestamp = int(timestamp)
                    if status == "pending" or (status == "processing" and
                                               current_time - timestamp > self.processing_timeout):
                        item_id = key.split("_")[-1]
                        pending_ids.append(item_id)

            if cursor == 0:
                break

        await self.mark_processing(source_name, pending_ids)
        return pending_ids

    async def get_item_status(self, source_name: str, item_id: str) -> str | None:
        key = f"{source_name}_update_{item_id}"
        value = await self.redis_client.get(key)
        if value:
            return value.split("_")[0]
        return None

    async def load_memory(self, user_id: str, token_limit=6000) -> ChatMemoryBuffer:
        key = f"memory:{user_id}"
        if await self.redis_client.exists(key):
            return pickle.loads(await redis_gateway.raw_redis_client.get(key))
        else:
            return ChatMemoryBuffer.from_defaults(token_limit=token_limit)

    async def save_memory(self, user_id: str, memory: ChatMemoryBuffer, timeout: int = 7200):
        key = f"chat-memory:{user_id}"
        await self.redis_client.set(key, pickle.dumps(memory), ex=timeout)


redis_gateway = RedisGateway()
