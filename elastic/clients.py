from decouple import config

from llama_index.vector_stores.elasticsearch import ElasticsearchStore


def get_elasticsearch_store():
    return ElasticsearchStore(
        es_url=config("ELASTIC_URL", cast=str),
        es_password=config("ES_PASSWORD", cast=str),
        es_user=config("ES_USER", cast=str),
        index_name=config("QA_INDEX_NAME", cast=str)
    )
