"""
Python AST Chunker — The core innovation of RepoSage.

Uses Python's built-in `ast` module to parse the syntax tree and extract
each function/class as an atomic, semantically complete chunk. Unlike
character-based chunking (RecursiveCharacterTextSplitter), this preserves
the natural semantic unit of code.

A 30-line function stays as one chunk. A class stays as one chunk.
Each chunk gets metadata: file path, line range, function/class name,
and docstring — enabling file:line citations in answers.
"""

import ast
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CodeChunk:
    """Represents a single semantically meaningful unit of code.

    Each chunk is one function, class, or module-level block with
    full metadata for citation in RAG responses.
    """
    content: str
    file_path: str
    chunk_type: str        # "function" | "class" | "module"
    name: str
    line_start: int
    line_end: int
    language: str = "python"
    docstring: Optional[str] = None
    calls: List[str] = field(default_factory=list)


class PythonASTChunker:
    """Extracts functions and classes from Python files using AST parsing.

    Unlike character-based chunking, this preserves semantic units.
    Each function or class becomes exactly one chunk with its full
    source code, name, docstring, and line range metadata.

    Design decisions:
    - Functions < 5 lines are skipped (getters/setters — not useful for search)
    - Module-level docstrings are captured as separate chunks (file-level context)
    - Searchable content prepends function name + docstring for better embedding
    - SyntaxError falls back to whole-file chunking (handles partial/broken code)
    """

    def __init__(self, min_lines: int = 5, max_chunk_chars: int = 8000):
        self.min_lines = min_lines
        self.max_chunk_chars = max_chunk_chars

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """Parse a Python file and extract function/class chunks.

        Args:
            file_path: Absolute or relative path to a .py file.

        Returns:
            List of CodeChunk objects, one per function/class found.
        """
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()
        chunks = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Fallback: treat whole file as one chunk (e.g., partial code, Jinja templates)
            return [CodeChunk(
                content=source[:self.max_chunk_chars],
                file_path=file_path,
                chunk_type="module",
                name=Path(file_path).stem,
                line_start=1,
                line_end=len(lines),
                language="python",
            )]

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            # Extract the source lines for this node
            start = node.lineno - 1
            end = node.end_lineno
            chunk_source = "\n".join(lines[start:end])

            # Skip tiny functions (< min_lines lines) — getters, __repr__, etc.
            if end - start < self.min_lines:
                continue

            # Truncate extremely large chunks (rare but possible — e.g., god classes)
            if len(chunk_source) > self.max_chunk_chars:
                chunk_source = chunk_source[:self.max_chunk_chars] + "\n# ... (truncated)"

            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            docstring = ast.get_docstring(node)

            # Build searchable content: name + docstring + code body
            # This bridges natural language queries to code-level retrieval
            # e.g., "validate user credentials" maps to verify_token() because
            # the docstring says "Validates user credentials via JWT token"
            searchable = f"# {chunk_type}: {node.name}\n"
            if docstring:
                searchable += f"# Summary: {docstring}\n"
            searchable += chunk_source
            
            # Extract function calls inside this chunk for GraphRAG
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)

            chunks.append(CodeChunk(
                content=searchable,
                file_path=file_path,
                chunk_type=chunk_type,
                name=node.name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                language="python",
                docstring=docstring,
                calls=list(set(calls)),
            ))

        # Also add module-level docstring (top of file explanation)
        # This gives high-level context about what the file does
        module_doc = ast.get_docstring(tree)
        if module_doc:
            chunks.insert(0, CodeChunk(
                content=f"# Module: {Path(file_path).name}\n# {module_doc}",
                file_path=file_path,
                chunk_type="module",
                name=Path(file_path).stem,
                line_start=1,
                line_end=3,
                language="python",
                docstring=module_doc,
            ))

        return chunks

    def get_imports(self, file_path: str) -> List[str]:
        """Extract import statements from a Python file.

        Useful for dependency graph analysis and understanding
        which modules a file depends on.
        """
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        imports = []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return imports
