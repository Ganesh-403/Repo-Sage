# RepoSage — Enterprise-Grade Codebase Intelligence System

RepoSage is a 100% offline, Agentic GraphRAG system designed for developers and engineering teams. By supplying a GitHub repository URL or a local directory path, users can query their codebase in natural language. The system autonomously retrieves context, traverses functional dependencies, and generates precise answers complete with exact file paths and line numbers.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-red.svg)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

Traditional Retrieval-Augmented Generation (RAG) systems fail on complex codebases due to arbitrary character-limit splitting and an inability to understand structural dependencies. RepoSage overcomes these limitations by combining:

1. **Abstract Syntax Tree (AST) Chunking**: Code is parsed logically into atomic structural units (functions, classes) rather than arbitrary text chunks.
2. **Knowledge Graphs (GraphRAG)**: Function-call dependencies are mapped at ingestion time. During retrieval, the engine dynamically injects caller and callee contexts, virtually eliminating missing-dependency hallucinations.
3. **Autonomous Agentic Workflows**: Powered by LangGraph, the query engine operates autonomously, utilizing tools to execute semantic searches and proactively read specific files if further context is required.

RepoSage operates entirely locally. It utilizes Ollama running the `qwen2.5-coder:7b` model, guaranteeing absolute privacy for proprietary codebases.

---

## Core Capabilities

- **Autonomous Agent**: Leverages LangGraph to actively investigate queries through iterative tool execution (`semantic_search` and `read_file`).
- **GraphRAG Architecture**: Uses `networkx` to build and traverse a directed graph of function calls across the codebase.
- **Real-Time Synchronization**: Monitors local directories using a `watchdog` daemon, seamlessly re-indexing files in the background upon modification.
- **Hybrid Search via RRF**: Combines dense vector retrieval (ChromaDB) with lexical keyword matching (BM25) using Reciprocal Rank Fusion to maximize recall.
- **Contextual Retrieval (Anthropic Pattern)**: Auto-generates file-level summaries and prepends them to individual chunks, preserving macro-level context within micro-level retrievals.
- **Multi-Language Support**: AST parsing for Python, Regular Expression heuristics for JavaScript/TypeScript, and line-based fallback for all other languages.
- **Precision Citations**: Every generated response includes verifiable source locations formatted as `filename:line_number`.

---

## System Architecture

### Phase 1: Ingestion Pipeline

1. **Source Resolution**: The system accepts public GitHub URLs (cloning via GitPython) or local file URIs (`local:///...`).
2. **Language-Aware Parsing**: Files are routed to specific chunkers. Python utilizes the native `ast` module; JS/TS utilizes regex patterns.
3. **Graph Construction**: The parser identifies function declarations and invocation calls (`ast.Call`), constructing a NetworkX directed graph.
4. **Context Injection**: An LLM generates a comprehensive summary for each file. This summary is injected into every child chunk.
5. **Embedding & Persistence**: Chunks are embedded using `nomic-embed-text` and persisted in a local ChromaDB collection alongside the serialized graph.

### Phase 2: Agentic Query Pipeline

1. **Tool-Equipped Agent**: The user query is passed to a LangGraph workflow controlling the `qwen2.5-coder:7b` model.
2. **Semantic Search**: The agent invokes the `semantic_search` tool, which triggers a Hybrid Search (Vector + BM25).
3. **Graph Traversal**: The RAG engine detects matched functions and traverses the Knowledge Graph to append related callers and callees to the context window.
4. **Iterative Investigation**: If the retrieved context is insufficient, the agent may invoke the `read_file` tool to inspect full file contents.
5. **Synthesis**: The agent formulates the final response, synthesizing the gathered context and citing source locations.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.com/) installed and running locally
- Git

### 1. Repository Setup

Clone the repository and configure the virtual environment:

```bash
git clone https://github.com/yourname/reposage.git
cd reposage

python -m venv .venv
# Linux/macOS
source .venv/bin/activate  
# Windows
.venv\Scripts\activate

pip install -r backend/requirements.txt
pip install streamlit requests
```

### 2. Model Configuration

Pull the necessary models via Ollama. By default, RepoSage utilizes Qwen2.5 for inference and Nomic for embeddings.

```bash
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

Copy the environment template:

```bash
cp .env.example .env
```
*(Optional: Edit `.env` to supply a GitHub Personal Access Token for indexing private repositories).*

### 3. Running the Application

**Backend Server (FastAPI)**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Frontend Client (Streamlit)**
Open a separate terminal instance and start the user interface:
```bash
cd frontend
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

### 4. Enabling Local Real-Time Synchronization (Optional)

To enable background monitoring and automatic re-indexing for local projects, execute the file watcher daemon:

```bash
python backend/reposage/ingestion/file_watcher.py "C:/absolute/path/to/your/project"
```

---

## Project Structure

```text
reposage/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── reposage/
│   │   ├── chunkers/
│   │   │   ├── python_chunker.py  # AST parser and GraphRAG call extraction
│   │   │   ├── js_chunker.py      # Regex JS/TS parser and extraction
│   │   │   └── generic_chunker.py # Line-based fallback mechanism
│   │   ├── ingestion/
│   │   │   ├── repo_indexer.py    # Ingestion orchestration and ChromaDB integration
│   │   │   ├── file_watcher.py    # Watchdog daemon for real-time synchronization
│   │   │   └── docstring_gen.py   # Contextual retrieval summary generator
│   │   ├── query/
│   │   │   ├── agent_engine.py    # LangGraph autonomous agent workflow
│   │   │   ├── rag_engine.py      # Hybrid RRF search and graph traversal
│   │   │   └── query_transformer.py # Query expansion logic
│   │   └── analysis/
│   │       └── repo_summarizer.py # Repository macro-analysis generator
│   ├── requirements.txt
│   └── tests/                     # Pytest suite
├── frontend/
│   ├── app.py                     # Streamlit frontend application
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Testing

Execute the test suite from the root directory:

```bash
python -m pytest backend/tests/ -v
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
