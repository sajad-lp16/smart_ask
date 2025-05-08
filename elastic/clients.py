from elasticsearch import AsyncElasticsearch
from core.log_config import elastic_logger as logger

from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from core.config import (
    ELASTIC_URL,
    ELASTIC_USER,
    ELASTIC_PASSWORD,
    ELASTIC_URL_FOR_CLIENT,
    ELASTIC_QA_INDEX_NAME,
    ELASTIC_SUMMARY_INDEX_NAME
)

index_mapper = {
    "qa": ELASTIC_QA_INDEX_NAME,
    "summary": ELASTIC_SUMMARY_INDEX_NAME
}


def get_elasticsearch_store(index: str):
    return ElasticsearchStore(
        es_url=ELASTIC_URL,
        es_password=ELASTIC_PASSWORD,
        es_user=ELASTIC_USER,
        index_name=index_mapper[index]
    )


def get_async_elastic_client():
    try:
        return AsyncElasticsearch(hosts=[f'http://{ELASTIC_USER}:{ELASTIC_PASSWORD}@{ELASTIC_URL_FOR_CLIENT}', ])
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch client: {str(e)}")
        raise
