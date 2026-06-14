"""
Generic Line-Based Chunker — Fallback for unsupported languages.

Used for languages without a dedicated parser (Go, Rust, Java, C++, Ruby, etc.).
Splits code into overlapping windows of configurable size, preserving some
context at chunk boundaries via overlap.

This is less precise than AST-based or regex-based chunking, but ensures
every file in a repository gets indexed — no code is silently skipped.
"""

from pathlib import Path
from typing import List
from .python_chunker import CodeChunk


class GenericChunker:
    """Splits any text file into overlapping line-based chunks.

    Args:
        chunk_size: Number of lines per chunk (default: 80).
        overlap: Number of overlapping lines between adjacent chunks (default: 15).

    The overlap ensures that code structures spanning chunk boundaries
    still appear in at least one chunk. For example, a function starting
    at line 78 and ending at line 95 would appear in both the first chunk
    (lines 1-80) and the second chunk (lines 66-145).
    """

    def __init__(self, chunk_size: int = 80, overlap: int = 15):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """Split a file into overlapping line-based chunks.

        Args:
            file_path: Path to any text source file.

        Returns:
            List of CodeChunk objects with line ranges and content.
        """
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()

        if not lines:
            return []

        # Detect language from extension
        ext = Path(file_path).suffix.lstrip(".").lower()
        lang = self._detect_language(ext)

        # Detect comment style
        if lang in ("javascript", "typescript", "java", "cpp", "c", "csharp", "kotlin", "swift", "scala", "php", "rust", "go", "css", "jsx", "tsx"):
            comment_start, comment_end = "// ", ""
        elif lang in ("sql",):
            comment_start, comment_end = "-- ", ""
        elif lang in ("html", "xml"):
            comment_start, comment_end = "<!-- ", " -->"
        else:
            comment_start, comment_end = "# ", ""

        # Small files: return as a single chunk
        if len(lines) <= self.chunk_size:
            header = f"{comment_start}File: {Path(file_path).name} (lines 1-{len(lines)}){comment_end}\n"
            return [CodeChunk(
                content=header + source,
                file_path=file_path,
                chunk_type="module",
                name=Path(file_path).stem,
                line_start=1,
                line_end=len(lines),
                language=lang,
            )]

        chunks = []
        step = self.chunk_size - self.overlap
        chunk_idx = 0

        for start in range(0, len(lines), step):
            end = min(start + self.chunk_size, len(lines))
            chunk_lines = lines[start:end]
            chunk_content = "\n".join(chunk_lines)

            # Build a descriptive name for this chunk
            chunk_name = f"{Path(file_path).stem}_part{chunk_idx}"

            # Add file context header for searchability
            header = f"{comment_start}File: {Path(file_path).name} (lines {start + 1}-{end}){comment_end}\n"
            searchable = header + chunk_content

            chunks.append(CodeChunk(
                content=searchable,
                file_path=file_path,
                chunk_type="module",
                name=chunk_name,
                line_start=start + 1,
                line_end=end,
                language=lang,
            ))

            chunk_idx += 1

            # Stop if we've reached the end of the file
            if end >= len(lines):
                break

        return chunks

    @staticmethod
    def _detect_language(ext: str) -> str:
        """Map file extension to language name."""
        lang_map = {
            "go": "go",
            "rs": "rust",
            "java": "java",
            "kt": "kotlin",
            "kts": "kotlin",
            "rb": "ruby",
            "cs": "csharp",
            "cpp": "cpp",
            "cc": "cpp",
            "cxx": "cpp",
            "c": "c",
            "h": "c",
            "hpp": "cpp",
            "swift": "swift",
            "scala": "scala",
            "php": "php",
            "lua": "lua",
            "r": "r",
            "R": "r",
            "sh": "bash",
            "bash": "bash",
            "zsh": "bash",
            "sql": "sql",
            "yaml": "yaml",
            "yml": "yaml",
            "toml": "toml",
            "json": "json",
            "xml": "xml",
            "html": "html",
            "css": "css",
            "md": "markdown",
            "txt": "text",
        }
        return lang_map.get(ext, ext if ext else "text")
