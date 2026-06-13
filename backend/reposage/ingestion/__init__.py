"""
Ingestion pipeline — clone repos, discover code files, chunk, embed, and store.
"""

from .repo_indexer import RepoIndexer
from .docstring_gen import DocstringGenerator

__all__ = ["RepoIndexer", "DocstringGenerator"]
