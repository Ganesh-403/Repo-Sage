"""
RepoSage — FastAPI Backend

The API layer for RepoSage. Provides endpoints for:
- POST /index     → Index a GitHub repository
- POST /query     → Ask a question about an indexed repo
- GET  /query/stream → SSE streaming for real-time answers
- GET  /repos     → List all indexed repositories
- GET  /repos/{name}/summary → Get repo summary
- DELETE /repos/{name} → Delete an indexed repo
- GET  /health    → Health check
"""

import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from reposage.ingestion.repo_indexer import RepoIndexer
from reposage.query.rag_engine import CodeRAGEngine
from reposage.query.agent_engine import CodeAgentEngine
from reposage.query.query_transformer import QueryTransformer
from reposage.analysis.repo_summarizer import RepoSummarizer

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("reposage")

# ─── Configuration ───
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CLONE_DIR = os.getenv("CLONE_DIR", "./tmp/reposage")

# ─── Shared instances ───
indexer = RepoIndexer(
    persist_dir=CHROMA_PERSIST_DIR,
    clone_dir=CLONE_DIR,
    ollama_base_url=OLLAMA_BASE_URL,
    ollama_model=OLLAMA_MODEL,
    ollama_embed_model=OLLAMA_EMBED_MODEL,
)
summarizer = RepoSummarizer(
    persist_dir=CHROMA_PERSIST_DIR,
    ollama_base_url=OLLAMA_BASE_URL,
    ollama_model=OLLAMA_MODEL,
    ollama_embed_model=OLLAMA_EMBED_MODEL,
)
query_transformer = QueryTransformer(
    ollama_base_url=OLLAMA_BASE_URL,
    model=OLLAMA_MODEL,
)

# Track indexing status
indexing_status: dict[str, dict] = {}


# ─── Lifespan ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 RepoSage backend starting...")
    logger.info(f"   ChromaDB: {CHROMA_PERSIST_DIR}")
    logger.info(f"   Clone dir: {CLONE_DIR}")
    logger.info(f"   Ollama URL: {OLLAMA_BASE_URL}")
    yield
    logger.info("RepoSage backend shutting down.")


# ─── App ───
app = FastAPI(
    title="RepoSage API",
    description="AI Codebase Intelligence — Index GitHub repos and ask questions about code.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ───

class IndexRequest(BaseModel):
    """Request to index a GitHub repository."""
    github_url: str = Field(
        ...,
        description="Full GitHub repository URL",
        json_schema_extra={"examples": ["https://github.com/tiangolo/fastapi"]},
    )
    github_token: str | None = Field(
        None,
        description="Optional GitHub PAT for private repos",
    )


class QueryRequest(BaseModel):
    """Request to query an indexed repository."""
    repo_name: str = Field(
        ...,
        description="Name of the indexed repository",
    )
    question: str = Field(
        ...,
        description="Natural language question about the codebase",
        json_schema_extra={"examples": ["How does authentication work?"]},
    )
    k: int = Field(
        6,
        description="Number of code chunks to retrieve",
        ge=1,
        le=20,
    )
    chat_history: list[dict] | None = Field(
        None,
        description="Previous conversation messages for context",
    )


class IndexResponse(BaseModel):
    repo: str
    files_processed: int
    files_skipped: int
    chunks: int
    status: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    chunks_used: int


# ─── Endpoints ───

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "reposage",
        "version": "1.0.0",
        "ollama_base_url": OLLAMA_BASE_URL,
    }


