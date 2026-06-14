"""
Repository Indexer — The full ingestion pipeline.

Pipeline: GitHub URL → git clone → file discovery → language-aware chunking
→ optional docstring generation → embedding → ChromaDB storage.

This is the entry point for indexing a new repository. It coordinates
all the chunkers, handles file filtering, and manages the vector store.
"""

import os
import shutil
import logging
import json
from pathlib import Path
from typing import Optional

import git
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

from ..chunkers.python_chunker import PythonASTChunker, CodeChunk
from ..chunkers.js_chunker import JSChunker
from ..chunkers.generic_chunker import GenericChunker
import pickle
from .docstring_gen import DocstringGenerator

logger = logging.getLogger(__name__)

# ─── Chunker routing by file extension ───
CHUNKERS = {
    ".py":  PythonASTChunker(),
    ".js":  JSChunker(),
    ".ts":  JSChunker(),
    ".tsx": JSChunker(),
    ".jsx": JSChunker(),
}
GENERIC = GenericChunker(chunk_size=80, overlap=15)

# ─── Directories and files to skip during indexing ───
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "build",
    ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
    "coverage", ".next", ".nuxt", "vendor", "target",
    "bin", "obj", ".eggs", "site-packages",
}

SKIP_SUFFIXES = {
    ".env", ".lock", ".min.js", ".min.css", ".map",
    ".ico", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".zip", ".tar", ".gz", ".bz2", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".db", ".sqlite", ".sqlite3",
}

# File extensions we know how to index
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".rb", ".cs",
    ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp",
    ".kt", ".kts", ".swift", ".scala", ".php",
    ".lua", ".r", ".sh", ".bash", ".zsh",
    ".sql", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".json", ".xml", ".html", ".css",
}

# Maximum file size to index (100KB) — skip generated/vendored large files
MAX_FILE_SIZE = 100_000


