from functools import lru_cache
from typing import List, Optional

from elasticsearch import Elasticsearch
from fastapi import APIRouter, Request
from pydantic import BaseModel
from structlog import get_logger

from .. import config
from ..search.search_index import query_question

router = APIRouter()
log = get_logger()


class Answers(BaseModel):
    answers: Optional[List[str]]


class ElasticResults(BaseModel):
    doc_text: Optional[List[str]]
    doc_url: Optional[str]
    sec_text: Optional[List[str]]
    sec_url: Optional[str]


@router.get("/answers/", response_model=Answers)
def answers(request: Request, question: str):

    language = request.headers.get("Accept-Language")
    es = get_es_client()

    if language:
        formatted_language = format_language(language)
        elastic_results = query_question(es, question, formatted_language)

    else:
        elastic_results = query_question(es, question)

    log.info(
        "elastic_results",
        elastic_results=elastic_results,
        question=question,
        language=language,
    )

    elastic_results_formatted = ElasticResults.parse_obj(elastic_results)

    return {"answers": elastic_results_formatted.sec_text}


def format_language(language):
    if "en" in language.lower():
        return "en"
    elif "fr" in language.lower():
        return "fr"


@lru_cache()
def get_es_client():
    conf = config.get()

    return Elasticsearch(
        [{"host": conf.elastic_search_host, "port": 443}],
        use_ssl=True,
        verify_certs=True,
    )