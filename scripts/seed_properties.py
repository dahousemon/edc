#!/usr/bin/env python3
"""
Seed the database with sample commercial properties.
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import text
from app.models.database import async_session, Property


SAMPLE_PROPERTIES = [
    {
        "name": "Aurora Tech Center",
        "address": "14200 E Alameda Ave",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80012",
        "property_type": "office",
        "total_sqft": 85000,
        "available_sqft": 25000,
        "price_per_sqft": None,
        "lease_rate": 24.50,
        "zoning": "C-3",
        "year_built": 2008,
        "features": ["fiber_connectivity", "conference_center", "parking_garage", "fitness_center"],
        "description": "Class A office building in Aurora's premier business district. Features modern amenities, excellent visibility from I-225, and abundant parking.",
        "latitude": 39.6997,
        "longitude": -104.8386,
    },
    {
        "name": "I-70 Distribution Hub",
        "address": "21000 E 40th Ave",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80019",
        "property_type": "warehouse",
        "total_sqft": 250000,
        "available_sqft": 250000,
        "price_per_sqft": None,
        "lease_rate": 9.75,
        "zoning": "I-2",
        "year_built": 2020,
        "features": ["rail_access", "highway_access", "loading_docks", "high_ceiling", "yard_space"],
        "description": "State-of-the-art distribution facility with 36' clear height, 50 dock doors, and immediate I-70 access. Rail spur available.",
        "latitude": 39.7673,
        "longitude": -104.7231,
    },
    {
        "name": "Fitzsimons Life Sciences Building",
        "address": "12635 E Montview Blvd",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80045",
        "property_type": "office",
        "total_sqft": 120000,
        "available_sqft": 35000,
        "price_per_sqft": None,
        "lease_rate": 32.00,
        "zoning": "MU-C",
        "year_built": 2015,
        "features": ["lab_space", "high_power", "loading_dock", "conference_center", "bioscience_ready"],
        "description": "Purpose-built life sciences facility on Fitzsimons campus. Lab-ready suites with specialized HVAC and power. Adjacent to UC Anschutz Medical Campus.",
        "latitude": 39.7458,
        "longitude": -104.8369,
    },
    {
        "name": "Aurora Gateway Industrial Park",
        "address": "4500 N Himalaya St",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80019",
        "property_type": "industrial",
        "total_sqft": 180000,
        "available_sqft": 65000,
        "price_per_sqft": None,
        "lease_rate": 8.50,
        "zoning": "I-1",
        "year_built": 2018,
        "features": ["highway_access", "loading_docks", "office_space", "fenced_yard", "24hr_security"],
        "description": "Modern flex industrial space with 28' clear height. Divisible from 15,000 SF. Convenient to E-470 and I-70.",
        "latitude": 39.7889,
        "longitude": -104.7456,
    },
    {
        "name": "Aurora Town Center Retail",
        "address": "14100 E Mississippi Ave",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80012",
        "property_type": "retail",
        "total_sqft": 45000,
        "available_sqft": 12000,
        "price_per_sqft": None,
        "lease_rate": 22.00,
        "zoning": "C-3",
        "year_built": 1995,
        "features": ["high_visibility", "parking", "anchor_tenants", "signage"],
        "description": "Inline retail space in established shopping center. High traffic location with excellent co-tenancy including major grocery anchor.",
        "latitude": 39.6889,
        "longitude": -104.8375,
    },
    {
        "name": "Aerospace Manufacturing Facility",
        "address": "2800 S Peoria St",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80014",
        "property_type": "industrial",
        "total_sqft": 150000,
        "available_sqft": 150000,
        "price_per_sqft": 165.00,
        "lease_rate": None,
        "zoning": "I-2",
        "year_built": 2005,
        "features": ["heavy_power", "crane_ready", "clean_room_capable", "loading_docks", "office_space"],
        "description": "Aerospace-grade manufacturing facility with 2,000 amp power, overhead crane infrastructure, and clean room potential. Ideal for defense contractors.",
        "latitude": 39.6512,
        "longitude": -104.8214,
    },
    {
        "name": "E-470 Business Campus",
        "address": "24500 E Quincy Ave",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80016",
        "property_type": "office",
        "total_sqft": 95000,
        "available_sqft": 40000,
        "price_per_sqft": None,
        "lease_rate": 21.00,
        "zoning": "C-2",
        "year_built": 2019,
        "features": ["fiber_connectivity", "ev_charging", "parking", "cafe", "outdoor_space"],
        "description": "New construction Class A office in growing E-470 corridor. LEED certified with modern amenities. Excellent DEN airport access.",
        "latitude": 39.6389,
        "longitude": -104.7123,
    },
    {
        "name": "Original Aurora Flex Space",
        "address": "9800 E Colfax Ave",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80010",
        "property_type": "mixed-use",
        "total_sqft": 35000,
        "available_sqft": 8000,
        "price_per_sqft": None,
        "lease_rate": 16.00,
        "zoning": "MU-C",
        "year_built": 1985,
        "features": ["storefront", "rear_loading", "high_ceilings", "office_space"],
        "description": "Versatile flex space in vibrant Original Aurora district. Suitable for light manufacturing, showroom, or creative office use. Recently renovated.",
        "latitude": 39.7397,
        "longitude": -104.8589,
    },
    {
        "name": "DEN Airport Logistics Center",
        "address": "26000 E 56th Ave",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80019",
        "property_type": "warehouse",
        "total_sqft": 400000,
        "available_sqft": 125000,
        "price_per_sqft": None,
        "lease_rate": 11.25,
        "zoning": "I-2",
        "year_built": 2022,
        "features": ["highway_access", "rail_access", "high_ceiling", "loading_docks", "trailer_parking", "airport_proximity"],
        "description": "Brand new distribution facility just 5 minutes from DEN. 40' clear height, 80 dock doors, ESFR sprinklers. Ideal for e-commerce and air cargo.",
        "latitude": 39.8156,
        "longitude": -104.6978,
    },
    {
        "name": "Southlands Medical Office",
        "address": "6180 S Main St",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80016",
        "property_type": "office",
        "total_sqft": 55000,
        "available_sqft": 15000,
        "price_per_sqft": None,
        "lease_rate": 28.00,
        "zoning": "C-2",
        "year_built": 2017,
        "features": ["medical_ready", "fiber_connectivity", "parking", "signage", "high_visibility"],
        "description": "Purpose-built medical office building in Southlands retail district. Plumbed for medical use with excellent patient accessibility.",
        "latitude": 39.5912,
        "longitude": -104.7234,
    },
    {
        "name": "Aurora Light Manufacturing",
        "address": "15200 E 33rd Place",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80011",
        "property_type": "industrial",
        "total_sqft": 75000,
        "available_sqft": 75000,
        "price_per_sqft": 125.00,
        "lease_rate": None,
        "zoning": "I-1",
        "year_built": 2000,
        "features": ["heavy_power", "loading_docks", "office_space", "fenced_yard", "overhead_doors"],
        "description": "Well-maintained manufacturing facility with 24' clear height and 800 amp 480V power. 20% office build-out. Enterprise Zone location.",
        "latitude": 39.7612,
        "longitude": -104.8023,
    },
    {
        "name": "Stanley Marketplace - Restaurant Space",
        "address": "2501 Dallas St",
        "city": "Aurora",
        "state": "CO",
        "zip_code": "80010",
        "property_type": "retail",
        "total_sqft": 4500,
        "available_sqft": 2200,
        "price_per_sqft": None,
        "lease_rate": 35.00,
        "zoning": "MU-C",
        "year_built": 1954,
        "features": ["historic_building", "high_foot_traffic", "food_service_ready", "outdoor_patio"],
        "description": "Unique opportunity in award-winning adaptive reuse food hall. Turnkey restaurant space with existing hood and grease trap. High visibility location.",
        "latitude": 39.7389,
        "longitude": -104.8667,
    },
]


async def seed_properties():
    """Insert sample properties into database."""
    print("Connecting to database...")

    async with async_session() as session:
        # Check if properties already exist
        result = await session.execute(text("SELECT COUNT(*) FROM properties"))
        count = result.scalar()

        if count > 0:
            print(f"Database already has {count} properties. Skipping seed.")
            return

        print(f"Inserting {len(SAMPLE_PROPERTIES)} sample properties...")

        for prop_data in SAMPLE_PROPERTIES:
            prop = Property(**prop_data)
            session.add(prop)

        await session.commit()
        print("Properties seeded successfully!")


def main():
    asyncio.run(seed_properties())


if __name__ == "__main__":
    main()
