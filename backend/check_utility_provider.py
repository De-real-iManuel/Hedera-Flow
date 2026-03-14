#!/usr/bin/env python3
"""Check utility provider in database"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.utility_provider import UtilityProvider
from uuid import UUID

# Utility provider ID from request
provider_id = UUID("ea3cc7e9-dc21-4c86-bb92-fb36f69ce7fd")

db = SessionLocal()
try:
    # Find the utility provider
    provider = db.query(UtilityProvider).filter(UtilityProvider.id == provider_id).first()
    
    if provider:
        print(f"Found utility provider:")
        print(f"  ID: {provider.id}")
        print(f"  Name: {provider.provider_name}")
        print(f"  Country: {provider.country_code}")
        print(f"  State: {provider.state_province}")
        print(f"  Active: {provider.is_active}")
    else:
        print(f"Utility provider {provider_id} NOT FOUND")
        
    # List all providers
    all_providers = db.query(UtilityProvider).all()
    print(f"\nTotal utility providers in database: {len(all_providers)}")
    for p in all_providers[:5]:
        print(f"  - {p.provider_name} ({p.state_province}, {p.country_code})")
        
finally:
    db.close()
