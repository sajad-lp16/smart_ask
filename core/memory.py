from core.redis_service import redis_gateway


class MemoryManager:
    def __init__(self):
        self.memory_source = redis_gateway
        self.history_load_count = 10

    async def load_memory_context(self, user_id):
        memory = await self.memory_source.load_memory(user_id)
        history = memory.get_all()
        chat_context = "\n".join([f"{m.role}: {m.message}" for m in history[-self.history_load_count:]])
        return chat_context

    async def update_memory_context(self, user_id, user_input, assistant_input):
        memory = await self.memory_source.load_memory(user_id)
        memory.put("user", user_input)
        memory.put("assistant", assistant_input)

        await self.memory_source.save_memory(user_id, memory)


memory_manager = MemoryManager()
