#!/usr/bin/env python3
"""
Seed the Aurora EDC knowledge base with sample data.

This script populates the vector store with Aurora-specific information
for the AI assistant to use when answering questions.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.rag import get_rag_service
from app.knowledge.ingestion import ingest_document, ingest_faq


# Aurora EDC Knowledge Base Content
AURORA_OVERVIEW = """
# Aurora, Colorado - Business Overview

Aurora is the third-largest city in Colorado with a population of approximately 400,000 residents. Located in the Denver metropolitan area, Aurora offers businesses exceptional access to markets, workforce, and infrastructure.

## Key Facts
- Population: ~400,000 (2024 estimate)
- Area: 160+ square miles spanning three counties (Arapahoe, Adams, Douglas)
- Location: Eastern Denver metropolitan area
- Elevation: 5,471 feet

## Strategic Location
Aurora's location provides unparalleled access:
- Adjacent to Denver International Airport (DEN) - one of the nation's busiest airports
- Interstate highway access: I-70, I-225, E-470
- Union Pacific and BNSF rail service
- RTD light rail and bus service

## Economic Profile
- Diverse economy spanning aerospace, healthcare, technology, manufacturing, and logistics
- Home to major employers including UCHealth, Children's Hospital Colorado, and Raytheon
- Growing tech hub with particular strength in aerospace and defense
- Strong small business ecosystem with over 15,000 registered businesses
"""

INCENTIVES_CONTENT = """
# Aurora Business Incentives and Programs

## Enterprise Zone Tax Credits
Aurora has designated Enterprise Zones offering state income tax credits:
- Investment Tax Credit: 3% credit on qualified equipment purchases
- Job Training Credit: Up to $1,200 per employee for qualifying training
- New Employee Credit: $1,100 per new full-time employee
- R&D Credit: 3% credit on qualified research expenditures
- Vacant Building Rehabilitation Credit: 25% of rehabilitation costs

## Job Growth Incentive Tax Credit (JGITC)
Performance-based state tax credit for businesses creating new jobs:
- Credit equals up to 50% of FICA taxes on new employees
- Requires minimum of 20 new jobs
- Jobs must pay at least 100% of average county wage
- Available for up to 8 years

## Personal Property Tax Exemption
Manufacturing equipment exemption:
- Qualified businesses can receive exemption on manufacturing equipment
- Applies to machinery and equipment used in manufacturing
- Must be new equipment placed in service in Colorado

## Sales & Use Tax Exemptions
- Manufacturing equipment purchases exempt from sales tax
- Research and development equipment exemptions
- Pollution control equipment exemptions

## Aurora-Specific Programs
- Aurora Economic Development Incentives: Customized packages for qualifying projects
- Fee waivers and rebates for economic development projects
- Infrastructure cost-sharing for major developments
- Expedited permitting for priority projects

## Opportunity Zones
Aurora has federally designated Opportunity Zones offering:
- Tax deferral on capital gains invested in Opportunity Zone funds
- Potential permanent exclusion of gains on new investments held 10+ years
- Located in strategic areas across the city
"""

WORKFORCE_CONTENT = """
# Aurora Workforce & Demographics

## Workforce Overview
- Access to 1.5+ million workers within 30-minute commute
- Highly educated workforce: 40%+ with bachelor's degree or higher
- Strong technical and healthcare talent pipeline
- Multilingual workforce with 130+ languages spoken

## Education & Training
- University of Colorado Anschutz Medical Campus (largest academic health center in Rocky Mountain region)
- Community College of Aurora
- Pickens Technical College
- Multiple universities within Denver metro area (DU, CU Denver, MSU Denver, Regis)

## Industry Workforce Strengths
- Healthcare & Bioscience: 50,000+ healthcare workers in Aurora
- Aerospace & Defense: Deep talent pool from nearby military installations
- Advanced Manufacturing: Strong vocational training programs
- Technology: Growing IT and software development workforce

## Labor Market Statistics
- Unemployment rate consistently below national average
- Competitive wages across industries
- Strong workforce participation rate
- Diverse age demographics supporting workforce sustainability

## Training Resources
- Workforce Innovation and Opportunity Act (WIOA) funding
- Industry-specific training partnerships
- Apprenticeship programs in manufacturing and skilled trades
- Healthcare career pathways programs
"""

MAJOR_EMPLOYERS = """
# Major Employers in Aurora

## Healthcare
- UCHealth University of Colorado Hospital: 10,000+ employees
- Children's Hospital Colorado: 8,000+ employees
- Medical Center of Aurora: 1,500+ employees
- Kaiser Permanente: 1,000+ employees

## Aerospace & Defense
- Raytheon: 3,000+ employees
- Lockheed Martin (nearby): 2,500+ employees
- Northrop Grumman: 500+ employees
- Ball Aerospace: 500+ employees

## Distribution & Logistics
- Amazon Fulfillment Centers: 5,000+ employees
- FedEx Ground: 1,000+ employees
- UPS: 500+ employees

