"""RAG (Retrieval Augmented Generation) service for knowledge base queries."""
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations with ChromaDB."""

    COLLECTION_NAME = "aurora_edc_knowledge"

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self._client: Optional[chromadb.Client] = None
        self._collection = None

    @property
    def client(self) -> chromadb.Client:
        """Lazy load ChromaDB client."""
        if self._client is None:
            logger.info(f"Initializing ChromaDB at {settings.chroma_persist_dir}")
            self._client = chromadb.Client(
                ChromaSettings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=settings.chroma_persist_dir,
                    anonymized_telemetry=False,
                )
            )
        return self._client

    @property
    def collection(self):
        """Get or create the knowledge base collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Add a document to the vector store.

        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Document metadata (source, category, etc.)
        """
        embedding = self.embedding_service.embed_text(content)

        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )
        logger.debug(f"Added document {doc_id} to vector store")

    def add_documents(
        self,
        doc_ids: List[str],
        contents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """
        Add multiple documents to the vector store.

        Args:
            doc_ids: List of document identifiers
            contents: List of document contents
            metadatas: List of metadata dicts
        """
        embeddings = self.embedding_service.embed_texts(contents)

        self.collection.add(
            ids=doc_ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(doc_ids)} documents to vector store")

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.

        Args:
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of matching documents with scores
        """
        query_embedding = self.embedding_service.embed_text(query)

        search_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }

        if filter_metadata:
            search_kwargs["where"] = filter_metadata

        results = self.collection.query(**search_kwargs)

        # Format results
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "relevance_score": 1 - results["distances"][0][i] if results["distances"] else 0,
                })

        return formatted_results

    def search_with_reranking(
        self,
        query: str,
        n_results: int = 5,
        initial_fetch: int = 20,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search with initial broad retrieval followed by reranking.

        This retrieves more documents initially, then re-scores them
        for better relevance.

        Args:
            query: Search query
            n_results: Final number of results
            initial_fetch: Number of documents to fetch initially
            filter_metadata: Optional filters

        Returns:
            List of top reranked documents
        """
        # Get initial results
        initial_results = self.search(
            query=query,
            n_results=initial_fetch,
            filter_metadata=filter_metadata,
        )

        if not initial_results:
            return []

        # Simple reranking: boost results that have query terms in content
        query_terms = set(query.lower().split())

        for result in initial_results:
            content_lower = result["content"].lower()
            term_matches = sum(1 for term in query_terms if term in content_lower)
            # Boost score based on term matches
            result["relevance_score"] = result["relevance_score"] * (1 + 0.1 * term_matches)

        # Sort by adjusted relevance score
        initial_results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return initial_results[:n_results]

    def get_context_for_query(
        self,
        query: str,
        n_results: int = 5,
        categories: Optional[List[str]] = None,
    ) -> str:
        """
        Get formatted context string for a query.

        Args:
            query: User's question
            n_results: Number of context chunks
            categories: Optional category filter

        Returns:
            Formatted context string for the LLM
        """
        filter_metadata = None
        if categories:
            filter_metadata = {"category": {"$in": categories}}

        results = self.search_with_reranking(
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata,
        )

        if not results:
            return ""

        # Format context with source citations
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["metadata"].get("source", "Aurora EDC Knowledge Base")
            category = result["metadata"].get("category", "General")
            title = result["metadata"].get("title", "")

            context_parts.append(
                f"[Source {i}: {title or category} - {source}]\n{result['content']}"
            )

        return "\n\n---\n\n".join(context_parts)

    def delete_document(self, doc_id: str) -> None:
        """Delete a document from the vector store."""
        self.collection.delete(ids=[doc_id])
        logger.debug(f"Deleted document {doc_id} from vector store")

    def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> None:
        """Delete documents matching metadata filter."""
        self.collection.delete(where=metadata_filter)
        logger.info(f"Deleted documents matching filter: {metadata_filter}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base collection."""
        return {
            "name": self.COLLECTION_NAME,
            "count": self.collection.count(),
        }

    def clear_collection(self) -> None:
        """Clear all documents from the collection (use with caution)."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self._collection = None
        logger.warning("Cleared entire knowledge base collection")


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
