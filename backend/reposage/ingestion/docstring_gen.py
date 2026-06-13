"""
Docstring Generator — Auto-generate summaries for undocumented functions.

Functions without docstrings are harder to retrieve via semantic search
because the embedding model has no natural language description to match
against. This module uses GPT-4o-mini to generate concise 1-sentence
summaries that are prepended to the chunk content before embedding.

This bridges the gap between how developers ask questions ("validate user
credentials") and how code is written (verify_token()).
"""

import logging
from typing import Optional
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)

# Focused prompt for generating concise function summaries
DOCSTRING_PROMPT = """You are a senior developer writing docstrings. Given this code,
write a single concise sentence (max 20 words) explaining what it does.
Focus on WHAT it does, not HOW. Use plain English, no jargon.

Code:
```
{code}
```

Write only the summary sentence, nothing else:"""

FILE_SUMMARY_PROMPT = """You are an expert developer. Read the following entire file and write a brief (2-3 sentences) summary of what this file is responsible for within the overall architecture. 
Focus on its purpose, primary components, and how it might interact with others.

File: {file_path}
Code:
```
{code}
```

Write only the summary, no other text:"""


class DocstringGenerator:
    """Generates 1-sentence summaries for functions without docstrings.

    Used during the ingestion pipeline to improve semantic retrieval
    quality. The generated summary is appended to the chunk's content
    before embedding, so the vector representation includes both the
    code and a natural language description.

    Args:
        openai_api_key: Optional API key (falls back to env var).
        model: OpenAI model to use (default: gpt-4o-mini).
        max_code_chars: Maximum code length to send for summarization.
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "llama3",
        max_code_chars: int = 3000,
    ):
        self.llm = ChatOllama(
            base_url=ollama_base_url,
            model=model,
            temperature=0,
            num_predict=60,
        )
        self.max_code_chars = max_code_chars

    def generate_docstring(self, code: str, name: str = "") -> Optional[str]:
        """Generate a 1-sentence summary for a code snippet.

        Args:
            code: The source code to summarize.
            name: Optional function/class name for context.

        Returns:
            A concise summary string, or None if generation fails.
        """
        if not code or not code.strip():
            return None

        # Truncate very long code to save tokens
        truncated = code[:self.max_code_chars]

        try:
            prompt = DOCSTRING_PROMPT.format(code=truncated)
            response = self.llm.invoke(prompt)
            summary = response.content.strip()

            # Basic validation — should be a short sentence
            if len(summary) > 200 or not summary:
                return None

            # Clean up common LLM artifacts
            summary = summary.strip('"').strip("'").strip(".")
            summary += "."

            return summary

        except Exception as e:
            logger.warning(f"Failed to generate docstring for {name}: {e}")
            return None

    def enrich_chunks(self, chunks: list) -> list:
        """Add AI-generated summaries to chunks that lack docstrings.

        Modifies chunks in-place by prepending the generated summary
        to the chunk's content field.

        Args:
            chunks: List of CodeChunk objects from any chunker.

        Returns:
            The same list with enriched content (modified in-place).
        """
        enriched_count = 0

        for chunk in chunks:
            # Skip chunks that already have docstrings
            if chunk.docstring:
                continue

            # Skip module-level chunks (less useful to summarize)
            if chunk.chunk_type == "module":
                continue

            summary = self.generate_docstring(chunk.content, chunk.name)
            if summary:
                # Prepend the generated summary for better semantic matching
                chunk.content = f"# AI-generated summary: {summary}\n{chunk.content}"
                chunk.docstring = f"[auto] {summary}"
                enriched_count += 1

        logger.info(f"Enriched {enriched_count}/{len(chunks)} chunks with AI docstrings")
        return chunks

    def generate_file_summary(self, code: str, file_path: str) -> Optional[str]:
        """Generate a summary for an entire file for contextual retrieval."""
        if not code or not code.strip():
            return None

        # Allow slightly more tokens for whole file context
        truncated = code[:self.max_code_chars * 2] 
        
        try:
            prompt = FILE_SUMMARY_PROMPT.format(file_path=file_path, code=truncated)
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            if not summary or len(summary) > 1000:
                return None
                
            return summary
        except Exception as e:
            logger.warning(f"Failed to generate file summary for {file_path}: {e}")
            return None

    def enrich_with_file_context(self, chunks: list, file_summary: str) -> list:
        """Prepend the file-level summary to every chunk from that file.
        
        This implements Anthropic's 'Contextual Retrieval' pattern, ensuring
        that even a small 10-line function chunk retains the global context
        of the module it belongs to.
        """
        if not file_summary:
            return chunks
            
        for chunk in chunks:
            context_header = f"// Context: This code belongs to a file with the following purpose: {file_summary}\n\n"
            chunk.content = context_header + chunk.content
            
        return chunks
