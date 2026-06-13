 🧠 RepoSage — AI Codebase Intelligence System

> Paste any GitHub repo URL. Ask *"How does authentication work?"* — get an answer with file paths and line numbers.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-orange.svg)](https://langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 What Is This?

RepoSage is a **100% local, RAG-powered codebase Q&A system** that indexes any GitHub repository and answers natural language questions about the code — with exact **file:line citations**. It uses **Ollama** for completely private, offline LLM inference and embeddings.

Unlike PDF chatbots that split documents by character count, RepoSage uses **AST-based code chunking** that preserves semantic function/class boundaries, producing dramatically better retrieval and answers.

### Example Queries

```
user › How does this repo handle JWT authentication?
  → Finds auth middleware, explains token validation logic
  → Cites middleware/auth.py:23, utils/jwt.py:8

user › Where and how is the database connection managed?
  → Identifies connection pool setup, environment variable config
  → Cites config/database.py:1

user › List all the API endpoints and what they do
  → Scans route files, lists endpoints with HTTP method, path, description
```

---

## 🏗️ Architecture

```
╔═══════════════════════════════════════════════════════════════╗
║  REPOSAGE PIPELINE                                            ║
╚═══════════════════════════════════════════════════════════════╝

PHASE 1 — INGESTION

[ GitHub URL ]  →  [ Repo Cloner ]  →  [ File Discoverer ]
                                              ↓
                                    [ Language-Aware Parser ]
                                      Python: ast module
                                      JS/TS:  regex-based
                                      Others: line-based fallback
                                              ↓
                                    [ Chunk Builder ]
                                      Each function/class → one chunk
                                      with file, line range, docstring
                                              ↓
                                    [ Embedding + ChromaDB ]
                                      Ollama (nomic-embed-text) → stored

PHASE 2 — QUERY

[ User Query ]  →  [ Query Transformer ]  →  [ Hybrid Search (RRF) ]
                     multi-query expansion       Vector (Chroma) + Lexical (BM25)
                                                       ↓
                                              [ Context Formatter ]
                                                file:line + full context
                                                       ↓
                                              [ Ollama LLM ]
                                                code-aware prompts
                                                       ↓
                                              [ Answer + Citations ]
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔗 **Any GitHub Repo** | Paste a public URL — system clones, discovers, and parses all code files |
| ✂️ **AST-Based Chunking** | Python `ast` module extracts functions/classes as atomic chunks |
| 🧠 **Contextual Retrieval** | *Anthropic Pattern:* Prepends file-level summaries to every chunk to preserve global context |
| ⚖️ **Hybrid Search (RRF)** | Reciprocal Rank Fusion combines Semantic (ChromaDB) and Lexical (BM25) search for exact keyword precision |
| 🌐 **Multi-Language** | Python, JavaScript, TypeScript, and line-based fallback for all others |
| 📍 **File:Line Citations** | Every answer includes exact source locations |
| 📖 **Auto Docstrings** | AI-generated summaries for undocumented functions improve retrieval |
| 💬 **Conversation Memory** | Follow-up questions understand context from previous turns |
| 📊 **Repo Summary** | Auto-generated overview: tech stack, modules, entry points |
| ⚡ **Streaming** | SSE-based token streaming for real-time answers |

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
ollama pull llama3
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

### 5. Use It

1. Open http://localhost:8501
2. Paste a GitHub URL (e.g., `https://github.com/tiangolo/fastapi`)
3. Wait for indexing to complete
4. Ask questions!

---

### Docker Compose (Alternative)

```bash
cp .env.example .env

docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:8501
```
*(Note: You will need to ensure the Docker container can reach your host's Ollama instance, typically via setting `OLLAMA_BASE_URL=http://host.docker.internal:11434` in your `.env` file.)*

---

## 📁 Project Structure

```
reposage/
├── backend/
│   ├── main.py                    # FastAPI app — /index, /query, /repos, /health
│   ├── reposage/
│   │   ├── chunkers/
│   │   │   ├── python_chunker.py  # AST-based Python chunker ← THE KEY FILE
│   │   │   ├── js_chunker.py      # Regex-based JS/TS chunker
│   │   │   └── generic_chunker.py # Line-based fallback
│   │   ├── ingestion/
│   │   │   ├── repo_indexer.py    # Clone → chunk → embed pipeline
│   │   │   └── docstring_gen.py   # AI-generated docstrings
│   │   ├── query/
│   │   │   ├── rag_engine.py      # RAG retrieval + GPT + citations
│   │   │   └── query_transformer.py # Multi-query expansion
│   │   └── analysis/
│   │       └── repo_summarizer.py # Repo overview generator
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                     # Streamlit chat UI
│   └── Dockerfile
├── tests/
│   ├── test_chunkers.py           # AST chunking tests
│   ├── test_retrieval.py          # RAG pipeline tests
│   └── fixtures/sample_repo/      # Test fixture files
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run only chunker tests
python -m pytest tests/test_chunkers.py -v

# Run with coverage
python -m pytest tests/ --cov=backend/reposage --cov-report=term-missing
```

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/index` | Index a GitHub repository |
| `GET` | `/index/status/{repo}` | Check indexing progress |
| `POST` | `/query` | Ask a question (returns full answer) |
| `POST` | `/query/stream` | Ask a question (SSE streaming) |
| `GET` | `/repos` | List indexed repositories |
| `GET` | `/repos/{name}/summary` | Get repo architecture overview |
| `DELETE` | `/repos/{name}` | Delete indexed repo |
| `GET` | `/health` | Health check |

### Example API Usage

```bash
# Index a repo
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/tiangolo/fastapi"}'

# Query the repo
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "fastapi", "question": "How does dependency injection work?"}'
```

---

## 🧠 Key Technical Decisions

### 1. AST-Based Chunking vs Character-Based
Normal RAG splits by character count — it cuts functions in half and loses context. RepoSage uses Python's `ast` module to parse the syntax tree, extracting each function/class as an atomic chunk. A 30-line function stays as one chunk.

### 2. Searchable Content Construction
Raw code is hard to search semantically. The phrase "validate user credentials" doesn't appear in code — the code says `verify_token()`. RepoSage prepends function name + docstring to each chunk before embedding, bridging natural language to code.

### 3. Hybrid Search & RRF
Pure vector search misses exact keyword matches (like specific variable names). RepoSage uses Reciprocal Rank Fusion (RRF) to merge results from both a vector store (ChromaDB) and a lexical search engine (BM25), guaranteeing perfect recall.

### 4. Contextual Retrieval (Anthropic Pattern)
A 30-line function loses its meaning without knowing what file it belongs to. During ingestion, RepoSage uses a local LLM to summarize every single file, then prepends that global context to every chunk extracted from that file. This completely eliminates "lost in translation" retrieval errors.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Code Parsing | Python `ast`, regex |
| Embeddings | Ollama (`nomic-embed-text`) |
| Vector Store | ChromaDB |
| LLM | Ollama (`llama3`) |
| Frontend | Streamlit |
| Git Operations | GitPython |
| Containers | Docker, docker-compose |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with 🧠 by <a href="https://github.com/yourname">Your Name</a>
</p>
]]>
