"""Document chunking strategies for the knowledge base."""
import re
from typing import List, Optional


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    separator: str = "\n\n",
) -> List[str]:
    """
    Split text into chunks with optional overlap.

    Args:
        text: Text to chunk
        chunk_size: Target size for each chunk (in characters)
        overlap: Number of characters to overlap between chunks
        separator: Preferred split point

    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # Find the end of this chunk
        chunk_end = current_pos + chunk_size

        if chunk_end >= len(text):
            # Last chunk - take the rest
            chunks.append(text[current_pos:].strip())
            break

        # Try to find a good break point
        chunk_text_segment = text[current_pos:chunk_end]

        # Look for separator (paragraph break)
        sep_pos = chunk_text_segment.rfind(separator)
        if sep_pos > chunk_size * 0.3:  # Found separator in latter 70% of chunk
            chunk_end = current_pos + sep_pos + len(separator)
        else:
            # Look for sentence end
            sentence_end = _find_sentence_end(chunk_text_segment)
            if sentence_end and sentence_end > chunk_size * 0.3:
                chunk_end = current_pos + sentence_end + 1

        # Add the chunk
        chunk = text[current_pos:chunk_end].strip()
        if chunk:
            chunks.append(chunk)

        # Move to next position with overlap
        current_pos = chunk_end - overlap

    return chunks


def _find_sentence_end(text: str) -> Optional[int]:
    """Find the last sentence-ending position in text."""
    # Look for sentence endings: . ! ? followed by space or end
    pattern = r'[.!?](?:\s|$)'
    matches = list(re.finditer(pattern, text))
    if matches:
        return matches[-1].start()
    return None


def chunk_by_headers(
    text: str,
    max_chunk_size: int = 1000,
) -> List[dict]:
    """
    Split text by markdown headers, keeping sections together.

    Args:
        text: Markdown text to chunk
        max_chunk_size: Maximum chunk size

    Returns:
        List of dicts with 'header' and 'content' keys
    """
    # Split by headers (# ## ### etc)
    header_pattern = r'^(#{1,6})\s+(.+)$'
    lines = text.split('\n')

    chunks = []
    current_header = None
    current_content = []

    for line in lines:
        header_match = re.match(header_pattern, line)

        if header_match:
            # Save previous section if exists
            if current_content:
                content = '\n'.join(current_content).strip()
                if content:
                    chunks.append({
                        'header': current_header,
                        'content': content,
                    })
                current_content = []

            current_header = header_match.group(2)
        else:
            current_content.append(line)

    # Don't forget the last section
    if current_content:
        content = '\n'.join(current_content).strip()
        if content:
            chunks.append({
                'header': current_header,
                'content': content,
            })

    # Split any chunks that are too large
    final_chunks = []
    for chunk in chunks:
        content = chunk['content']
        if len(content) > max_chunk_size:
            # Split this chunk further
            sub_chunks = chunk_text(content, chunk_size=max_chunk_size, overlap=50)
            for i, sub_chunk in enumerate(sub_chunks):
                final_chunks.append({
                    'header': f"{chunk['header']} (Part {i+1})" if chunk['header'] else None,
                    'content': sub_chunk,
                })
        else:
            final_chunks.append(chunk)

    return final_chunks


def chunk_document(
    content: str,
    doc_type: str,
    chunk_size: int = 500,
) -> List[str]:
    """
    Chunk a document based on its type.

    Args:
        content: Document content
        doc_type: Type of document (markdown, plain, html)
        chunk_size: Target chunk size

    Returns:
        List of text chunks
    """
    if doc_type == "markdown":
        header_chunks = chunk_by_headers(content, max_chunk_size=chunk_size)
        return [c['content'] for c in header_chunks]
    elif doc_type == "html":
        # Strip HTML tags for chunking
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text(separator='\n\n')
        return chunk_text(text, chunk_size=chunk_size)
    else:
        # Plain text
        return chunk_text(content, chunk_size=chunk_size)


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.

    Uses a simple heuristic: ~4 characters per token for English text.
    """
    return len(text) // 4
