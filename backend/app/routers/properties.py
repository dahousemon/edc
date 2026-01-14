"""Property search API endpoints."""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Property, get_db
from app.models.schemas import PropertySearchRequest, PropertyResponse, PropertyListResponse
from app.services.llm import get_llm_service, LLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("/", response_model=PropertyListResponse)
async def list_properties(
    property_type: Optional[str] = Query(None),
    min_sqft: Optional[int] = Query(None, ge=0),
    max_sqft: Optional[int] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    zoning: Optional[str] = Query(None),
    features: Optional[str] = Query(None, description="Comma-separated feature list"),
    available_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List properties with optional filters.
    """
    query = select(Property)
    count_query = select(func.count(Property.id))

    if available_only:
        query = query.where(Property.is_available == True)
        count_query = count_query.where(Property.is_available == True)

    if property_type:
        query = query.where(Property.property_type == property_type)
        count_query = count_query.where(Property.property_type == property_type)

    if min_sqft:
        query = query.where(Property.available_sqft >= min_sqft)
        count_query = count_query.where(Property.available_sqft >= min_sqft)

    if max_sqft:
        query = query.where(Property.available_sqft <= max_sqft)
        count_query = count_query.where(Property.available_sqft <= max_sqft)

    if max_price:
        query = query.where(
            or_(
                Property.price_per_sqft <= max_price,
                Property.lease_rate <= max_price
            )
        )
        count_query = count_query.where(
            or_(
                Property.price_per_sqft <= max_price,
                Property.lease_rate <= max_price
            )
        )

    if zoning:
        query = query.where(Property.zoning == zoning)
        count_query = count_query.where(Property.zoning == zoning)

    # Get total
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Property.available_sqft.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    properties = result.scalars().all()

    # Filter by features if specified (done in Python as JSON field)
    if features:
        feature_list = [f.strip().lower() for f in features.split(",")]
        properties = [
            p for p in properties
            if any(f in [feat.lower() for feat in (p.features or [])] for f in feature_list)
        ]

    return PropertyListResponse(
        properties=[PropertyResponse.model_validate(p) for p in properties],
        total=total,
    )


@router.post("/search", response_model=PropertyListResponse)
async def search_properties_natural(
    query: str,
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Search properties using natural language.

    The query is processed by the LLM to extract search parameters.
    """
    # Extract search parameters from natural language
    params = await llm_service.generate_property_search_query(query)

    # Build database query
    db_query = select(Property).where(Property.is_available == True)

    if params.get("property_type"):
        db_query = db_query.where(Property.property_type == params["property_type"])

    if params.get("min_sqft"):
        db_query = db_query.where(Property.available_sqft >= params["min_sqft"])

    if params.get("max_sqft"):
        db_query = db_query.where(Property.available_sqft <= params["max_sqft"])

    if params.get("max_price_per_sqft"):
        db_query = db_query.where(Property.price_per_sqft <= params["max_price_per_sqft"])

    if params.get("max_lease_rate"):
        db_query = db_query.where(Property.lease_rate <= params["max_lease_rate"])

    if params.get("zoning"):
        db_query = db_query.where(Property.zoning == params["zoning"])

    db_query = db_query.order_by(Property.available_sqft.desc()).limit(20)

    result = await db.execute(db_query)
    properties = list(result.scalars().all())

    # Filter by features if specified
    if params.get("features"):
        feature_set = set(f.lower() for f in params["features"])
        properties = [
            p for p in properties
            if feature_set.intersection(set(f.lower() for f in (p.features or [])))
        ]

    return PropertyListResponse(
        properties=[PropertyResponse.model_validate(p) for p in properties],
        total=len(properties),
    )


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get details for a specific property.
    """
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property = result.scalar_one_or_none()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    return PropertyResponse.model_validate(property)


@router.get("/types/list")
async def get_property_types(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of available property types.
    """
    result = await db.execute(
        select(Property.property_type)
        .where(Property.is_available == True)
        .distinct()
    )
    types = [row[0] for row in result.all() if row[0]]

    return {"property_types": types}


@router.get("/zoning/list")
async def get_zoning_types(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of available zoning types.
    """
    result = await db.execute(
        select(Property.zoning)
        .where(Property.is_available == True)
        .distinct()
    )
    zones = [row[0] for row in result.all() if row[0]]

    return {"zoning_types": zones}


@router.get("/features/list")
async def get_property_features(
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of all property features.
    """
    result = await db.execute(
        select(Property.features)
        .where(Property.is_available == True)
    )

    all_features = set()
    for row in result.all():
        if row[0]:
            all_features.update(row[0])

    return {"features": sorted(list(all_features))}


@router.get("/stats/summary")
async def get_property_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics for available properties.
    """
    # Total available
    total_result = await db.execute(
        select(func.count(Property.id))
        .where(Property.is_available == True)
    )
    total = total_result.scalar()

    # By type
    type_result = await db.execute(
        select(Property.property_type, func.count(Property.id))
        .where(Property.is_available == True)
        .group_by(Property.property_type)
    )
    by_type = dict(type_result.all())

    # Total available sqft
    sqft_result = await db.execute(
        select(func.sum(Property.available_sqft))
        .where(Property.is_available == True)
    )
    total_sqft = sqft_result.scalar() or 0

    # Average price per sqft
    avg_price_result = await db.execute(
        select(func.avg(Property.price_per_sqft))
        .where(
            and_(
                Property.is_available == True,
                Property.price_per_sqft.isnot(None)
            )
        )
    )
    avg_price = avg_price_result.scalar()

    # Average lease rate
    avg_lease_result = await db.execute(
        select(func.avg(Property.lease_rate))
        .where(
            and_(
                Property.is_available == True,
                Property.lease_rate.isnot(None)
            )
        )
    )
    avg_lease = avg_lease_result.scalar()

    return {
        "total_available": total,
        "by_type": by_type,
        "total_available_sqft": total_sqft,
        "avg_price_per_sqft": round(avg_price, 2) if avg_price else None,
        "avg_lease_rate": round(avg_lease, 2) if avg_lease else None,
    }
