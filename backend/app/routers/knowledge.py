"""Knowledge base management API endpoints."""
import logging
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Document, get_db
from app.models.schemas import (
    DocumentUploadRequest,
    DocumentResponse,
    DocumentListResponse,
)
from app.services.rag import get_rag_service, RAGService
from app.knowledge.chunking import chunk_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    request: DocumentUploadRequest,
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Add a new document to the knowledge base.
    """
    # Create document record
    doc = Document(
        title=request.title,
        content=request.content,
        source=request.source,
        category=request.category,
        doc_type=request.doc_type,
        metadata=request.metadata,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Add to vector store
    rag_service.add_document(
        doc_id=str(doc.id),
        content=request.content,
        metadata={
            "title": request.title,
            "source": request.source or "",
            "category": request.category,
            "doc_type": request.doc_type,
        },
    )

    return DocumentResponse.model_validate(doc)


@router.post("/documents/bulk")
async def create_documents_bulk(
    documents: List[DocumentUploadRequest],
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Add multiple documents to the knowledge base.
    """
    doc_ids = []
    contents = []
    metadatas = []

    for doc_request in documents:
        doc = Document(
            title=doc_request.title,
            content=doc_request.content,
            source=doc_request.source,
            category=doc_request.category,
            doc_type=doc_request.doc_type,
            metadata=doc_request.metadata,
        )
        db.add(doc)
        await db.flush()  # Get the ID without committing

        doc_ids.append(str(doc.id))
        contents.append(doc_request.content)
        metadatas.append({
            "title": doc_request.title,
            "source": doc_request.source or "",
            "category": doc_request.category,
            "doc_type": doc_request.doc_type,
        })

    await db.commit()

    # Add all to vector store
    rag_service.add_documents(doc_ids, contents, metadatas)

    return {"status": "created", "count": len(documents)}


@router.post("/documents/chunked")
async def create_chunked_document(
    title: str,
    content: str,
    source: Optional[str] = None,
    category: str = "general",
    chunk_size: int = Query(500, ge=100, le=2000),
    chunk_overlap: int = Query(50, ge=0, le=200),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Add a large document by automatically chunking it.
    """
    chunks = chunk_text(content, chunk_size=chunk_size, overlap=chunk_overlap)

    parent_id = uuid.uuid4()
    doc_ids = []
    contents = []
    metadatas = []

    for i, chunk_content in enumerate(chunks):
        doc = Document(
            title=f"{title} (Part {i+1}/{len(chunks)})",
            content=chunk_content,
            source=source,
            category=category,
            doc_type="chunked",
            chunk_index=i,
            total_chunks=len(chunks),
            parent_doc_id=parent_id,
        )
        db.add(doc)
        await db.flush()

        doc_ids.append(str(doc.id))
        contents.append(chunk_content)
        metadatas.append({
            "title": title,
            "source": source or "",
            "category": category,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "parent_doc_id": str(parent_id),
        })

    await db.commit()

    # Add all chunks to vector store
    rag_service.add_documents(doc_ids, contents, metadatas)

    return {
        "status": "created",
        "parent_id": str(parent_id),
        "chunks_created": len(chunks),
    }


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    category: Optional[str] = Query(None),
    doc_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List documents in the knowledge base.
    """
    query = select(Document).where(Document.is_active == True)
    count_query = select(func.count(Document.id)).where(Document.is_active == True)

    if category:
        query = query.where(Document.category == category)
        count_query = count_query.where(Document.category == category)

    if doc_type:
        query = query.where(Document.doc_type == doc_type)
        count_query = count_query.where(Document.doc_type == doc_type)

    if search:
        search_filter = Document.title.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific document.
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.model_validate(doc)


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get document content.
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc.id),
        "title": doc.title,
        "content": doc.content,
        "category": doc.category,
        "source": doc.source,
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Delete a document from the knowledge base.
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector store
    rag_service.delete_document(str(document_id))

    # Soft delete from database
    doc.is_active = False
    await db.commit()

    return {"status": "deleted"}


@router.get("/search")
async def search_knowledge_base(
    query: str = Query(..., min_length=2),
    category: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Search the knowledge base using semantic search.
    """
    filter_metadata = None
    if category:
        filter_metadata = {"category": category}

    results = rag_service.search(
        query=query,
        n_results=limit,
        filter_metadata=filter_metadata,
    )

    return {
        "query": query,
        "results": results,
    }


@router.get("/stats")
async def get_knowledge_stats(
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Get statistics about the knowledge base.
    """
    # Database stats
    total_result = await db.execute(
        select(func.count(Document.id)).where(Document.is_active == True)
    )
    total_docs = total_result.scalar()

    # By category
    category_result = await db.execute(
        select(Document.category, func.count(Document.id))
        .where(Document.is_active == True)
        .group_by(Document.category)
    )
    by_category = dict(category_result.all())

    # By type
    type_result = await db.execute(
        select(Document.doc_type, func.count(Document.id))
        .where(Document.is_active == True)
        .group_by(Document.doc_type)
    )
    by_type = dict(type_result.all())

    # Vector store stats
    vector_stats = rag_service.get_collection_stats()

    return {
        "total_documents": total_docs,
        "by_category": by_category,
        "by_type": by_type,
        "vector_store": vector_stats,
    }


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all document categories.
    """
    result = await db.execute(
        select(Document.category)
        .where(Document.is_active == True)
        .distinct()
    )
    categories = [row[0] for row in result.all() if row[0]]

    return {"categories": categories}
