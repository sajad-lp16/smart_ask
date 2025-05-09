import json

from llama_index.core import Settings

from core.memory import memory_manager
from ai.components.prompts import ROUTER_PROMPT
from ai.components.llama_index_clients import BasicChatEngine
from ai.components.quering_index import (
    help_index,
    qa_index_manager,
    summary_index_manager
)

class Router:
    def __init__(self):
        self.routing_prompt = ROUTER_PROMPT  # needs user_input & chat history for formating

    def get_routing_schema(self):
        return {
            "message_type": None,
            "deal_ids": None,
            "emails": None,
            "person_ids": None,
            "ticket_ids": None,
        }

    async def index_path(self, user_id: str, user_input: str):
        user_chat_memory = await memory_manager.get_user_memory(user_id)
        routing_prompt = self.routing_prompt % user_input

        async with BasicChatEngine(memory=user_chat_memory) as chat_engine:
            ai_analysis = (
                await chat_engine.achat(routing_prompt)
            ).response.strip().replace("```json", "").replace("`", "")

        response_schema = self.get_routing_schema()
        response_schema.update(json.loads(ai_analysis))
        message_type = response_schema.pop("message_type")

        await memory_manager.update_memory_context(user_id, user_input, ai_analysis)

        if message_type == "help":
            return help_index(response_schema)

        elif message_type == "question":
            if not any(response_schema.values()):
                return qa_index_manager.qa_query(user_id, user_input)
            return qa_index_manager.qa_based_query(user_id, user_input, response_schema)

        elif message_type == "summarize":
            return summary_index_manager.summary_query(user_id, user_input, response_schema)


router = Router()
