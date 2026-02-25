#!/usr/bin/env python3
"""
Environment Variables Validation Script
Checks if all required environment variables are set correctly.
"""

import os
import sys
from typing import List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def check_variable(name: str, required: bool = True, check_value: bool = False) -> Tuple[bool, str]:
    """
    Check if an environment variable is set.
    
    Args:
        name: Variable name
        required: Whether the variable is required
        check_value: Whether to check if value is not a placeholder
    
    Returns:
        Tuple of (is_valid, message)
    """
    value = os.getenv(name)
    
    if value is None:
        if required:
            return False, f"{RED}✗{RESET} {name}: Not set (REQUIRED)"
        else:
            return True, f"{YELLOW}○{RESET} {name}: Not set (optional)"
    
    if check_value:
        placeholders = ['xxxxx', 'your-', 'change-', 'path/to/', '[YOUR-', '[PASSWORD]', '[ENDPOINT]']
        if any(placeholder in value for placeholder in placeholders):
            return False, f"{YELLOW}⚠{RESET} {name}: Contains placeholder value"
    
    return True, f"{GREEN}✓{RESET} {name}: Set"


def main():
    """Main validation function."""
    print("=" * 60)
    print("Hedera Flow MVP - Environment Variables Validation")
    print("=" * 60)
    print()
    
    errors: List[str] = []
    warnings: List[str] = []
    
    # Database Configuration
    print("📊 Database Configuration:")
    checks = [
        ('DATABASE_URL', True, True),
        ('POSTGRES_HOST', True, False),
        ('POSTGRES_PORT', True, False),
        ('POSTGRES_USER', True, False),
        ('POSTGRES_PASSWORD', True, True),
        ('POSTGRES_DB', True, False),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:  # If required and not valid
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Redis Configuration
    print("🔴 Redis Configuration:")
    checks = [
        ('REDIS_URL', True, True),
        ('REDIS_HOST', True, False),
        ('REDIS_PORT', True, False),
        ('REDIS_PASSWORD', True, True),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # JWT Configuration
    print("🔐 JWT Configuration:")
    checks = [
        ('JWT_SECRET_KEY', True, True),
        ('JWT_ALGORITHM', True, False),
        ('JWT_EXPIRATION_DAYS', True, False),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Hedera Configuration
    print("🌐 Hedera Configuration:")
    checks = [
        ('HEDERA_NETWORK', True, False),
        ('HEDERA_OPERATOR_ID', True, True),
        ('HEDERA_OPERATOR_KEY', True, True),
        ('HEDERA_TREASURY_ID', True, True),
        ('HEDERA_TREASURY_KEY', True, True),
        ('HCS_TOPIC_EU', True, True),
        ('HCS_TOPIC_US', True, True),
        ('HCS_TOPIC_ASIA', True, True),
        ('HCS_TOPIC_SA', True, True),
        ('HCS_TOPIC_AFRICA', True, True),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Google Cloud Vision API
    print("👁️  Google Cloud Vision API:")
    checks = [
        ('GOOGLE_APPLICATION_CREDENTIALS', True, True),
        ('GOOGLE_CLOUD_PROJECT_ID', False, True),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # IPFS Configuration
    print("📦 IPFS Configuration (Pinata):")
    checks = [
        ('PINATA_API_KEY', True, True),
        ('PINATA_SECRET_KEY', True, True),
        ('PINATA_JWT', False, True),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Exchange Rate APIs
    print("💱 Exchange Rate APIs:")
    checks = [
        ('COINGECKO_API_KEY', True, True),
        ('COINMARKETCAP_API_KEY', False, True),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Email Configuration
    print("📧 Email Configuration:")
    checks = [
        ('SENDGRID_API_KEY', False, True),
        ('FROM_EMAIL', False, True),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Application Settings
    print("⚙️  Application Settings:")
    checks = [
        ('ENVIRONMENT', True, False),
        ('DEBUG', True, False),
        ('RATE_LIMIT_PER_MINUTE', True, False),
    ]
    
    for check in checks:
        is_valid, message = check_variable(*check)
        print(f"  {message}")
        if not is_valid and check[1]:
            errors.append(message)
        elif not is_valid:
            warnings.append(message)
    print()
    
    # Summary
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if errors:
        print(f"{RED}✗ {len(errors)} ERRORS found:{RESET}")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
        print()
    
    if warnings:
        print(f"{YELLOW}⚠ {len(warnings)} WARNINGS found:{RESET}")
        for warning in warnings[:5]:  # Show first 5 warnings
            print(f"  {warning}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more")
        print()
    
    if not errors and not warnings:
        print(f"{GREEN}✓ All environment variables are properly configured!{RESET}")
        print()
        return 0
    elif not errors:
        print(f"{YELLOW}⚠ Configuration has warnings but should work.{RESET}")
        print()
        return 0
    else:
        print(f"{RED}✗ Configuration has errors. Please fix them before running the application.{RESET}")
        print()
        print("💡 Tips:")
        print("  1. Copy .env.example to .env: cp .env.example .env")
        print("  2. Edit .env and replace placeholder values")
        print("  3. See ENV_SETUP.md for detailed setup instructions")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
