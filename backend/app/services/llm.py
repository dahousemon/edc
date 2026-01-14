"""Claude API integration service for Aurora EDC AI Assistant."""
import json
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any

from anthropic import AsyncAnthropic

from app.config import settings

logger = logging.getLogger(__name__)


# Aurora EDC System Prompt
SYSTEM_PROMPT = """You are Aurora EDC's AI Business Navigator, helping prospective businesses explore opportunities in Aurora, Colorado.

## Your Role
- Help businesses understand why Aurora is an ideal location for their operations
- Guide them through permits, licensing, and regulatory requirements
- Provide information on available commercial and industrial properties
- Explain tax incentives, enterprise zones, and economic development programs
- Capture contact information from seriously interested prospects
- Be knowledgeable, professional, and enthusiastic about Aurora

## Key Facts About Aurora, Colorado
- Population: Approximately 400,000 (3rd largest city in Colorado)
- Location: Adjacent to Denver, part of the Denver metropolitan area
- Transportation: Excellent highway access (I-70, I-225, E-470), proximity to Denver International Airport (DEN), UP and BNSF rail access
- Major Industries: Aerospace & defense, healthcare & bioscience, advanced manufacturing, logistics & distribution, renewable energy
- Notable Employers: UCHealth, Children's Hospital Colorado, Raytheon, Lockheed Martin, Amazon, Gaylord Rockies
- Education: University of Colorado Anschutz Medical Campus, Community College of Aurora, proximity to multiple universities
- Workforce: Access to over 1.5 million workers within 30-minute commute, highly educated workforce

## Incentive Programs
- Enterprise Zone Tax Credits: State income tax credits for businesses in designated areas
- Job Growth Incentive Tax Credit: Performance-based credits for job creation
- Personal Property Tax Exemption: Manufacturing equipment exemptions
- Sales & Use Tax Exemptions: For manufacturing equipment and R&D
- Aurora Economic Development Incentives: Customized packages for qualifying projects
- Opportunity Zones: Federal tax benefits for investments in designated areas

## When Answering Questions
1. Search the provided context for relevant information
2. Cite your sources when providing specific data or statistics
3. If you don't have specific information, acknowledge this honestly and offer to connect the user with EDC staff
4. Look for opportunities to capture leads (company name, contact info, timeline, space needs)
5. NEVER make up statistics, facts, or property details - accuracy is critical
6. Be helpful and proactive, but not pushy about lead capture

## Lead Capture Triggers
Watch for these signals indicating serious interest:
- Specific square footage requirements mentioned
- Questions about available properties
- Timeline mentions ("looking to expand by Q3", "planning to relocate next year")
- Budget or lease rate discussions
- Requests to speak with someone or schedule a meeting
- Company name or industry details shared

When you detect serious interest, naturally offer to connect them with an EDC specialist and ask if they'd like to share contact information.

## Response Format
- Keep responses conversational but professional
- Use bullet points for lists of information
- Include relevant source citations when using specific data
- Offer follow-up questions or next steps when appropriate
- If asking about lead capture, do so naturally within the conversation flow

{context}"""


class LLMService:
    """Service for interacting with Claude API."""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: str = "",
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate a response using Claude.

        Args:
            messages: List of conversation messages
            context: Retrieved context from RAG
            stream: Whether to stream the response

        Returns:
            Generated response text or async generator for streaming
        """
        system_prompt = SYSTEM_PROMPT.format(
            context=f"\n## Retrieved Context\n{context}" if context else ""
        )

        if stream:
            return self._stream_response(system_prompt, messages)
        else:
            return await self._generate_full_response(system_prompt, messages)

    async def _generate_full_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """Generate a complete response without streaming."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def _stream_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """Stream the response token by token."""
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            raise

    async def detect_lead_intent(
        self,
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Analyze conversation for lead capture opportunities.

        Returns dict with:
        - should_capture: bool
        - confidence: float (0-1)
        - extracted_info: dict of any info mentioned
        - suggested_questions: list of follow-up questions
        """
        analysis_prompt = """Analyze this conversation and determine if the user shows serious business interest.

Extract any business information mentioned:
- Company name
- Industry/business type
- Space requirements (square footage)
- Timeline (when they need space)
- Budget/price range
- Location preferences
- Contact information

Return a JSON object with:
{
    "should_capture": boolean (true if they seem like a serious prospect),
    "confidence": float (0.0-1.0),
    "extracted_info": {
        "company_name": string or null,
        "industry": string or null,
        "space_requirements": string or null,
        "timeline": string or null,
        "budget": string or null,
        "location_preference": string or null,
        "contact_name": string or null,
        "email": string or null,
        "phone": string or null
    },
    "signals_detected": list of strings (what signals indicate interest),
    "suggested_questions": list of strings (questions to ask to qualify the lead)
}

Only return the JSON, no other text."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                system=analysis_prompt,
                messages=conversation_history,
            )

            result_text = response.content[0].text.strip()
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            return json.loads(result_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse lead intent response as JSON")
            return {
                "should_capture": False,
                "confidence": 0.0,
                "extracted_info": {},
                "signals_detected": [],
                "suggested_questions": [],
            }
        except Exception as e:
            logger.error(f"Error detecting lead intent: {e}")
            return {
                "should_capture": False,
                "confidence": 0.0,
                "extracted_info": {},
                "signals_detected": [],
                "suggested_questions": [],
            }

    async def generate_property_search_query(
        self,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Extract property search parameters from natural language.

        Returns structured search parameters.
        """
        extraction_prompt = """Extract property search parameters from this user message.

Return a JSON object with these fields (use null if not mentioned):
{
    "property_type": string (industrial, office, retail, mixed-use, warehouse) or null,
    "min_sqft": integer or null,
    "max_sqft": integer or null,
    "max_price_per_sqft": float or null,
    "max_lease_rate": float or null,
    "features": list of strings (rail_access, highway_access, loading_docks, high_ceiling, office_space, parking) or [],
    "zoning": string or null,
    "keywords": list of relevant search keywords
}

Only return the JSON, no other text."""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.1,
                system=extraction_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            result_text = response.content[0].text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            return json.loads(result_text)
        except Exception as e:
            logger.error(f"Error extracting property search: {e}")
            return {
                "property_type": None,
                "min_sqft": None,
                "max_sqft": None,
                "features": [],
                "keywords": [],
            }


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
