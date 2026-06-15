"""
Code-Aware RAG Query Engine — The brain of RepoSage.

Handles the full query pipeline:
1. Receive natural language question
2. Retrieve relevant code chunks from ChromaDB (vector similarity)
3. Format chunks with file:line attribution
4. Construct code-aware prompts (system + user)
5. Stream response from local Ollama model
6. Return answer with source citations

The system prompt instructs the LLM to always cite file paths and line
numbers, explain code before technical details, and connect multi-file
answers.
"""

import os
import logging
from typing import Optional, AsyncGenerator

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.messages import SystemMessage, HumanMessage
import pickle
from .query_transformer import QueryTransformer

logger = logging.getLogger(__name__)

# ─── Prompts ───

SYSTEM_PROMPT = """You are RepoSage, an expert code assistant with deep knowledge \
of the {repo_name} codebase. You answer questions about code architecture, \
implementation details, and specific functions.

Rules:
1. ALWAYS cite specific file paths and line numbers from the provided context
2. If code is shown, explain it clearly before the technical details
3. If the answer spans multiple files, explain how they connect
4. If the answer is not in the provided context, say "I don't see that in the indexed code"
5. Format file citations as: `filename.py:line_number`
6. Use markdown formatting for code blocks and structure your answer clearly
7. Be concise but thorough — developers value precision over verbosity

You're talking to a developer who wants to understand this codebase quickly."""

QUERY_PROMPT = """Here are the relevant code sections from the {repo_name} repository:

{context}

---

Developer's question: {question}

Provide a clear answer with specific file:line citations."""

CONDENSE_PROMPT = """Given the following conversation and a follow-up question, \
rephrase the follow-up question to be a standalone question that includes \
relevant context from the conversation history.

Chat History:
{chat_history}

Follow Up Question: {question}

Standalone question:"""


