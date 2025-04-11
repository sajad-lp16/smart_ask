from decouple import config
from elasticsearch import AsyncElasticsearch

from llama_index.vector_stores.elasticsearch import ElasticsearchStore

ELASTIC_URL = config("ELASTIC_URL", cast=str)
ES_PASSWORD = config("ES_PASSWORD", cast=str)
ES_USER = config("ES_USER", cast=str)
ELASTIC_URL_FOR_CLIENT = config("ELASTIC_URL_FOR_CLIENT", cast=str)

index_mapper = {
    "qa": config("QA_INDEX_NAME", cast=str),
    "summary": config("SUMMARY_INDEX_NAME", cast=str)
}


def get_elasticsearch_store(index: str):
    return ElasticsearchStore(
        es_url=config("ELASTIC_URL", cast=str),
        es_password=config("ES_PASSWORD", cast=str),
        es_user=config("ES_USER", cast=str),
        index_name=index_mapper[index]
    )


def get_async_elastic_client():
    return AsyncElasticsearch(hosts=[f'http://{ES_USER}:{ES_PASSWORD}@{ELASTIC_URL_FOR_CLIENT}', ])