## Retail & Hospitality
- Gaylord Rockies Resort: 2,500+ employees
- Aurora Mall / Town Center: 2,000+ employees combined

## Government & Education
- City of Aurora: 4,000+ employees
- Aurora Public Schools: 6,000+ employees
- Cherry Creek School District: 1,500+ (Aurora portion)

## Other Major Employers
- Boeing: 500+ employees
- Comcast: 500+ employees
- Panasonic Enterprise Solutions: 300+ employees
"""

PERMIT_GUIDE = """
# Aurora Business Permits & Licensing Guide

## General Business License
All businesses operating in Aurora need a City of Aurora business license:
- Apply online through the City's portal
- Annual renewal required
- Fee varies by business type

## Zoning & Land Use
Before starting a business, verify zoning compliance:
- Check zoning at auroragov.org/zoning
- May require Use by Right approval or Special Use Permit
- Site plan review for commercial development

## Building Permits
Required for construction, renovation, or tenant improvements:
- Submit through Aurora's online permitting system
- Plan review typically 2-4 weeks
- Inspections required at various stages

## Industry-Specific Permits

### Food Service
- Food service license from Tri-County Health Department
- Food handler certifications for employees
- Annual inspections required

### Liquor License
- City of Aurora liquor license
- State of Colorado liquor license
- Public hearing may be required

### Manufacturing
- Air quality permits (if applicable) from Colorado DPHE
- Industrial wastewater permits
- Hazardous materials permits (if applicable)

### Healthcare
- State licensing through CDPHE
- Federal certifications as applicable
- Local occupancy and building permits

## Contact Information
- Business Licensing: (303) 739-7057
- Planning & Development: (303) 739-7250
- Building Permits: (303) 739-7420
"""

PROPERTIES_INFO = """
# Commercial & Industrial Properties in Aurora

## Industrial Space
Aurora offers excellent industrial options:
- I-70 Corridor: Major distribution hub with warehouse and logistics facilities
- Airport Industrial Area: Ideal for air cargo and time-sensitive operations
- E-470 Corridor: Growing industrial development with modern facilities

## Office Space
- Fitzsimons Innovation Campus: Life sciences and healthcare office space
- Downtown Aurora: Traditional office buildings with transit access
- I-225 Corridor: Class A and B office buildings
- Southeast Business District: Emerging office development

## Retail & Mixed-Use
- Aurora Town Center area
- Stanley Marketplace (adaptive reuse success)
- Southlands shopping district
- Original Aurora (Main Street district)

## Available Space Overview
- Industrial vacancy: ~5-7%
- Office vacancy: ~12-15%
- Average industrial lease rate: $8-12/sf NNN
- Average office lease rate: $18-28/sf FSG

## Key Features Available
Many properties offer:
- Rail access (UP/BNSF)
- Highway access (I-70, I-225, E-470)
- Proximity to DEN airport
- High power availability
- Fiber connectivity
"""

TRANSPORTATION = """
# Transportation & Infrastructure in Aurora

## Air
- Denver International Airport (DEN): 10-20 minutes from most Aurora locations
- 5th busiest airport in the US
- Direct flights to 200+ destinations
- Major cargo hub

## Highway
- I-70: East-west transcontinental route
- I-225: North-south through Aurora
- E-470: Beltway connecting to DEN and regional destinations
- US-40 (Colfax Avenue): Historic route through Aurora

## Rail
- Union Pacific Railroad: Freight service
- BNSF Railway: Freight service
- RTD Light Rail: A, R, and N lines serve Aurora
- Future RTD expansions planned

## Transit
- RTD bus service throughout Aurora
- FlexRide on-demand service
- Bustang intercity service
- Free MallRide and MetroRide in downtown Denver

