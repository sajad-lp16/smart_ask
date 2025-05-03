import json

from llama_index.core import Settings

from ai.components.prompts import ROUTER_PROMPT
from ai.components.quering_index import (
    help_index,
    QAIndicesManager,
    SummaryIndicesManager
)


class Router:
    ROUTING_PROMPT = ROUTER_PROMPT

    @classmethod
    def get_routing_schema(cls):
        return {
            "message_type": None,
            "deal_ids": None,
            "emails": None,
            "person_ids": None,
            "ticket_ids": None,
        }

    @classmethod
    async def index_path(cls, user_input: str):
        routing_prompt = cls.ROUTING_PROMPT % user_input
        ai_analysis = (await Settings.llm.acomplete(routing_prompt)).text.strip().replace("```json", "").replace("`", "")
        response_schema = cls.get_routing_schema()

        response_schema.update(json.loads(ai_analysis))
        print(response_schema)
        message_type = response_schema.pop("message_type")

        if message_type == "help":
            return help_index(response_schema)

        elif message_type == "question":
            if not any(response_schema.values()):
                return QAIndicesManager.qa_query(user_input)
            return QAIndicesManager.qa_based_query(user_input, response_schema)

        elif message_type == "summarize":
            return SummaryIndicesManager.summary_query(user_input, response_schema)