@app.post("/index", response_model=IndexResponse, tags=["Indexing"])
def index_repository(request: IndexRequest):
    """Index a GitHub repository for querying.

    Clones the repository, parses all code files using language-aware
    chunkers (AST for Python, regex for JS/TS, line-based for others),
    embeds the chunks, and stores them in ChromaDB.
    """
    if not OLLAMA_BASE_URL:
        raise HTTPException(
            status_code=500,
            detail="OLLAMA_BASE_URL not configured. Set it in .env file.",
        )

    repo_name = request.github_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    # Update status
    indexing_status[repo_name] = {"status": "indexing", "progress": "Cloning repository..."}

    try:
        token = request.github_token or GITHUB_TOKEN
        result = indexer.index_repo(request.github_url, github_token=token)
        indexing_status[repo_name] = {"status": "done", "result": result}
        return IndexResponse(**result)
    except ValueError as e:
        indexing_status[repo_name] = {"status": "error", "error": str(e)}
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        indexing_status[repo_name] = {"status": "error", "error": str(e)}
        logger.exception(f"Failed to index {request.github_url}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")


@app.get("/index/status/{repo_name}", tags=["Indexing"])
def get_index_status(repo_name: str):
    """Check the indexing status of a repository."""
    if repo_name not in indexing_status:
        raise HTTPException(status_code=404, detail="No indexing task found for this repo")
    return indexing_status[repo_name]


@app.post("/query", response_model=QueryResponse, tags=["Query"])
def query_repository(request: QueryRequest):
    """Ask a question about an indexed repository.

    Uses RAG to retrieve relevant code chunks and generate an answer
    with file:line citations.
    """
    if not OLLAMA_BASE_URL:
        raise HTTPException(
            status_code=500,
            detail="OLLAMA_BASE_URL not configured.",
        )

    collection_dir = os.path.join(CHROMA_PERSIST_DIR, request.repo_name)
    if not os.path.exists(collection_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found or not indexed.",
        )

    try:
        engine = CodeAgentEngine(
            repo_name=request.repo_name,
            persist_dir=CHROMA_PERSIST_DIR,
            clone_dir=CLONE_DIR,
            ollama_base_url=OLLAMA_BASE_URL,
            ollama_model=OLLAMA_MODEL,
            ollama_embed_model=OLLAMA_EMBED_MODEL,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found or not indexed. Error: {e}",
        )

    try:
        result = engine.query(
            question=request.question,
            k=request.k,
            chat_history=request.chat_history,
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.exception(f"Query failed for {request.repo_name}")
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.post("/query/stream", tags=["Query"])
async def query_stream(request: QueryRequest):
    """Stream an answer token by token using Server-Sent Events (SSE).

    Returns a text/event-stream response where each event contains
    a JSON object with either a token, sources list, or done signal.
    """
    if not OLLAMA_BASE_URL:
        raise HTTPException(status_code=500, detail="OLLAMA_BASE_URL not configured.")

    collection_dir = os.path.join(CHROMA_PERSIST_DIR, request.repo_name)
    if not os.path.exists(collection_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found or not indexed.",
        )

    try:
        engine = CodeRAGEngine(
            repo_name=request.repo_name,
            persist_dir=CHROMA_PERSIST_DIR,
            ollama_base_url=OLLAMA_BASE_URL,
            ollama_model=OLLAMA_MODEL,
            ollama_embed_model=OLLAMA_EMBED_MODEL,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found. Error: {e}",
        )

    async def event_generator():
        try:
            async for event in engine.aquery_stream(
                question=request.question,
                k=request.k,
                chat_history=request.chat_history,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/repos", tags=["Repositories"])
def list_repositories():
    """List all indexed repositories with their chunk counts."""
    repos = indexer.list_repos()
    return {"repos": repos, "count": len(repos)}


@app.get("/repos/{repo_name}/summary", tags=["Repositories"])
def get_repo_summary(repo_name: str):
    """Get a high-level summary of an indexed repository.

    Returns tech stack, architecture overview, key modules,
    and entry points.
    """
    result = summarizer.summarize(repo_name)
    if "Could not load" in result["summary"]:
        raise HTTPException(status_code=404, detail=result["summary"])
    return result


@app.delete("/repos/{repo_name}", tags=["Repositories"])
def delete_repository(repo_name: str):
    """Delete an indexed repository's embeddings."""
    deleted = indexer.delete_repo(repo_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_name}' not found.")
    return {"status": "deleted", "repo": repo_name}


# ─── Run ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
    )
