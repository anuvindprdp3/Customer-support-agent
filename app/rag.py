from __future__ import annotations

from typing import Any

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI


class AzureSearchRAG:
    def __init__(
        self,
        search_client: SearchClient,
        openai_client: AzureOpenAI,
        embedding_deployment: str,
        top_k: int = 3,
    ) -> None:
        self.search_client = search_client
        self.openai_client = openai_client
        self.embedding_deployment = embedding_deployment
        self.top_k = top_k

    def embed(self, text: str) -> list[float]:
        response = self.openai_client.embeddings.create(
            model=self.embedding_deployment,
            input=text,
        )
        return response.data[0].embedding

    def retrieve(self, query: str) -> list[dict[str, Any]]:
        vector = self.embed(query)
        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=self.top_k,
            fields="content_vector",
        )
        results = self.search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["id", "content", "source"],
        )
        docs: list[dict[str, Any]] = []
        for item in results:
            docs.append({
                "id": item["id"],
                "content": item["content"],
                "source": item.get("source", "")
            })
        return docs


def format_context(docs: list[dict[str, Any]]) -> str:
    if not docs:
        return "No relevant documents found."
    chunks = []
    for doc in docs:
        source = doc.get("source", "warranty_policy.md")
        chunks.append(f"Source: {source}\n{doc['content']}")
    return "\n\n".join(chunks)
