import json

from llama_index.core import Settings, Document
from llama_index.core import VectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import (
    ResponseMode,
    get_response_synthesizer
)

from core.config import ZAMMAD_TICKET_PREFIX
from ai.components.llama_index_clients import VectorStoreEngine
from elastic.query import ElasticQueryManager
from elastic.query_factory import build_query_hint
from ai.components.prompts import (
    WELCOME_MESSAGE,
    QA_PROMPT_TEMPLATE,
    QA_BASED_PROMPT_TEMPLATE
)


async def help_index(*args, **kwargs):
    return WELCOME_MESSAGE


class QAIndicesManager:
    SIMPLE_QA_PROMPT = PromptTemplate(QA_PROMPT_TEMPLATE)
    QA_BASED_ON_ARGS_PROMPT = PromptTemplate(QA_BASED_PROMPT_TEMPLATE)
    elastic_query_manager = ElasticQueryManager

    I_DONT_KNOW_SIMPLE_QA_QUERY_MESSAGE = "Sorry, I can't provide you answer for this question yet, you can try other questions:)"

    @classmethod
    async def qa_query(cls, user_input: str, score_threshold: float = 0.9) -> str:
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode.COMPACT, text_qa_template=cls.SIMPLE_QA_PROMPT
        )

        async with VectorStoreEngine(
                "qa", response_synthesizer=response_synthesizer, similarity_top_k=5
        ) as query_engine:
            response = await query_engine.aquery(user_input)

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
        return cls.I_DONT_KNOW_SIMPLE_QA_QUERY_MESSAGE

    @classmethod
    async def qa_based_query(cls, user_input: str, query_based_on: dict) -> str:
        text_preview = "### You are asking question based on: \n" + build_query_hint(**query_based_on) + "\n\n"
        related_hits = await cls.elastic_query_manager.get_related_elastic_hits(**query_based_on, return_hits=True)

        docs = []
        for item in related_hits:
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
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode.COMPACT,
            text_qa_template=cls.QA_BASED_ON_ARGS_PROMPT
        )

        query_engine = index.as_query_engine(response_synthesizer=response_synthesizer, similarity_top_k=5)
        response = query_engine.query(user_input)
        return text_preview + str(response)


class SummaryIndicesManager:
    elastic_query_manager = ElasticQueryManager

    @classmethod
    async def summary_query(cls, user_input: str, query_based_on: dict) -> list[str]:
        text_preview = "### You are asking for summary based on: \n" + build_query_hint(**query_based_on) + "\n\n"
        response_message = await cls.elastic_query_manager.query_elastic_based_on_args(**query_based_on)
        if isinstance(response_message, str):
            return [text_preview + response_message]

        data = [text_preview + response_message[0]]
        data.extend(response_message[1:])
        return data
