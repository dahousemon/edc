"""Document ingestion utilities for the knowledge base."""
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from app.knowledge.chunking import chunk_text, chunk_by_headers

logger = logging.getLogger(__name__)


async def fetch_url_content(url: str) -> tuple[str, str]:
    """
    Fetch content from a URL.

    Returns:
        Tuple of (content, content_type)
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "text/html")
        return response.text, content_type


def extract_text_from_html(html: str) -> tuple[str, str]:
    """
    Extract clean text from HTML.

    Returns:
        Tuple of (title, content)
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Get title
    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()

    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()

    # Get text
    text = soup.get_text(separator='\n\n')

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n\n'.join(chunk for chunk in chunks if chunk)

    return title, text


async def ingest_url(
    url: str,
    category: str = "webpage",
    chunk_size: int = 500,
) -> List[Dict[str, Any]]:
    """
    Ingest content from a URL into chunks.

    Args:
        url: URL to fetch
        category: Document category
        chunk_size: Target chunk size

    Returns:
        List of document chunks with metadata
    """
    try:
        html_content, content_type = await fetch_url_content(url)

        if "html" in content_type:
            title, text_content = extract_text_from_html(html_content)
        else:
            title = url.split("/")[-1]
            text_content = html_content

        # Chunk the content
        chunks = chunk_text(text_content, chunk_size=chunk_size)

        documents = []
        parent_id = str(uuid4())

        for i, chunk_content in enumerate(chunks):
            documents.append({
                "id": str(uuid4()),
                "title": f"{title} (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else title,
                "content": chunk_content,
                "source": url,
                "category": category,
                "doc_type": "webpage",
                "chunk_index": i,
                "total_chunks": len(chunks),
                "parent_doc_id": parent_id,
                "metadata": {
                    "original_title": title,
                    "url": url,
                },
            })

        logger.info(f"Ingested {len(documents)} chunks from {url}")
        return documents

    except Exception as e:
        logger.error(f"Error ingesting URL {url}: {e}")
        raise


def ingest_document(
    content: str,
    title: str,
    source: Optional[str] = None,
    category: str = "document",
    doc_type: str = "text",
    chunk_size: int = 500,
    metadata: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Ingest a document into chunks.

    Args:
        content: Document content
        title: Document title
        source: Source reference
        category: Document category
        doc_type: Document type
        chunk_size: Target chunk size
        metadata: Additional metadata

    Returns:
        List of document chunks with metadata
    """
    # Determine chunking strategy based on doc type
    if doc_type == "markdown":
        header_chunks = chunk_by_headers(content, max_chunk_size=chunk_size)
        chunks = []
        for hc in header_chunks:
            chunk_title = f"{title} - {hc['header']}" if hc['header'] else title
            chunks.append((chunk_title, hc['content']))
    else:
        text_chunks = chunk_text(content, chunk_size=chunk_size)
        chunks = [(f"{title} (Part {i+1})" if len(text_chunks) > 1 else title, c)
                  for i, c in enumerate(text_chunks)]

    documents = []
    parent_id = str(uuid4())

    for i, (chunk_title, chunk_content) in enumerate(chunks):
        doc_metadata = metadata.copy() if metadata else {}
        doc_metadata["original_title"] = title

        documents.append({
            "id": str(uuid4()),
            "title": chunk_title,
            "content": chunk_content,
            "source": source,
            "category": category,
            "doc_type": doc_type,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "parent_doc_id": parent_id,
            "metadata": doc_metadata,
        })

    logger.info(f"Ingested document '{title}' into {len(documents)} chunks")
    return documents


def ingest_faq(
    faqs: List[Dict[str, str]],
    category: str = "faq",
) -> List[Dict[str, Any]]:
    """
    Ingest FAQ entries.

    Each FAQ becomes its own document.

    Args:
        faqs: List of dicts with 'question' and 'answer' keys
        category: Document category

    Returns:
        List of FAQ documents
    """
    documents = []

    for faq in faqs:
        question = faq.get("question", "")
        answer = faq.get("answer", "")

        if question and answer:
            content = f"Question: {question}\n\nAnswer: {answer}"

            documents.append({
                "id": str(uuid4()),
                "title": question[:100],
                "content": content,
                "source": "FAQ Database",
                "category": category,
                "doc_type": "faq",
                "chunk_index": 0,
                "total_chunks": 1,
                "metadata": {
                    "question": question,
                    "answer": answer,
                },
            })

    logger.info(f"Ingested {len(documents)} FAQ entries")
    return documents
