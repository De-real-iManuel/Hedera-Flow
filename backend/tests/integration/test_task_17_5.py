"""
Test Task 17.5: Generate transaction details (from, to, amount, memo)

This test verifies that the payment preparation endpoint generates complete
transaction details including:
- from: User's Hedera account ID
- to: Utility provider's Hedera account ID
- amount: HBAR amount
- memo: Formatted payment memo

Requirements: FR-6.6, US-7
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from app.main import app
from app.core.database import Base, get_db
f