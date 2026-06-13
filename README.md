🧠 RepoSage — AI Codebase Intelligence System

> Paste any GitHub repo URL or use a local directory. Ask *"How does authentication work?"* — get an answer with file paths and line numbers.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-red.svg)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 What Is This?

RepoSage is an **autonomous, 100% local, Agentic GraphRAG system** that indexes any GitHub repository or local directory and answers natural language questions about the code — with exact **file:line citations**. It uses **Ollama** (`qwen2.5-coder:7b`) for completely private, offline LLM inference and embeddings.

Unlike PDF chatbots that split documents by character count, RepoSage uses **AST-based code chunking** and **Knowledge Graphs (GraphRAG)** that preserve semantic boundaries and trace function call dependencies, producing dramatically better retrieval and answers.

---

## 🏗️ Architecture

```
╔═══════════════════════════════════════════════════════════════╗
║  REPOSAGE PIPELINE                                            ║
╚═══════════════════════════════════════════════════════════════╝

PHASE 1 — INGESTION (Static or Real-Time Local Sync)

[ Code Source ]  →  [ File Discoverer ]
                      ↓
            [ Language-Aware Parser ]
              Python: ast module (extracts calls)
              JS/TS:  regex-based (extracts calls)
                      ↓
            [ Chunk Builder & GraphRAG Builder ]
              Extracts functions/classes and builds NetworkX Knowledge Graph
                      ↓
            [ Embedding + ChromaDB ]
              Ollama (nomic-embed-text) → stored

PHASE 2 — AGENTIC QUERY (LangGraph)

[ User Query ]  →  [ LangGraph Autonomous Agent ]
                             ↓
              Tool 1: `semantic_search(query)`
                 (Hybrid Search + GraphRAG Context)
                             ↓
              Tool 2: `read_file(path)`
                 (Proactively opens files for missing context)
                             ↓
                [ Answer + Exact File Citations ]
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Autonomous Agent** | Powered by LangGraph, the AI actively uses search and file-reading tools to investigate complex queries |
| 🕸️ **GraphRAG** | Extracts function-call dependencies into a Knowledge Graph to completely eliminate missing-dependency hallucinations |
| 🔄 **Real-Time Sync** | Use `watchdog` to monitor local directories and automatically re-index files the moment you save them (`local:///...`) |
| 🔗 **Any GitHub Repo** | Paste a public URL — system clones, discovers, and parses all code files |
| ✂️ **AST-Based Chunking** | Python `ast` module extracts functions/classes as atomic chunks |
| 🧠 **Contextual Retrieval** | *Anthropic Pattern:* Prepends file-level summaries to every chunk to preserve global context |
| ⚖️ **Hybrid Search (RRF)** | Reciprocal Rank Fusion combines Semantic (ChromaDB) and Lexical (BM25) search for exact keyword precision |
| 🌐 **Multi-Language** | Python, JavaScript, TypeScript, and line-based fallback for all others |
| 📍 **File:Line Citations** | Every answer includes exact source locations |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/yourname/reposage.git
cd reposage

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install streamlit requests  # Frontend deps
```

### 2. Pull Ollama Models & Configure

```bash
# Pull the default models
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

cp .env.example .env
# Edit .env to customize models if needed
```

### 3. Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Run Frontend (separate terminal)

```bash
cd frontend
streamlit run app.py
```

### 5. Local Real-Time Sync (Optional)

```bash
# In a new terminal, start the watchdog daemon for your local project
python backend/reposage/ingestion/file_watcher.py "C:/path/to/my/project"
```

---

## 📁 Project Structure

```
reposage/
├── backend/
│   ├── main.py                    # FastAPI app — /index, /query, /repos, /health
│   ├── reposage/
│   │   ├── chunkers/
│   │   │   ├── python_chunker.py  # AST-based Python chunker + GraphRAG extraction
│   │   │   ├── js_chunker.py      # Regex-based JS/TS chunker
│   │   │   └── generic_chunker.py # Line-based fallback
│   │   ├── ingestion/
│   │   │   ├── repo_indexer.py    # Clone/Local → chunk → embed + GraphRAG pipeline
│   │   │   ├── file_watcher.py    # Watchdog daemon for real-time local sync
│   │   │   └── docstring_gen.py   # AI-generated docstrings
│   │   ├── query/
│   │   │   ├── agent_engine.py    # LangGraph autonomous agent
│   │   │   ├── rag_engine.py      # Core RAG retrieval + GraphRAG traversal
│   │   │   └── query_transformer.py # Multi-query expansion
│   │   └── analysis/
│   │       └── repo_summarizer.py # Repo overview generator
│   ├── requirements.txt
│   └── tests/                     # Pytest suite
├── frontend/
│   ├── app.py                     # Streamlit chat UI
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest backend/tests/ -v

# Run only chunker tests
python -m pytest backend/tests/test_chunkers.py -v
```

---

## 🧠 Key Technical Decisions

### 1. GraphRAG & Knowledge Graphs
Standard RAG systems fail when the answer requires understanding dependencies (e.g., "what does function A do?" when function A just calls function B). RepoSage extracts call graphs during indexing and dynamically injects caller/callee code chunks into the context at query time.

### 2. Autonomous Agentic Workflow (LangGraph)
Instead of a single-shot generation prompt, RepoSage uses LangGraph. The LLM is provided with `semantic_search` and `read_file` tools. If the search results aren't clear enough, the agent will autonomously open the target file to investigate further before answering.

### 3. Contextual Retrieval (Anthropic Pattern)
A 30-line function loses its meaning without knowing what file it belongs to. During ingestion, RepoSage uses a local LLM to summarize every single file, then prepends that global context to every chunk extracted from that file.

### 4. Hybrid Search & RRF
Pure vector search misses exact keyword matches (like specific variable names). RepoSage uses Reciprocal Rank Fusion (RRF) to merge results from both a vector store (ChromaDB) and a lexical search engine (BM25), guaranteeing perfect recall.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Code Parsing | Python `ast`, regex, `networkx` |
| Agent Engine | LangChain, LangGraph |
| Embeddings | Ollama (`nomic-embed-text`) |
| Vector Store | ChromaDB |
| LLM | Ollama (`qwen2.5-coder:7b`) |
| Frontend | Streamlit |
| Background Sync | `watchdog` |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