## Infrastructure
- Aurora Water: Reliable water supply from diverse sources
- Xcel Energy: Electric and natural gas
- Multiple fiber providers for high-speed internet
- Enterprise-grade telecom facilities
"""

# FAQs
FAQS = [
    {
        "question": "What incentives are available for businesses relocating to Aurora?",
        "answer": "Aurora offers several incentives including Enterprise Zone tax credits (investment, job training, new employee, and R&D credits), Job Growth Incentive Tax Credits, personal property tax exemptions for manufacturing equipment, sales & use tax exemptions, and customized incentive packages for qualifying projects. The city also has designated Opportunity Zones offering federal tax benefits."
    },
    {
        "question": "How close is Aurora to Denver International Airport?",
        "answer": "Aurora is exceptionally well-positioned relative to Denver International Airport (DEN). Most Aurora locations are 10-20 minutes from the airport. The city has direct highway access via I-70, E-470, and Pena Boulevard, making it ideal for businesses requiring frequent air travel or air cargo operations."
    },
    {
        "question": "What industries are strong in Aurora?",
        "answer": "Aurora has particular strength in Healthcare & Bioscience (home to UC Anschutz Medical Campus and Children's Hospital), Aerospace & Defense (Raytheon, Lockheed Martin nearby), Advanced Manufacturing, Logistics & Distribution (Amazon, FedEx), and Technology. The city's diverse economy also includes significant retail, hospitality, and professional services sectors."
    },
    {
        "question": "What is the workforce like in Aurora?",
        "answer": "Aurora provides access to over 1.5 million workers within a 30-minute commute. The workforce is highly educated (40%+ with bachelor's degree or higher), multilingual (130+ languages spoken), and diverse. Strong training pipelines exist through UC Anschutz, Community College of Aurora, and various technical programs."
    },
    {
        "question": "How do I get a business license in Aurora?",
        "answer": "To obtain a business license in Aurora, apply online through the City's portal at auroragov.org. All businesses operating in Aurora need a City business license. Annual renewal is required, and fees vary by business type. You should also verify zoning compliance before starting operations."
    },
    {
        "question": "What is the Enterprise Zone and how does it benefit my business?",
        "answer": "Aurora's Enterprise Zone is a designated area offering state income tax credits including: 3% Investment Tax Credit on equipment, up to $1,200 Job Training Credit per employee, $1,100 New Employee Credit per full-time hire, 3% R&D Credit, and 25% Vacant Building Rehabilitation Credit. These credits can significantly reduce your state tax burden."
    },
    {
        "question": "Are there available warehouse or distribution facilities in Aurora?",
        "answer": "Yes, Aurora has significant industrial inventory, particularly along the I-70 Corridor and E-470 areas. Typical industrial vacancy rates are 5-7%, with lease rates averaging $8-12/sf NNN. Many facilities offer features like rail access, high power availability, and proximity to Denver International Airport."
    },
    {
        "question": "How does Aurora compare to Denver for business costs?",
        "answer": "Aurora generally offers more competitive costs compared to Denver, including lower lease rates for commercial and industrial space, while maintaining excellent highway and airport access. The city's Enterprise Zone credits and other incentives can further reduce costs. Aurora also offers more available land for development compared to Denver's more constrained market."
    },
    {
        "question": "What permits do I need to open a restaurant in Aurora?",
        "answer": "To open a restaurant in Aurora, you'll need: a City of Aurora business license, a food service license from Tri-County Health Department, food handler certifications for employees, building permits for any construction or tenant improvements, and if serving alcohol, both City and State liquor licenses. Zoning compliance verification is also required."
    },
    {
        "question": "Does Aurora have rail access for freight?",
        "answer": "Yes, Aurora has freight rail service from both Union Pacific Railroad and BNSF Railway. Several industrial areas have direct rail access or spur opportunities. This rail infrastructure, combined with highway access and airport proximity, makes Aurora an excellent location for logistics and distribution operations."
    },
]


def main():
    """Seed the knowledge base with Aurora EDC content."""
    print("Initializing RAG service...")
    rag = get_rag_service()

    print("Clearing existing collection...")
    try:
        rag.clear_collection()
    except Exception:
        pass  # Collection may not exist yet

    # Ingest overview content
    print("Ingesting Aurora overview...")
    docs = ingest_document(
        content=AURORA_OVERVIEW,
        title="Aurora Colorado Business Overview",
        source="Aurora EDC",
        category="overview",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest incentives
    print("Ingesting incentives information...")
    docs = ingest_document(
        content=INCENTIVES_CONTENT,
        title="Aurora Business Incentives",
        source="Aurora EDC",
        category="incentives",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest workforce info
    print("Ingesting workforce information...")
    docs = ingest_document(
        content=WORKFORCE_CONTENT,
        title="Aurora Workforce Demographics",
        source="Aurora EDC",
        category="workforce",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest major employers
    print("Ingesting major employers...")
    docs = ingest_document(
        content=MAJOR_EMPLOYERS,
        title="Major Employers in Aurora",
        source="Aurora EDC",
        category="employers",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest permit guide
    print("Ingesting permit guide...")
    docs = ingest_document(
        content=PERMIT_GUIDE,
        title="Aurora Permits and Licensing Guide",
        source="Aurora EDC",
        category="permits",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest properties info
    print("Ingesting properties information...")
    docs = ingest_document(
        content=PROPERTIES_INFO,
        title="Aurora Commercial Properties",
        source="Aurora EDC",
        category="properties",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest transportation
    print("Ingesting transportation information...")
    docs = ingest_document(
        content=TRANSPORTATION,
        title="Aurora Transportation Infrastructure",
        source="Aurora EDC",
        category="infrastructure",
        doc_type="markdown",
    )
    for doc in docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Ingest FAQs
    print("Ingesting FAQs...")
    faq_docs = ingest_faq(FAQS, category="faq")
    for doc in faq_docs:
        rag.add_document(doc["id"], doc["content"], {
            "title": doc["title"],
            "source": doc["source"],
            "category": doc["category"],
        })

    # Verify
    stats = rag.get_collection_stats()
    print(f"\nKnowledge base seeded successfully!")
    print(f"Total documents: {stats['count']}")


if __name__ == "__main__":
    main()
