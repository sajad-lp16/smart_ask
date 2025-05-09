from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine.types import ChatMessage
from llama_index.core.llms import MessageRole
from core.redis_service import redis_gateway


class MemoryManager:
    def __init__(self):
        self.memories = {}
        self.memory_source = redis_gateway
        self.history_load_count = 10

    async def load_memory_context(self, user_id):
        memory = await self.memory_source.load_memory(user_id)
        history = memory.get_all()
        chat_context = "\n".join(history[-self.history_load_count:])
        return chat_context

    async def get_user_memory(self, user_id: str) -> ChatMemoryBuffer:
        if user_id not in self.memories:
            self.memories[user_id] = ChatMemoryBuffer.from_defaults()
        return self.memories[user_id]

    async def update_memory_context(self, user_id: str, user_input: str, response: str) -> None:
        memory = await self.get_user_memory(user_id)

        user_message = ChatMessage(
            role=MessageRole.USER,
            content=user_input
        )
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response
        )

        await memory.aput(user_message)
        await memory.aput(assistant_message)


memory_manager = MemoryManager()
