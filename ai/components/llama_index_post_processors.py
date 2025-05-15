from typing import List, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle

from data_source import QA_SOURCE_PRIORITY_SCORES


class MixedScoreHeaderPostprocessor(BaseNodePostprocessor):
    header_key: str = "source"
    boost_factors: dict = QA_SOURCE_PRIORITY_SCORES
    default_boost: float = 0.02
    top_k: Optional[int] = 3

    def _postprocess_nodes(
            self,
            nodes: List[NodeWithScore],
            query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        if not nodes:
            return []
        for node_with_score in nodes:
            header_level = node_with_score.node.metadata.get(self.header_key)
            boost = self.boost_factors.get(header_level, self.default_boost)

            node_with_score.score += boost

        sorted_nodes = sorted(nodes, key=lambda x: x.score, reverse=True)

        if self.top_k is not None:
            return sorted_nodes[:self.top_k]
        else:
            return sorted_nodes
