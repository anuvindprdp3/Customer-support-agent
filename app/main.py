from __future__ import annotations

import json
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from openai import AzureOpenAI

from app.config import load_settings
from app.guardrails import check_input, check_output
from app.memory import ConversationMemory
from app.rag import AzureSearchRAG, format_context
from app.schemas import ChatRequest, ChatResponse
from app.tools import get_tool_definitions, run_tool

load_dotenv()

app = FastAPI(title="Customer Support Agent")

settings = load_settings()

openai_client = AzureOpenAI(
    api_key=settings.openai_key,
    api_version=settings.openai_api_version,
    azure_endpoint=settings.openai_endpoint,
)

search_client = SearchClient(
    endpoint=settings.search_endpoint,
    index_name=settings.search_index,
    credential=AzureKeyCredential(settings.search_admin_key),
)

rag = AzureSearchRAG(
    search_client=search_client,
    openai_client=openai_client,
    embedding_deployment=settings.openai_embedding_deployment,
    top_k=settings.top_k,
)

memory = ConversationMemory(max_turns=settings.max_history_turns)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def build_system_prompt(context: str) -> str:
    return (
        "You are a customer support agent. Answer using the provided context. "
        "If the context is insufficient, say you do not know. "
        "Cite sources in brackets like [warranty_policy.md].\n\n"
        f"Context:\n{context}"
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    ok, message = check_input(request.message)
    if not ok:
        raise HTTPException(status_code=400, detail=message)

    docs = rag.retrieve(request.message)
    context = format_context(docs)

    messages = [{"role": "system", "content": build_system_prompt(context)}]
    messages.extend(memory.get(request.session_id))
    messages.append({"role": "user", "content": request.message})

    tools = get_tool_definitions()

    while True:
        response = openai_client.chat.completions.create(
            model=settings.openai_deployment,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        assistant = response.choices[0].message

        if assistant.tool_calls:
            messages.append({"role": "assistant", "tool_calls": assistant.tool_calls})
            for call in assistant.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = run_tool(call.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                })
            continue

        content = assistant.content or ""
        ok, output_message = check_output(content)
        if not ok:
            content = output_message
        memory.add(request.session_id, "user", request.message)
        memory.add(request.session_id, "assistant", content)

        sources = [doc.get("source", "warranty_policy.md") for doc in docs]
        return ChatResponse(response=content, sources=sources)
