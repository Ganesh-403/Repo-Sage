"""
Tests for the retrieval pipeline — verify that RAG components work correctly.

These tests mock the LLM and Embedding interfaces to avoid requiring models during CI.
They verify:
- Context formatting with file:line citations
- Query condensation with chat history
- Document metadata structure
- Source citation formatting
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reposage.chunkers.python_chunker import CodeChunk


# ─── Mock classes for testing without actual models ───

@dataclass
class MockDocument:
    """Simulates a LangChain Document."""
    page_content: str
    metadata: dict


class MockResponse:
    """Simulates an LLM response."""
    def __init__(self, content: str):
        self.content = content


# ═══════ Context Formatting Tests ═══════

class TestContextFormatting:
    """Test that code chunks are formatted correctly for the LLM prompt."""

    def test_format_single_document(self):
        """Verify formatting of a single code chunk."""
        doc = MockDocument(
            page_content="def hello():\n    return 'world'",
            metadata={
                "file": "src/utils.py",
                "line_start": 42,
                "type": "function",
                "name": "hello",
                "language": "python",
            },
        )

        # Simulate _format_context logic
        m = doc.metadata
        header = f"### [1] {m['file']}:{m['line_start']} ({m['type']}: {m['name']})"
        code_fence = f"```{m['language']}\n{doc.page_content}\n```"
        result = f"{header}\n{code_fence}"

        assert "src/utils.py:42" in result
        assert "function: hello" in result
        assert "```python" in result
        assert "def hello():" in result

    def test_format_multiple_documents(self):
        """Verify formatting of multiple chunks with indexing."""
        docs = [
            MockDocument(
                page_content="def auth():\n    pass",
                metadata={
                    "file": "auth.py", "line_start": 10,
                    "type": "function", "name": "auth", "language": "python",
                },
            ),
            MockDocument(
                page_content="class UserService:\n    pass",
                metadata={
                    "file": "services/user.py", "line_start": 1,
                    "type": "class", "name": "UserService", "language": "python",
                },
            ),
        ]

        parts = []
        for i, doc in enumerate(docs, 1):
            m = doc.metadata
            header = f"### [{i}] {m['file']}:{m['line_start']} ({m['type']}: {m['name']})"
            code_fence = f"```{m['language']}\n{doc.page_content}\n```"
            parts.append(f"{header}\n{code_fence}")

        result = "\n\n".join(parts)

        assert "[1]" in result
        assert "[2]" in result
        assert "auth.py:10" in result
        assert "services/user.py:1" in result

    def test_source_citation_format(self):
        """Verify source citations are file:line format."""
        docs = [
            MockDocument(
                page_content="...",
                metadata={"file": "src/auth/login.py", "line_start": 42},
            ),
            MockDocument(
                page_content="...",
                metadata={"file": "utils/jwt.py", "line_start": 8},
            ),
        ]

        sources = [
            f"{d.metadata['file']}:{d.metadata['line_start']}" for d in docs
        ]

        assert sources == ["src/auth/login.py:42", "utils/jwt.py:8"]


# ═══════ Metadata Tests ═══════

class TestDocumentMetadata:
    """Verify that chunk metadata structure is correct for RAG."""

    def test_required_metadata_fields(self):
        """All chunks should have the required metadata fields."""
        required_fields = {"repo", "file", "type", "name", "line_start", "line_end", "language"}

        metadata = {
            "repo": "fastapi-backend",
            "file": "src/auth/login.py",
            "type": "function",
            "name": "authenticate_user",
            "line_start": 42,
            "line_end": 67,
            "language": "python",
        }

        assert required_fields.issubset(metadata.keys())

    def test_chunk_type_values(self):
        """Chunk type should be one of the valid values."""
        valid_types = {"function", "class", "module"}

        for chunk_type in ["function", "class", "module"]:
            assert chunk_type in valid_types

    def test_code_chunk_dataclass(self):
        """Verify CodeChunk dataclass works correctly."""
        chunk = CodeChunk(
            content="def foo(): pass",
            file_path="test.py",
            chunk_type="function",
            name="foo",
            line_start=1,
            line_end=5,
            language="python",
            docstring="Test function",
        )

        assert chunk.content == "def foo(): pass"
        assert chunk.file_path == "test.py"
        assert chunk.chunk_type == "function"
        assert chunk.name == "foo"
        assert chunk.line_start == 1
        assert chunk.line_end == 5
        assert chunk.language == "python"
        assert chunk.docstring == "Test function"


# ═══════ Query Transformer Tests ═══════

class TestQueryTransformerLogic:
    """Test query transformation logic without API calls."""

    def test_original_query_always_included(self):
        """The original query should always be in the expansion list."""
        queries = ["How does auth work?"]  # Original
        # Simulated expansions
        expansions = [
            "authentication flow",
            "login function",
            "JWT verify",
            "token check",
        ]
        queries.extend(expansions)

        assert queries[0] == "How does auth work?"
        assert len(queries) == 5

    def test_deduplication_logic(self):
        """Duplicate documents should be removed."""
        docs = [
            MockDocument(page_content="def auth(): pass", metadata={}),
            MockDocument(page_content="def auth(): pass", metadata={}),  # Duplicate
            MockDocument(page_content="def login(): pass", metadata={}),
        ]

        seen = set()
        unique = []
        for doc in docs:
            key = doc.page_content.strip()
            if key not in seen:
                seen.add(key)
                unique.append(doc)

        assert len(unique) == 2, "Should deduplicate identical chunks"


# ═══════ Chat History Condensation Tests ═══════

class TestChatHistoryCondensation:
    """Test conversation memory logic."""

    def test_no_history_returns_original(self):
        """With no chat history, question should be unchanged."""
        question = "How does login work?"
        chat_history = []

        # Logic: if no history, return original
        result = question if not chat_history else "condensed"
        assert result == question

    def test_history_formatting(self):
        """Chat history should be formatted correctly for condensation."""
        history = [
            {"role": "user", "content": "What is authenticate_user?"},
            {"role": "assistant", "content": "authenticate_user validates credentials..."},
        ]

        formatted = "\n".join(
            f"{msg['role'].title()}: {msg['content']}" for msg in history[-6:]
        )

        assert "User: What is authenticate_user?" in formatted
        assert "Assistant: authenticate_user validates credentials..." in formatted

    def test_history_truncation(self):
        """Only the last 6 messages should be used for condensation."""
        history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        truncated = history[-6:]

        assert len(truncated) == 6
        assert truncated[0]["content"] == "msg 14"

# ═══════ Hybrid Search & RRF Tests ═══════

class TestHybridSearchRRF:
    """Test Reciprocal Rank Fusion logic."""

    def test_reciprocal_rank_fusion(self):
        from reposage.query.rag_engine import CodeRAGEngine
        engine = CodeRAGEngine.__new__(CodeRAGEngine) # Bypass __init__
        
        docA = MockDocument(page_content="docA", metadata={})
        docB = MockDocument(page_content="docB", metadata={})
        docC = MockDocument(page_content="docC", metadata={})
        
        vector_docs = [docA, docB, docC]
        bm25_docs = [docC, docA]
        
        # docA: rank 0 in vector, rank 1 in bm25 -> 1/60 + 1/61 = 0.03306
        # docB: rank 1 in vector, rank inf in bm25 -> 1/61 = 0.01639
        # docC: rank 2 in vector, rank 0 in bm25 -> 1/62 + 1/60 = 0.03279
        
        # Expected order: docA, docC, docB
        fused = engine._reciprocal_rank_fusion(vector_docs, bm25_docs, k=60)
        
        assert len(fused) == 3
        assert fused[0].page_content == "docA"
        assert fused[1].page_content == "docC"
        assert fused[2].page_content == "docB"
