import time
import pickle
from typing import (
    List,
    Dict,
    Optional
)

import redis.asyncio as redis

from llama_index.core.memory import ChatMemoryBuffer


class RedisGateway:
    def __init__(self, host: str = "redis", port: int = 6379, db: int = 0):
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.processing_timeout = 5 * 60

    async def queue_items(self, source_name: str, item_ids: List[str]) -> None:
        """
        Queue multiple items for processing with status "pending"
        """
        async with self.redis_client.pipeline() as pipe:
            current_time = int(time.time())
            for item_id in item_ids:
                key = f"{source_name}_update_{item_id}"
                value = f"pending_{current_time}"
                await pipe.set(key, value)
            await pipe.execute()

    async def mark_processing(self, source_name: str, item_ids: List[str]) -> None:
        """
        Mark multiple items as being processed
        """
        async with self.redis_client.pipeline() as pipe:
            current_time = int(time.time())
            for item_id in item_ids:
                key = f"{source_name}_update_{item_id}"
                value = f"processing_{current_time}"
                await pipe.set(key, value)
            await pipe.execute()

    async def mark_completed(self, source_name: str, item_ids: List[str]) -> None:
        """
        Mark multiple items as completed and remove them from Redis
        """
        async with self.redis_client.pipeline() as pipe:
            for item_id in item_ids:
                key = f"{source_name}_update_{item_id}"
                await pipe.delete(key)
            await pipe.execute()

    async def get_pending_items(self, source_name: str) -> List[Dict[str, str]]:
        """
        Get all pending items and processing items that have been processing for more than 5 minutes
        """
        pattern = f"{source_name}_update_*"
        pending_items = []
        current_time = int(time.time())

        # Use SCAN to iterate through all keys matching the pattern
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern)

            for key in keys:
                value = await self.redis_client.get(key)
                if value:
                    status, timestamp = value.split("_")
                    timestamp = int(timestamp)

                    # Check if item is pending or has been processing for too long
                    if status == "pending" or (status == "processing" and
                                               current_time - timestamp > self.processing_timeout):
                        item_id = key.split("_")[-1]
                        pending_items.append({
                            "item_id": item_id,
                            "status": status,
                            "timestamp": timestamp
                        })

            if cursor == 0:
                break

        return pending_items

    async def get_item_status(self, source_name: str, item_id: str) -> Optional[str]:
        key = f"{source_name}_update_{item_id}"
        value = await self.redis_client.get(key)
        if value:
            return value.split("_")[0]
        return None

    async def load_memory(self, user_id: str, token_limit=30000) -> ChatMemoryBuffer:
        key = f"memory:{user_id}"
        if await self.redis_client.exists(key):
            return pickle.loads(redis_gateway.redis_client.get(key))
        else:
            return ChatMemoryBuffer.from_defaults(token_limit=token_limit)

    async def save_memory(self, user_id: str, memory: ChatMemoryBuffer):
        key = f"memory:{user_id}"
        await self.redis_client.set(key, pickle.dumps(memory))


redis_gateway = RedisGateway()
