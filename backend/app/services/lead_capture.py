"""Lead capture and scoring service."""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Lead, Conversation

logger = logging.getLogger(__name__)


class LeadCaptureService:
    """Service for lead capture, scoring, and management."""

    # Scoring weights for different lead attributes
    SCORING_WEIGHTS = {
        "company_name": 15,          # Has company name
        "contact_name": 10,          # Has contact name
        "email": 20,                 # Has email (high value)
        "phone": 15,                 # Has phone number
        "industry": 10,              # Specified industry
        "space_requirements": 15,    # Specific space needs
        "timeline": 15,              # Has timeline
        "budget": 10,                # Mentioned budget
    }

    # Industry bonuses (target industries for Aurora)
    INDUSTRY_BONUSES = {
        "aerospace": 10,
        "defense": 10,
        "manufacturing": 10,
        "advanced manufacturing": 15,
        "healthcare": 8,
        "bioscience": 10,
        "logistics": 8,
        "distribution": 8,
        "warehouse": 5,
        "technology": 8,
        "renewable energy": 10,
        "clean energy": 10,
    }

    # Timeline urgency bonuses
    TIMELINE_BONUSES = {
        "immediate": 15,
        "asap": 15,
        "q1": 12,
        "q2": 10,
        "q3": 8,
        "q4": 6,
        "this year": 8,
        "next year": 4,
        "6 months": 10,
        "3 months": 12,
    }

    async def create_lead(
        self,
        db: AsyncSession,
        lead_data: Dict[str, Any],
        conversation_id: Optional[UUID] = None,
    ) -> Lead:
        """
        Create a new lead from captured data.

        Args:
            db: Database session
            lead_data: Lead information dict
            conversation_id: Associated conversation ID

        Returns:
            Created Lead object
        """
        # Calculate lead score
        score = self.calculate_score(lead_data)

        lead = Lead(
            conversation_id=conversation_id,
            company_name=lead_data.get("company_name"),
            contact_name=lead_data.get("contact_name"),
            email=lead_data.get("email"),
            phone=lead_data.get("phone"),
            industry=lead_data.get("industry"),
            space_requirements=lead_data.get("space_requirements"),
            timeline=lead_data.get("timeline"),
            budget=lead_data.get("budget"),
            location_preference=lead_data.get("location_preference"),
            notes=lead_data.get("notes"),
            score=score,
            status="new",
            source=lead_data.get("source", "chatbot"),
        )

        db.add(lead)
        await db.commit()
        await db.refresh(lead)

        # Update conversation if linked
        if conversation_id:
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.lead_captured = True
                conversation.lead_id = lead.id
                await db.commit()

        logger.info(f"Created lead {lead.id} with score {score}")
        return lead

    def calculate_score(self, lead_data: Dict[str, Any]) -> int:
        """
        Calculate a lead score (0-100) based on available information.

        Args:
            lead_data: Lead information dict

        Returns:
            Integer score 0-100
        """
        score = 0

        # Base scoring for provided fields
        for field, weight in self.SCORING_WEIGHTS.items():
            if lead_data.get(field):
                score += weight

        # Industry bonus
        industry = (lead_data.get("industry") or "").lower()
        for keyword, bonus in self.INDUSTRY_BONUSES.items():
            if keyword in industry:
                score += bonus
                break

        # Timeline urgency bonus
        timeline = (lead_data.get("timeline") or "").lower()
        for keyword, bonus in self.TIMELINE_BONUSES.items():
            if keyword in timeline:
                score += bonus
                break

        # Space requirements bonus (larger = more valuable, typically)
        space_req = lead_data.get("space_requirements", "")
        if space_req:
            # Try to extract square footage
            import re
            numbers = re.findall(r'[\d,]+', space_req)
            if numbers:
                try:
                    sqft = int(numbers[0].replace(",", ""))
                    if sqft >= 100000:
                        score += 10
                    elif sqft >= 50000:
                        score += 7
                    elif sqft >= 20000:
                        score += 5
                    elif sqft >= 10000:
                        score += 3
                except ValueError:
                    pass

        # Cap at 100
        return min(score, 100)

    async def update_lead(
        self,
        db: AsyncSession,
        lead_id: UUID,
        updates: Dict[str, Any],
    ) -> Optional[Lead]:
        """
        Update an existing lead.

        Args:
            db: Database session
            lead_id: Lead ID
            updates: Fields to update

        Returns:
            Updated Lead or None
        """
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        lead = result.scalar_one_or_none()

        if not lead:
            return None

        for field, value in updates.items():
            if hasattr(lead, field) and value is not None:
                setattr(lead, field, value)

        # Recalculate score if data fields changed
        data_fields = {"company_name", "contact_name", "email", "phone",
                       "industry", "space_requirements", "timeline", "budget"}
        if data_fields.intersection(updates.keys()):
            lead.score = self.calculate_score({
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "email": lead.email,
                "phone": lead.phone,
                "industry": lead.industry,
                "space_requirements": lead.space_requirements,
                "timeline": lead.timeline,
                "budget": lead.budget,
            })

        await db.commit()
        await db.refresh(lead)
        return lead

    async def get_leads(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        min_score: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Lead], int]:
        """
        Get leads with optional filters.

        Returns:
            Tuple of (leads list, total count)
        """
        query = select(Lead)
        count_query = select(func.count(Lead.id))

        if status:
            query = query.where(Lead.status == status)
            count_query = count_query.where(Lead.status == status)

        if assigned_to:
            query = query.where(Lead.assigned_to == assigned_to)
            count_query = count_query.where(Lead.assigned_to == assigned_to)

        if min_score:
            query = query.where(Lead.score >= min_score)
            count_query = count_query.where(Lead.score >= min_score)

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get leads with pagination
        query = query.order_by(Lead.score.desc(), Lead.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        leads = result.scalars().all()

        return list(leads), total

    async def get_lead_by_id(
        self,
        db: AsyncSession,
        lead_id: UUID,
    ) -> Optional[Lead]:
        """Get a single lead by ID."""
        result = await db.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    def should_prompt_for_info(
        self,
        extracted_info: Dict[str, Any],
        confidence: float,
    ) -> tuple[bool, List[str]]:
        """
        Determine if we should prompt for more lead information.

        Args:
            extracted_info: Currently extracted information
            confidence: Lead detection confidence

        Returns:
            Tuple of (should_prompt, list of missing fields to ask about)
        """
        if confidence < 0.5:
            return False, []

        # Priority fields we want
        priority_fields = ["company_name", "email", "space_requirements", "timeline"]
        missing = []

        for field in priority_fields:
            if not extracted_info.get(field):
                missing.append(field)

        # Only prompt if we have at least some info and are missing key fields
        has_some_info = any(extracted_info.get(f) for f in self.SCORING_WEIGHTS.keys())

        if has_some_info and missing:
            return True, missing

        return False, []


# Singleton instance
_lead_capture_service: Optional[LeadCaptureService] = None


def get_lead_capture_service() -> LeadCaptureService:
    """Get or create lead capture service instance."""
    global _lead_capture_service
    if _lead_capture_service is None:
        _lead_capture_service = LeadCaptureService()
    return _lead_capture_service
