"""
Repository Summarizer — Generates high-level overviews of indexed codebases.

After indexing a repository, this module generates a structured summary:
- Tech stack detection (languages, frameworks, databases)
- Main module identification
- Entry point discovery
- Dependency analysis
- Architecture overview

The summary is stored alongside the embeddings and shown to users
when they first connect to a repository — giving instant context
before they start asking questions.
"""

import os
import logging
from typing import Optional
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are analyzing a codebase. Based on the following code samples
from the repository "{repo_name}", generate a structured overview.

Code samples:
{samples}

Generate a concise developer-friendly overview with these sections:

## Tech Stack
List the main languages, frameworks, and libraries detected.

## Architecture Overview
Describe the high-level architecture in 2-3 sentences.

## Key Modules
List the main modules/directories and what they do.

## Entry Points
Identify the main entry points (e.g., main.py, index.js, app.py).

## Notable Patterns
List any notable design patterns or architectural decisions.

Keep the total response under 400 words. Be specific, not generic."""


class RepoSummarizer:
    """Generates high-level summaries of indexed repositories.

    Uses a sample of indexed code chunks to generate a structured
    overview of the repository's architecture, tech stack, and
    key modules.

    Args:
        openai_api_key: Optional API key (falls back to env var).
        persist_dir: ChromaDB persistence directory.
    """

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama3",
        ollama_embed_model: str = "nomic-embed-text",
    ):
        self.persist_dir = persist_dir
        self.llm = ChatOllama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0,
            num_predict=800,
        )
        self.embed = OllamaEmbeddings(
            base_url=ollama_base_url,
            model=ollama_embed_model,
        )

    def summarize(self, repo_name: str) -> dict:
        """Generate a high-level summary of an indexed repository.

        Samples code chunks from the vector store, focusing on
        module-level and class-level chunks which give the best
        architectural overview.

        Args:
            repo_name: Name of the indexed repository.

        Returns:
            Dict with 'summary' (markdown) and 'metadata' (stats).
        """
        collection_dir = os.path.join(self.persist_dir, repo_name)

        if not os.path.exists(collection_dir):
            return {
                "summary": "Repository summary not found or not indexed.",
                "metadata": {},
            }

        try:
            vectorstore = Chroma(
                persist_directory=collection_dir,
                embedding_function=self.embed,
                collection_name=repo_name,
            )
        except Exception as e:
            logger.error(f"Could not load collection for {repo_name}: {e}")
            return {
                "summary": f"Could not load repository: {e}",
                "metadata": {},
            }

        # Sample diverse chunks for the overview
        # Use a broad query to get a representative sample
        docs = vectorstore.similarity_search(
            "main entry point architecture overview",
            k=15,
        )

        if not docs:
            return {
                "summary": "No code chunks found in the index.",
                "metadata": {"chunks": 0},
            }

        # Build samples text from retrieved chunks
        samples = []
        languages = set()
        files = set()

        for doc in docs:
            m = doc.metadata
            file_path = m.get("file", "unknown")
            chunk_type = m.get("type", "unknown")
            name = m.get("name", "unknown")
            lang = m.get("language", "unknown")

            languages.add(lang)
            files.add(file_path)

            # Truncate long chunks for the summary prompt
            content = doc.page_content[:500]
            samples.append(
                f"[{file_path} | {chunk_type}: {name} | {lang}]\n{content}"
            )

        samples_text = "\n\n---\n\n".join(samples)

        # Generate summary
        try:
            prompt = SUMMARY_PROMPT.format(
                repo_name=repo_name,
                samples=samples_text,
            )
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
        except Exception as e:
            logger.error(f"Summary generation failed for {repo_name}: {e}")
            summary = f"Summary generation failed: {e}"

        total_chunks = vectorstore._collection.count()

        return {
            "summary": summary,
            "metadata": {
                "repo": repo_name,
                "total_chunks": total_chunks,
                "languages": sorted(list({str(l) for l in languages if l})),
                "files_sampled": len(files),
            },
        }
