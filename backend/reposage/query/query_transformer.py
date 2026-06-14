"""
Query Transformer — Multi-query expansion for code-specific questions.

A developer asking "How does auth work?" needs results from:
- authentication flow
- login endpoint
- JWT validation
- middleware checks
- session handling

A single query misses most of these. The query transformer generates
4 code-specific rephrasings before retrieval, then merges and
deduplicates the results — dramatically improving recall.

This is especially critical for code search, where the same concept
can be expressed many ways: "rate limiting" = "throttling" = "request quota"
= "rate_limiter" = "throttle_middleware".
"""

import logging
from typing import Optional

from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)

EXPANSION_PROMPT = """You are a code search query optimizer. A developer is searching
a codebase and asked: "{question}"

Generate exactly 4 alternative search queries that would help find the relevant code.
Think about:
- The actual function/variable names that might exist (e.g., "authenticate_user", "verify_token")
- Related concepts (e.g., "auth" relates to "login", "JWT", "session", "middleware")
- Both high-level and specific terms (e.g., "authentication flow" AND "check_password")
- Common naming patterns in code (snake_case, camelCase, class names)

Output exactly 4 queries, one per line, no numbering or bullets:"""


class QueryTransformer:
    """Generates multiple search queries from a single user question.

    Expands a natural language question into 4 code-specific rephrasings
    to improve retrieval recall. Each variant targets different aspects
    of how the same concept might appear in code.

    Args:
        openai_api_key: Optional API key (falls back to env var).
        model: OpenAI model for query generation (default: gpt-4o-mini).
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ):
        self.llm = ChatOllama(
            base_url=ollama_base_url,
            model=model,
            temperature=0.3,
            num_predict=200,
        )

    def expand_query(self, question: str) -> list[str]:
        """Generate multiple search queries from a single question.

        Args:
            question: The user's original natural language question.

        Returns:
            List of 4-5 queries (original + generated expansions).
        """
        queries = [question]  # Always include the original

        try:
            prompt = EXPANSION_PROMPT.format(question=question)
            response = self.llm.invoke(prompt)
            raw = response.content.strip()

            # Parse the 4 generated queries
            for line in raw.splitlines():
                line = line.strip().lstrip("0123456789.-) ")
                if line and len(line) > 3 and line not in queries:
                    queries.append(line)

            # Cap at 5 total queries (original + 4 expansions)
            queries = queries[:5]

        except Exception as e:
            logger.warning(f"Query expansion failed, using original: {e}")

        logger.info(f"Expanded '{question}' → {queries}")
        return queries

    def expand_and_retrieve(self, question: str, retriever, k_per_query: int = 4) -> list:
        """Expand query, retrieve for each variant, deduplicate results.

        This is the main entry point for multi-query retrieval.
        Retrieves documents for each expanded query, then deduplicates
        by page_content to avoid showing the same code chunk twice.

        Args:
            question: The user's question.
            retriever: A LangChain retriever instance.
            k_per_query: Number of results per expanded query.

        Returns:
            Deduplicated list of Document objects.
        """
        queries = self.expand_query(question)
        all_docs = []
        seen_content = set()

        for q in queries:
            try:
                docs = retriever.invoke(q)
                for doc in docs[:k_per_query]:
                    # Deduplicate by full content string
                    content_key = doc.page_content.strip()
                    if content_key not in seen_content:
                        seen_content.add(content_key)
                        all_docs.append(doc)
            except Exception as e:
                logger.warning(f"Retrieval failed for query '{q}': {e}")

        logger.info(
            f"Multi-query retrieval: {len(queries)} queries → "
            f"{len(all_docs)} unique chunks"
        )
        return all_docs
