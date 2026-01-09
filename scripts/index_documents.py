from __future__ import annotations

import hashlib
import os
import sys
from typing import Iterable

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
)
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.config import load_settings

CHUNK_SIZE = 800
OVERLAP = 100
VECTOR_DIMENSIONS = 1536


def chunk_text(text: str) -> Iterable[str]:
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + CHUNK_SIZE)
        yield text[start:end]
        if end == length:
            break
        start = end - OVERLAP


def build_index(name: str) -> SearchIndex:
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="vector-profile", algorithm_configuration_name="hnsw")],
    )

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, sortable=True),
    ]

    return SearchIndex(name=name, fields=fields, vector_search=vector_search)


def main() -> None:
    load_dotenv()
    settings = load_settings()

    openai_client = AzureOpenAI(
        api_key=settings.openai_key,
        api_version=settings.openai_api_version,
        azure_endpoint=settings.openai_endpoint,
    )

    index_client = SearchIndexClient(
        endpoint=settings.search_endpoint,
        credential=AzureKeyCredential(settings.search_admin_key),
    )

    index = build_index(settings.search_index)
    index_client.create_or_update_index(index)

    search_client = SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index,
        credential=AzureKeyCredential(settings.search_admin_key),
    )

    with open(os.path.join(os.getcwd(), "warranty_policy.md"), "r", encoding="utf-8") as handle:
        content = handle.read()

    docs = []
    for idx, chunk in enumerate(chunk_text(content)):
        chunk_id = hashlib.sha1(chunk.encode("utf-8")).hexdigest()
        embedding = openai_client.embeddings.create(
            model=settings.openai_embedding_deployment,
            input=chunk,
        ).data[0].embedding
        docs.append({
            "id": chunk_id,
            "content": chunk,
            "content_vector": embedding,
            "source": "warranty_policy.md",
        })

    if docs:
        search_client.upload_documents(docs)

    print(f"Indexed {len(docs)} chunks into {settings.search_index}")


if __name__ == "__main__":
    main()
