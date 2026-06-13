"""
JavaScript/TypeScript Regex Chunker

Extracts functions, arrow functions, classes, and exported components
from JS/TS files using regex pattern matching. Since JS/TS don't have
a stdlib AST parser in Python, we use carefully crafted regex patterns
that handle the most common code structures.

Handles:
- Named function declarations: function foo() { ... }
- Arrow function assignments: const foo = (...) => { ... }
- Class declarations: class Foo { ... }
- Export default declarations
- JSDoc comments (/** ... */) attached to functions
"""

import re
from pathlib import Path
from typing import List
from .python_chunker import CodeChunk


# ─── Regex patterns for JS/TS code structures ───

# Matches: function functionName(params) {
FUNC_PATTERN = re.compile(
    r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
    re.MULTILINE,
)

# Matches: const/let/var functionName = (params) => {
# Also:   const/let/var functionName = async (params) => {
# Also:   const/let/var functionName = function(params) {
ARROW_PATTERN = re.compile(
    r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>\s*[{(]",
    re.MULTILINE,
)

FUNC_EXPR_PATTERN = re.compile(
    r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(",
    re.MULTILINE,
)

# Matches: class ClassName {
# Also:   class ClassName extends BaseClass {
CLASS_PATTERN = re.compile(
    r"^(?:export\s+)?(?:default\s+)?class\s+(\w+)",
    re.MULTILINE,
)

# Matches JSDoc comments: /** ... */
JSDOC_PATTERN = re.compile(
    r"/\*\*\s*(.*?)\*/",
    re.DOTALL,
)


class JSChunker:
    """Extracts functions, arrow functions, and classes from JS/TS files.

    Uses regex pattern matching since Python doesn't have a built-in JS parser.
    Captures the most common code structures and falls back to line-based
    chunking for files with non-standard patterns.
    """

    def __init__(self, min_lines: int = 5, max_chunk_chars: int = 8000):
        self.min_lines = min_lines
        self.max_chunk_chars = max_chunk_chars

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """Parse a JS/TS file and extract function/class chunks.

        Args:
            file_path: Path to a .js, .ts, .jsx, or .tsx file.

        Returns:
            List of CodeChunk objects found via regex matching.
        """
        source = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()
        lang = Path(file_path).suffix.lstrip(".").lower()
        if lang in ("jsx", "tsx"):
            lang = "tsx" if "tsx" in lang else "jsx"

        # Collect all match positions: (line_number, name, type)
        matches = []

        for pattern, chunk_type in [
            (FUNC_PATTERN, "function"),
            (ARROW_PATTERN, "function"),
            (FUNC_EXPR_PATTERN, "function"),
            (CLASS_PATTERN, "class"),
        ]:
            for m in pattern.finditer(source):
                line_num = source[:m.start()].count("\n") + 1
                name = m.group(1)
                matches.append((line_num, name, chunk_type))

        # Sort by line number and deduplicate (same line, same name)
        matches.sort(key=lambda x: x[0])
        seen = set()
        unique_matches = []
        for line_num, name, chunk_type in matches:
            key = (line_num, name)
            if key not in seen:
                seen.add(key)
                unique_matches.append((line_num, name, chunk_type))

        if not unique_matches:
            # No recognizable structures — fall back to whole file
            return self._fallback_chunk(file_path, source, lines, lang)

        chunks = []

        for i, (line_num, name, chunk_type) in enumerate(unique_matches):
            # Determine chunk boundaries
            start_line = line_num
            if i + 1 < len(unique_matches):
                end_line = unique_matches[i + 1][0] - 1
            else:
                end_line = len(lines)

            # Try to find the actual end by brace matching
            actual_end = self._find_block_end(lines, start_line - 1, end_line)
            if actual_end:
                end_line = actual_end

            # Skip tiny chunks
            if end_line - start_line + 1 < self.min_lines:
                continue

            chunk_source = "\n".join(lines[start_line - 1:end_line])
            if len(chunk_source) > self.max_chunk_chars:
                chunk_source = chunk_source[:self.max_chunk_chars] + "\n// ... (truncated)"

            # Look for JSDoc comment above this function/class
            docstring = self._find_jsdoc(lines, start_line - 1)

            # Build searchable content
            searchable = f"// {chunk_type}: {name}\n"
            if docstring:
                searchable += f"// Summary: {docstring}\n"
            searchable += chunk_source
            
            # Extract function calls for GraphRAG (heuristic)
            call_matches = re.findall(r"(\w+)\s*\(", chunk_source)
            js_keywords = {"if", "for", "while", "switch", "catch", "function", "return", "import", "export"}
            calls = list(set([c for c in call_matches if c not in js_keywords and c != name]))

            chunks.append(CodeChunk(
                content=searchable,
                file_path=file_path,
                chunk_type=chunk_type,
                name=name,
                line_start=start_line,
                line_end=end_line,
                language=lang,
                docstring=docstring,
                calls=calls,
            ))

        return chunks if chunks else self._fallback_chunk(file_path, source, lines, lang)

    def _find_block_end(self, lines: List[str], start_idx: int, max_end: int) -> int | None:
        """Find the end of a { ... } block by counting braces.

        Returns the 1-indexed line number of the closing brace,
        or None if braces don't balance (fall back to next match).
        """
        brace_count = 0
        started = False

        for i in range(start_idx, min(max_end, len(lines))):
            line = lines[i]
            # Remove string literals and comments to avoid false brace matches
            cleaned = self._strip_strings_and_comments(line)

            for char in cleaned:
                if char == "{":
                    brace_count += 1
                    started = True
                elif char == "}":
                    brace_count -= 1
                    if started and brace_count == 0:
                        return i + 1  # 1-indexed

        return None

    @staticmethod
    def _strip_strings_and_comments(line: str) -> str:
        """Remove string literals and comments from a line for brace counting."""
        # Remove single-line comments
        line = re.sub(r"//.*$", "", line)
        # Remove string literals (simple approach)
        line = re.sub(r"'[^']*'", "", line)
        line = re.sub(r'"[^"]*"', "", line)
        line = re.sub(r"`[^`]*`", "", line)
        return line

    @staticmethod
    def _find_jsdoc(lines: List[str], func_line_idx: int) -> str | None:
        """Look for a JSDoc comment (/** ... */) immediately above a function."""
        # Walk backwards from the function line looking for */
        idx = func_line_idx - 1
        while idx >= 0 and lines[idx].strip() == "":
            idx -= 1

        if idx < 0 or "*/" not in lines[idx]:
            return None

        # Collect the JSDoc block
        doc_lines = []
        while idx >= 0:
            doc_lines.insert(0, lines[idx])
            if "/**" in lines[idx]:
                break
            idx -= 1

        doc_text = "\n".join(doc_lines)
        # Clean up JSDoc syntax
        doc_text = re.sub(r"/\*\*\s*", "", doc_text)
        doc_text = re.sub(r"\s*\*/", "", doc_text)
        doc_text = re.sub(r"^\s*\*\s?", "", doc_text, flags=re.MULTILINE)
        doc_text = doc_text.strip()

        return doc_text if doc_text else None

    def _fallback_chunk(
        self, file_path: str, source: str, lines: List[str], lang: str
    ) -> List[CodeChunk]:
        """Fall back to treating the whole file as a single chunk."""
        return [CodeChunk(
            content=source[:self.max_chunk_chars],
            file_path=file_path,
            chunk_type="module",
            name=Path(file_path).stem,
            line_start=1,
            line_end=len(lines),
            language=lang,
        )]
