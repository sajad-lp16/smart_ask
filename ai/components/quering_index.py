import json

from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import (
    ResponseMode,
    get_response_synthesizer
)
from core.memory import memory_manager
from core.config import (
    ZAMMAD_TICKET_PREFIX,
    FORUM_TOPIC_URL
)
from ai.components.llama_index_clients import VectorStoreEngine
from elastic.query import elastic_query_manager
from elastic.query_factory import build_query_hint
from ai.components.prompts import (
    WELCOME_MESSAGE,
    QA_PROMPT_TEMPLATE,
    QA_BASED_PROMPT_TEMPLATE
)


async def help_index(*args, **kwargs):
    return WELCOME_MESSAGE


class QAIndicesManager:
    def __init__(self):
        self.simple_qa_prompt = PromptTemplate(QA_PROMPT_TEMPLATE)
        self.qa_based_on_args_prompt = PromptTemplate(QA_BASED_PROMPT_TEMPLATE)
        self.i_dont_know_simple_qa_message = (
            "Sorry, I can't provide you answer for this question yet, "
            "you can try other questions:)"
        )

    @staticmethod
    def _reference_builder(source: str, source_id):
        source_url_mapping = {
            "zammad": lambda: ZAMMAD_TICKET_PREFIX + str(source_id),
            "forum": lambda: FORUM_TOPIC_URL + str(source_id),
            "avicenna_learn": lambda: source_id,
            "avicenna_blog": lambda: source_id,
        }
        source_url_builder = source_url_mapping[source]
        return source_url_builder()

    async def qa_query(self, user_id, user_input: str, score_threshold: float = 0.9) -> str:
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode.COMPACT, text_qa_template=self.simple_qa_prompt
        )
        chat_history = await memory_manager.load_memory_context(user_id)
        async with VectorStoreEngine(
                "qa", response_synthesizer=response_synthesizer, similarity_top_k=5, chat_history=chat_history
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
        references_data = set([(node.metadata.get("source"), node.metadata.get("source_id")) for node in high_score_nodes])

        reference_str = ""
        if is_related and references_data:
            reference_str += "**reference_ticket**:\n"
            for source, source_id in references_data:
                reference_str += f"- {self._reference_builder(source, source_id)}\n"

        if reference_str:
            response = f"{answer} \n\n {reference_str}"
            await memory_manager.update_memory_context(user_id, user_input, response)
            return response

        await memory_manager.update_memory_context(user_id, user_input, self.i_dont_know_simple_qa_message)
        return self.i_dont_know_simple_qa_message

    async def qa_based_query(self, user_id, user_input: str, query_based_on: dict) -> str:
        text_preview = "### You are asking question based on: \n" + build_query_hint(**query_based_on) + "\n\n"
        related_hits = await elastic_query_manager.get_related_elastic_hits(**query_based_on)
        chat_history = await memory_manager.load_memory_context(user_id)
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
            text_qa_template=self.qa_based_on_args_prompt
        )

        query_engine = index.as_query_engine(
            response_synthesizer=response_synthesizer, similarity_top_k=5, chat_history=chat_history
        )
        response = text_preview + str(query_engine.query(user_input))

        await memory_manager.update_memory_context(user_id, user_input, response)

        return response


class SummaryIndicesManager:
    async def summary_query(self, user_id, user_input: str, query_based_on: dict) -> list[str]:
        text_preview = "### You are asking for summary based on: \n" + build_query_hint(**query_based_on) + "\n\n"
        response_message = await elastic_query_manager.query_elastic_based_on_args(**query_based_on)
        if isinstance(response_message, str):
            response = [text_preview + response_message]
            await memory_manager.update_memory_context(user_id, user_input, f"{response}")
            return [text_preview + response_message]

        response = [text_preview + response_message[0]]
        response.extend(response_message[1:])

        await memory_manager.update_memory_context(user_id, user_input, f"{response}")

        return response


qa_index_manager = QAIndicesManager()
summary_index_manager = SummaryIndicesManager()
