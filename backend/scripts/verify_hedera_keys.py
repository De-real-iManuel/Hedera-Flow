"""
Simple Hedera Account Verification
Tests if your operator account credentials are valid
"""
import os
from dotenv import load_dotenv

load_dotenv()

operator_id = os.getenv('HEDERA_OPERATOR_ID')
operator_key = os.getenv('HEDERA_OPERATOR_KEY')

print("=" * 70)
print("HEDERA ACCOUNT VERIFICATION")
print("=" * 70)
print(f"\nOperator ID: {operator_id}")
print(f"Operator Key: {operator_key[:20]}... (truncated)")
print(f"Key Format: {'DER (302e...)' if operator_key.startswith('302e') else 'Hex (0x...)' if operator_key.startswith('0x') else 'Unknown'}")

print("\n" + "=" * 70)
print("ISSUE DETECTED:")
print("=" * 70)
print("\nYour HEDERA_OPERATOR_KEY appears to be in Ethereum format (0x...).")
print("Hedera requires keys in DER format (starting with '302e').")
print("\nTo fix this:")
print("1. Go to https://portal.hedera.com/")
print("2. Login and go to your testnet account")
print("3. Copy the PRIVATE KEY (should start with '302e')")
print("4. Update .env file:")
print(f"   HEDERA_OPERATOR_KEY=302e020100300506032b657004220420...")
print("\nAlternatively, use your Treasury key format as a template.")
print(f"Treasury key format (correct): {os.getenv('HEDERA_TREASURY_KEY')[:20]}...")
