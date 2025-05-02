import json
from typing import Awaitable, Callable, Any

from llama_index.core import Settings

from ai.components.prompts import ROUTER_PROMPT
from ai.components.quering_index import help_index, QAIndicesManager


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
    async def index_path(cls, user_input: str) -> tuple[Awaitable[Any], dict | None]:
        routing_prompt = cls.ROUTING_PROMPT % user_input
        ai_analysis = await Settings.llm.acomplete(routing_prompt).text.strip().replace("```json", "").replace("`", "")
        response_schema = cls.get_routing_schema()

        response_schema.update(json.loads(ai_analysis))

        if response_schema["message_type"] == "help":
            return help_index, None

        elif response_schema["message_type"] == "question":
            del response_schema["message_type"]

            if not any(response_schema.values()):
                return QAIndicesManager.qa_query, None

            if isinstance(related_hits, str):
                return [text_preview + related_hits]

            return [await q_based_query(query_text, related_hits, hint_text=text_preview)]

        elif response_schema["message_type"] == "summarize":
            del response_schema["message_type"]
            text_preview = "### You are asking for summary based on: \n" + build_query_hint(**response_schema) + "\n\n"
            response_message = await query_elastic(**response_schema)
            if isinstance(response_message, str):
                return [text_preview + response_message]

            data = [text_preview + response_message[0]]
            data.extend(response_message[1:])
            return data
