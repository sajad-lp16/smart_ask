import json
from llama_index.core import Settings, Document
from llama_index.core import VectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import get_response_synthesizer, ResponseMode

from ai.utils.llama_index_clients import VectorStoreEngine
from elastic.query import query_elastic, build_query_hint
from ai.utils.prompts import (
    ROUTER_PROMPT,
    WELCOME_MESSAGE,
    QA_PROMPT_TEMPLATE,
    QA_BASED_PROMPT_TEMPLATE
)
from constants import ZAMMAD_TICKET_PREFIX
from core.log_config import ai_logger as logger
from typing import List, Optional

qa_prompt = PromptTemplate(QA_PROMPT_TEMPLATE)
qa_based_prompt = PromptTemplate(QA_BASED_PROMPT_TEMPLATE)


async def qa_query(query_text, score_threshold=0.9):
    response_synthesizer = get_response_synthesizer(response_mode=ResponseMode.COMPACT, text_qa_template=qa_prompt)
    async with VectorStoreEngine("qa", response_synthesizer=response_synthesizer, similarity_top_k=5) as query_engine:
        response = await query_engine.aquery(query_text)

    try:
        response_json = json.loads(str(response).strip().replace("```json", "").replace("`", ""))
        answer = response_json.get("answer", "")
        is_related = response_json.get("related", True)
    except json.JSONDecodeError:
        is_related = True
        answer = {"answer": str(response), "related": True}

    high_score_nodes = [node for node in response.source_nodes if getattr(node, "score", 1.0) >= score_threshold]
    reference_ids = set([node.metadata.get("ticket_id") for node in high_score_nodes])

    reference_str = ""
    if is_related and reference_ids:
        reference_str += "**reference_ticket**:\n"
        for reference_id in reference_ids:
            reference_str += f"- {ZAMMAD_TICKET_PREFIX + reference_id}\n"

    if reference_str:
        return f"{answer} \n\n {reference_str}"
    return "Sorry, I can't provide you answer for this question yet, you can try other questions:)"


async def q_based_query(query, data, hint_text):
    docs = []
    for item in data:
        docs.append(
            Document(
                metadata={
                    "ticket_id": item["ticket_id"],
                    "person_ids": item["person_ids"],
                    "deal_ids": item["deal_ids"],
                },
                text=item["summary"]
            )
        )
    index = VectorStoreIndex.from_documents(docs)
    response_synthesizer = get_response_synthesizer(response_mode=ResponseMode.COMPACT,
                                                    text_qa_template=qa_based_prompt)
    query_engine = index.as_query_engine(response_synthesizer=response_synthesizer, similarity_top_k=5)

    response = query_engine.query(query)
    return hint_text + str(response)


async def query_documents(query_text: str) -> list[str]:
    routing_prompt = ROUTER_PROMPT % query_text
    ai_analysis = Settings.llm.complete(routing_prompt).text.strip().replace("```json", "").replace("`", "")

    ai_analysis_data = {
        "message_type": None,
        "deal_ids": None,
        "emails": None,
        "person_ids": None,
        "ticket_ids": None,
    }
    ai_analysis_data.update(json.loads(ai_analysis))

    if ai_analysis_data["message_type"] == "help":
        return [WELCOME_MESSAGE]

    elif ai_analysis_data["message_type"] == "question":
        print("query_elastic")
        del ai_analysis_data["message_type"]
        if not any(ai_analysis_data.values()):
            return [await qa_query(query_text)]

        text_preview = "### You are asking question based on: \n" + build_query_hint(**ai_analysis_data) + "\n\n"
        related_hits = await query_elastic(**ai_analysis_data, return_hits=True)
        if isinstance(related_hits, str):
            return [text_preview + related_hits]

        return [await q_based_query(query_text, related_hits, hint_text=text_preview)]

    elif ai_analysis_data["message_type"] == "summarize":
        print("query_elastic")
        del ai_analysis_data["message_type"]
        text_preview = "### You are asking for summary based on: \n" + build_query_hint(**ai_analysis_data) + "\n\n"
        response_message = await query_elastic(**ai_analysis_data)
        if isinstance(response_message, str):
            return [response_message]
        data = [text_preview + response_message[0]]
        data.extend(response_message[1:])
        return data