class RepoIndexer:
    """Indexes a GitHub repository into ChromaDB for RAG retrieval.

    Handles the full pipeline from cloning to embedding storage.
    Each repository gets its own ChromaDB collection.
    """

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        clone_dir: str = "./tmp/reposage",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5-coder:7b",
        ollama_embed_model: str = "nomic-embed-text",
    ):
        self.persist_dir = persist_dir
        self.clone_dir = clone_dir

        # Initialize Ollama embeddings
        self.embed = OllamaEmbeddings(
            base_url=ollama_base_url,
            model=ollama_embed_model,
        )
        # Initialize docstring generator for contextual retrieval
        self.context_gen = DocstringGenerator(
            ollama_base_url=ollama_base_url,
            model=ollama_model,
        )

    def index_repo(self, github_url: str, github_token: Optional[str] = None) -> dict:
        """Clone a GitHub repo, chunk all code files, embed and store.

        Args:
            github_url: Full GitHub repository URL (e.g., https://github.com/user/repo)
            github_token: Optional GitHub PAT for private repos.

        Returns:
            Dict with indexing stats: repo name, files processed, chunks created.
        """
        is_local = github_url.startswith("local:///")
        if is_local:
            repo_path = Path(github_url.replace("local:///", ""))
            if not repo_path.exists():
                raise ValueError(f"Local path {repo_path} does not exist.")
            repo_name = repo_path.name
            tmp_path = str(repo_path)
            logger.info(f"Indexing local repository at {tmp_path}")
        else:
            repo_name = self._extract_repo_name(github_url)
            tmp_path = os.path.join(self.clone_dir, repo_name)

            # Clone the repository (depth=1 for speed — we don't need git history)
            logger.info(f"Cloning {github_url} → {tmp_path}")
            clone_url = github_url
            if github_token and "github.com" in github_url:
                # Inject token for private repo access
                clone_url = github_url.replace(
                    "https://github.com",
                    f"https://{github_token}@github.com"
                )

            if os.path.exists(tmp_path):
                shutil.rmtree(tmp_path)

            try:
                git.Repo.clone_from(clone_url, tmp_path, depth=1)
            except git.GitCommandError as e:
                logger.error(f"Failed to clone {github_url}: {e}")
                raise ValueError(f"Could not clone repository: {e}")

        # Discover and chunk all code files
        all_chunks: list[Document] = []
        files_processed = 0
        files_skipped = 0

        for file_path in Path(tmp_path).rglob("*"):
            # Skip directories
            if not file_path.is_file():
                continue

            # Skip known junk directories
            if any(skip in file_path.parts for skip in SKIP_DIRS):
                files_skipped += 1
                continue

            # Skip by suffix
            if any(file_path.name.endswith(s) for s in SKIP_SUFFIXES):
                files_skipped += 1
                continue

            # Skip files that are too large (likely generated/vendored)
            if file_path.stat().st_size > MAX_FILE_SIZE:
                files_skipped += 1
                continue

            # Skip non-code files
            ext = file_path.suffix.lower()
            if ext not in CODE_EXTENSIONS:
                files_skipped += 1
                continue

            # Route to the appropriate chunker
            chunker = CHUNKERS.get(ext, GENERIC)

            try:
                raw_chunks = chunker.chunk_file(str(file_path))
                
                # Contextual Retrieval: Generate file summary and apply to chunks
                relative_path = str(file_path.relative_to(tmp_path)).replace("\\", "/")
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        file_content = f.read()
                    
                    file_summary = self.context_gen.generate_file_summary(file_content, relative_path)
                    if file_summary:
                        raw_chunks = self.context_gen.enrich_with_file_context(raw_chunks, file_summary)
                except Exception as e:
                    logger.warning(f"Contextual retrieval failed for {file_path}: {e}")
                    
            except Exception as e:
                logger.warning(f"Failed to chunk {file_path}: {e}")
                files_skipped += 1
                continue

            # Convert to LangChain Documents with rich metadata
            for chunk in raw_chunks:
                all_chunks.append(Document(
                    page_content=chunk.content,
                    metadata={
                        "repo":       repo_name,
                        "file":       relative_path,
                        "type":       chunk.chunk_type,
                        "name":       chunk.name,
                        "line_start": chunk.line_start,
                        "line_end":   chunk.line_end,
                        "language":   chunk.language,
                        "calls":      getattr(chunk, "calls", []),
                    }
                ))

            files_processed += 1

        if not all_chunks:
            raise ValueError(f"No code files found in {github_url}")

        # Embed and store in ChromaDB — batch to avoid API rate limits
        logger.info(f"Embedding {len(all_chunks)} chunks for {repo_name}...")
        collection_dir = os.path.join(self.persist_dir, repo_name)

        # Delete existing collection if re-indexing
        if os.path.exists(collection_dir):
            shutil.rmtree(collection_dir)

        # Sanitize metadata for Chroma (Chroma accepts only str, int, float, bool)
        chroma_docs = []
        for doc in all_chunks:
            sanitized_metadata = doc.metadata.copy()
            if "calls" in sanitized_metadata and isinstance(sanitized_metadata["calls"], list):
                sanitized_metadata["calls"] = ",".join(sanitized_metadata["calls"])
            
            # Re-create Document to avoid modifying the original list reference in all_chunks
            chroma_docs.append(Document(
                page_content=doc.page_content,
                metadata=sanitized_metadata
            ))

        # Batch embed in groups of 100 to avoid rate limits
        batch_size = 100
        vectorstore = None

        for i in range(0, len(chroma_docs), batch_size):
            batch = chroma_docs[i:i + batch_size]
            if vectorstore is None:
                vectorstore = Chroma.from_documents(
                    batch, self.embed,
                    persist_directory=collection_dir,
                    collection_name=repo_name,
                )
            else:
                vectorstore.add_documents(batch)

        logger.info(f"Indexed {repo_name}: {files_processed} files, {len(all_chunks)} chunks")

        # Save documents for BM25 retrieval
        bm25_path = os.path.join(collection_dir, "bm25_docs.pkl")
        try:
            with open(bm25_path, "wb") as f:
                pickle.dump(all_chunks, f)
            logger.info(f"Saved BM25 documents to {bm25_path}")
        except Exception as e:
            logger.error(f"Failed to save BM25 documents: {e}")

        # Save metadata JSON to avoid initializing Chroma just to read collection stats
        meta_path = os.path.join(collection_dir, "metadata.json")
        try:
            with open(meta_path, "w") as f:
                json.dump({
                    "name": repo_name,
                    "chunks": len(all_chunks),
                    "files_processed": files_processed,
                }, f)
            logger.info(f"Saved metadata to {meta_path}")
        except Exception as e:
            logger.error(f"Failed to save metadata.json: {e}")

        # Build Knowledge Graph (GraphRAG)
        try:
            import networkx as nx
            graph = nx.DiGraph()
            
            for chunk in all_chunks:
                chunk_name = chunk.metadata.get("name")
                if chunk_name and chunk_name != "unknown":
                    graph.add_node(chunk_name, file=chunk.metadata.get("file"))
                    calls = chunk.metadata.get("calls", [])
                    for call in calls:
                        graph.add_edge(chunk_name, call, type="calls")
                        
            graph_path = os.path.join(collection_dir, "graph.pkl")
            with open(graph_path, "wb") as f:
                pickle.dump(graph, f)
            logger.info(f"Saved Knowledge Graph with {graph.number_of_nodes()} nodes to {graph_path}")
        except ImportError:
            logger.warning("networkx not installed, skipping GraphRAG build")
        except Exception as e:
            logger.error(f"Failed to save Knowledge Graph: {e}")

        # Keep remote clones so the agent's read_file tool can read original files.
        # They will be cleaned up in delete_repo.
        # if not is_local:
        #     try:
        #         shutil.rmtree(tmp_path)
        #     except Exception:
        #         pass

        return {
            "repo": repo_name,
            "files_processed": files_processed,
            "files_skipped": files_skipped,
            "chunks": len(all_chunks),
            "status": "indexed",
        }

    def list_repos(self) -> list[dict]:
        """List all indexed repositories.

        Returns:
            List of dicts with repo name and chunk count.
        """
        repos = []
        persist_path = Path(self.persist_dir)

        if not persist_path.exists():
            return repos

        for repo_dir in persist_path.iterdir():
            if repo_dir.is_dir():
                # Try reading metadata.json first (fastest)
                meta_path = repo_dir / "metadata.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, "r") as f:
                            meta = json.load(f)
                        repos.append({
                            "name": repo_dir.name,
                            "chunks": meta.get("chunks", 0),
                        })
                        continue
                    except Exception:
                        pass

                # Fallback: load bm25_docs.pkl size
                bm25_path = repo_dir / "bm25_docs.pkl"
                if bm25_path.exists():
                    try:
                        with open(bm25_path, "rb") as f:
                            docs = pickle.load(f)
                        repos.append({
                            "name": repo_dir.name,
                            "chunks": len(docs),
                        })
                        continue
                    except Exception:
                        pass

                # Ultimate fallback
                repos.append({
                    "name": repo_dir.name,
                    "chunks": -1,
                })

        return repos

    def delete_repo(self, repo_name: str) -> bool:
        """Delete an indexed repository's embeddings and clone directory.

        Args:
            repo_name: Name of the repository to delete.

        Returns:
            True if successfully deleted, False if not found.
        """
        deleted = False
        collection_dir = os.path.join(self.persist_dir, repo_name)
        if os.path.exists(collection_dir):
            shutil.rmtree(collection_dir)
            deleted = True

        clone_path = os.path.join(self.clone_dir, repo_name)
        if os.path.exists(clone_path):
            try:
                shutil.rmtree(clone_path)
                deleted = True
            except Exception as e:
                logger.warning(f"Failed to delete clone directory {clone_path}: {e}")

        return deleted

    @staticmethod
    def _extract_repo_name(github_url: str) -> str:
        """Extract repository name from a GitHub URL.

        Examples:
            https://github.com/user/repo → repo
            https://github.com/user/repo.git → repo
            https://github.com/user/repo/ → repo
        """
        name = github_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name
