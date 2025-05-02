import json

from llama_index.core import Settings, Document
from llama_index.core import VectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode

from core.config import ZAMMAD_TICKET_PREFIX
from ai.components.llama_index_clients import VectorStoreEngine
# from elastic.query import query_elastic, build_query_hint
from ai.components.prompts import (
    ROUTER_PROMPT,
    WELCOME_MESSAGE,
    QA_PROMPT_TEMPLATE,
    QA_BASED_PROMPT_TEMPLATE
)

async def query_controller(query_text: str) -> list[str]:



    routing_prompt = ROUTER_PROMPT % query_text
    ai_analysis = await Settings.llm.acomplete(routing_prompt).text.strip().replace("```json", "").replace("`", "")

    ai_analysis_data = {
        "message_type": None,
        "deal_ids": None,
        "emails": None,
        "person_ids": None,
        "ticket_ids": None,
    }
    ai_analysis_data.update(json.loads(ai_analysis))

    # if ai_analysis_data["message_type"] == "help":
    #     return [WELCOME_MESSAGE]
    #
    # elif ai_analysis_data["message_type"] == "question":
    #     del ai_analysis_data["message_type"]
    #     if not any(ai_analysis_data.values()):
    #         return [await qa_query(query_text)]
    #
    #     text_preview = "### You are asking question based on: \n" + build_query_hint(**ai_analysis_data) + "\n\n"
    #
    #     if isinstance(related_hits, str):
    #         return [text_preview + related_hits]
    #
    #     return [await q_based_query(query_text, related_hits, hint_text=text_preview)]
    #
    # elif ai_analysis_data["message_type"] == "summarize":
    #     del ai_analysis_data["message_type"]
    #     text_preview = "### You are asking for summary based on: \n" + build_query_hint(**ai_analysis_data) + "\n\n"
    #     response_message = await query_elastic(**ai_analysis_data)
    #     if isinstance(response_message, str):
    #         return [text_preview + response_message]
    #
    #     data = [text_preview + response_message[0]]
    #     data.extend(response_message[1:])
    #     return data