class CodeRAGEngine:
    """RAG query engine for code-aware question answering.

    Retrieves relevant code chunks from ChromaDB and generates
    answers with file:line citations using a local Ollama model.

    Args:
        repo_name: Name of the indexed repository.
        persist_dir: ChromaDB persistence directory.
        ollama_base_url: Base URL for local Ollama service.
        ollama_model: Local Ollama model name.
        ollama_embed_model: Local Ollama embedding model name.
    """

    def __init__(
        self,
        repo_name: str,
        persist_dir: str = "./chroma_db",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama3",
        ollama_embed_model: str = "nomic-embed-text",
    ):
        embed = OllamaEmbeddings(
            base_url=ollama_base_url,
            model=ollama_embed_model,
        )

        collection_dir = os.path.join(persist_dir, repo_name)
        self.vectorstore = Chroma(
            persist_directory=collection_dir,
            embedding_function=embed,
            collection_name=repo_name,
        )
        self.repo_name = repo_name
        self.llm = ChatOllama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0,
        )
        self.condense_llm = ChatOllama(
            base_url=ollama_base_url,
            model=ollama_model,
            temperature=0,
        )
        self.query_transformer = QueryTransformer(
            ollama_base_url=ollama_base_url,
            model=ollama_model,
        )
        
        # Load BM25 index if available
        self.bm25_retriever = None
        bm25_path = os.path.join(collection_dir, "bm25_docs.pkl")
        if os.path.exists(bm25_path):
            try:
                with open(bm25_path, "rb") as f:
                    docs = pickle.load(f)
                self.bm25_retriever = BM25Retriever.from_documents(docs)
                logger.info(f"Loaded BM25 index with {len(docs)} documents.")
            except Exception as e:
                logger.error(f"Failed to load BM25 index: {e}")

        # Load Knowledge Graph
        self.graph = None
        graph_path = os.path.join(collection_dir, "graph.pkl")
        if os.path.exists(graph_path):
            try:
                import networkx as nx
                with open(graph_path, "rb") as f:
                    self.graph = pickle.load(f)
                logger.info(f"Loaded Knowledge Graph with {self.graph.number_of_nodes()} nodes.")
            except ImportError:
                logger.warning("networkx not installed, skipping GraphRAG.")
            except Exception as e:
                logger.error(f"Failed to load Knowledge Graph: {e}")


    def _format_context(self, docs) -> str:
        """Format code chunks with clear file:line attribution.

        Each chunk is displayed with:
        - Header: file_path:line_start (type: name)
        - Language-specific code fence
        - Full chunk content

        This formatting helps the LLM understand where code comes from
        and produce accurate citations in its response.
        """
        parts = []
        for i, doc in enumerate(docs, 1):
            m = doc.metadata
            file_path = m.get("file", "unknown")
            line_start = m.get("line_start", "?")
            chunk_type = m.get("type", "unknown")
            name = m.get("name", "unknown")
            language = m.get("language", "")

            header = f"### [{i}] {file_path}:{line_start} ({chunk_type}: {name})"
            code_fence = f"```{language}\n{doc.page_content}\n```"
            parts.append(f"{header}\n{code_fence}")

        return "\n\n".join(parts)

    def _condense_question(self, question: str, chat_history: list[dict]) -> str:
        """Condense a follow-up question using conversation history.

        Handles cases like "Tell me more about that function" by
        incorporating context from previous turns.
        """
        if not chat_history:
            return question

        history_str = "\n".join(
            f"{msg['role'].title()}: {msg['content']}" for msg in chat_history[-6:]
        )

        prompt = CONDENSE_PROMPT.format(
            chat_history=history_str,
            question=question,
        )

        response = self.condense_llm.invoke(prompt)
        condensed = response.content.strip()
        logger.info(f"Condensed: '{question}' → '{condensed}'")
        return condensed

    def _reciprocal_rank_fusion(self, vector_docs: list, bm25_docs: list, k: int = 60) -> list:
        """Merge documents using Reciprocal Rank Fusion (RRF)."""
        fused_scores = {}
        doc_map = {}
        
        for rank, doc in enumerate(vector_docs):
            content_key = doc.page_content.strip()
            doc_map[content_key] = doc
            fused_scores[content_key] = fused_scores.get(content_key, 0) + 1 / (rank + k)
            
        for rank, doc in enumerate(bm25_docs):
            content_key = doc.page_content.strip()
            doc_map[content_key] = doc
            fused_scores[content_key] = fused_scores.get(content_key, 0) + 1 / (rank + k)
            
        # Sort by fused score
        sorted_docs = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_map[key] for key, _ in sorted_docs]

    def _retrieve_and_fuse(self, question: str, k: int) -> tuple[list, list[str]]:
        """Retrieve relevant code chunks and enrich context in parallel using a ThreadPoolExecutor."""
        # Expand queries once
        queries = self.query_transformer.expand_query(question)
        
        vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        
        # Parallel retrieval
        from concurrent.futures import ThreadPoolExecutor
        
        def retrieve_vector(q):
            try:
                return vector_retriever.invoke(q)
            except Exception as e:
                logger.warning(f"Vector retrieval failed for '{q}': {e}")
                return []
                
        def retrieve_bm25(q):
            try:
                self.bm25_retriever.k = k
                return self.bm25_retriever.invoke(q)
            except Exception as e:
                logger.warning(f"BM25 retrieval failed for '{q}': {e}")
                return []

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Concurrently fetch vector and BM25 matching documents across all queries
            vector_futures = [executor.submit(retrieve_vector, q) for q in queries]
            bm25_futures = [executor.submit(retrieve_bm25, q) for q in queries] if self.bm25_retriever else []
            
            vector_results = [f.result() for f in vector_futures]
            bm25_results = [f.result() for f in bm25_futures]

        # Flatten and deduplicate lists
        vector_docs = []
        seen_vector = set()
        for docs_list in vector_results:
            for doc in docs_list:
                key = doc.page_content.strip()
                if key not in seen_vector:
                    seen_vector.add(key)
                    vector_docs.append(doc)
                    
        bm25_docs = []
        seen_bm25 = set()
        for docs_list in bm25_results:
            for doc in docs_list:
                key = doc.page_content.strip()
                if key not in seen_bm25:
                    seen_bm25.add(key)
                    bm25_docs.append(doc)

        # Reciprocal Rank Fusion
        docs = self._reciprocal_rank_fusion(vector_docs, bm25_docs)[:k]

        # GraphRAG Context Enrichment
        if self.graph and self.bm25_retriever:
            doc_lookup = {d.metadata.get("name"): d for d in self.bm25_retriever.docs if d.metadata.get("name")}
            graph_context_docs = []
            
            for doc in docs:
                name = doc.metadata.get("name")
                if name and self.graph.has_node(name):
                    try:
                        neighbors = list(self.graph.predecessors(name)) + list(self.graph.successors(name))
                        for n in neighbors[:3]:  # Top 3 neighbors per chunk
                            if n in doc_lookup and doc_lookup[n] not in docs and doc_lookup[n] not in graph_context_docs:
                                extra_doc = doc_lookup[n]
                                extra_doc.metadata["type"] = extra_doc.metadata.get("type", "") + " (Graph Context)"
                                graph_context_docs.append(extra_doc)
                    except Exception as e:
                        logger.warning(f"Graph traversal failed for {name}: {e}")
                        
            docs.extend(graph_context_docs)

        sources = [
            f"{d.metadata.get('file', '?')}:{d.metadata.get('line_start', '?')}"
            for d in docs
        ]
        return docs, sources

    def query(
        self,
        question: str,
        k: int = 6,
        chat_history: Optional[list[dict]] = None,
    ) -> dict:
        """Answer a question about the codebase using RAG.

        Args:
            question: Natural language question about the code.
            k: Number of chunks to retrieve (default: 6).
            chat_history: Optional list of previous messages for context.

        Returns:
            Dict with 'answer', 'sources', and 'chunks_used'.
        """
        # Condense follow-up questions using chat history
        standalone_question = self._condense_question(
            question, chat_history or []
        )

        # Retrieve documents concurrently
        docs, sources = self._retrieve_and_fuse(standalone_question, k)

        if not docs:
            return {
                "answer": "I couldn't find any relevant code in the indexed repository. "
                          "Try rephrasing your question or make sure the repository "
                          "has been indexed correctly.",
                "sources": [],
                "chunks_used": 0,
            }

        # Format context and build prompt
        context = self._format_context(docs)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(repo_name=self.repo_name)),
            HumanMessage(content=QUERY_PROMPT.format(
                repo_name=self.repo_name,
                context=context,
                question=standalone_question,
            )),
        ]

        answer = self.llm.invoke(messages).content

        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(docs),
        }

    async def aquery_stream(
        self,
        question: str,
        k: int = 6,
        chat_history: Optional[list[dict]] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream an answer token by token (for SSE endpoints).

        Yields dicts with either:
        - {"type": "token", "content": "..."} for each token
        - {"type": "sources", "sources": [...]} at the end
        - {"type": "done"} when streaming is complete

        Args:
            question: Natural language question.
            k: Number of chunks to retrieve.
            chat_history: Optional conversation history.
        """
        # Condense follow-up questions using chat history
        standalone_question = self._condense_question(
            question, chat_history or []
        )

        # Retrieve documents concurrently
        docs, sources = self._retrieve_and_fuse(standalone_question, k)

        if not docs:
            yield {
                "type": "token",
                "content": "I couldn't find any relevant code in the indexed repository.",
            }
            yield {"type": "done"}
            return

        context = self._format_context(docs)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(repo_name=self.repo_name)),
            HumanMessage(content=QUERY_PROMPT.format(
                repo_name=self.repo_name,
                context=context,
                question=standalone_question,
            )),
        ]

        # Stream tokens
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield {"type": "token", "content": chunk.content}

        # Send sources at the end
        yield {"type": "sources", "sources": sources}
        yield {"type": "done"}

    def get_collection_stats(self) -> dict:
        """Get statistics about the indexed collection."""
        try:
            count = self.vectorstore._collection.count()
            return {
                "repo": self.repo_name,
                "chunks": count,
                "status": "ready",
            }
        except Exception as e:
            return {
                "repo": self.repo_name,
                "chunks": 0,
                "status": f"error: {e}",
            }
