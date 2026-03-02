#!/usr/bin/env python3
"""
Test Hedera Connection

Quick script to verify Hedera testnet connection and account balances.
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hedera import Client, AccountBalanceQuery, AccountId, PrivateKey
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test Hedera connection"""
    try:
        logger.info("=" * 60)
        logger.info("HEDERA CONNECTION TEST")
        logger.info("=" * 60)
        
        # Initialize client
        logger.info(f"Network: {settings.hedera_network}")
        
        if settings.hedera_network == "testnet":
            client = Client.forTestnet()
        else:
            client = Client.forMainnet()
        
        # Set operator
        operator_id = AccountId.fromString(settings.hedera_operator_id)
        operator_key = PrivateKey.fromString(settings.hedera_operator_key)
        client.setOperator(operator_id, operator_key)
        
        logger.info(f"✅ Client initialized")
        logger.info("")
        
        # Check operator balance
        logger.info(f"Checking operator account: {settings.hedera_operator_id}")
        query = AccountBalanceQuery().setAccountId(operator_id)
        balance = query.execute(client)
        
        logger.info(f"✅ Operator Balance: {balance.hbars} HBAR")
        logger.info("")
        
        # Check treasury balance
        logger.info(f"Checking treasury account: {settings.hedera_treasury_id}")
        treasury_id = AccountId.fromString(settings.hedera_treasury_id)
        query = AccountBalanceQuery().setAccountId(treasury_id)
        balance = query.execute(client)
        
        logger.info(f"✅ Treasury Balance: {balance.hbars} HBAR")
        logger.info("")
        
        # Summary
        logger.info("=" * 60)
        logger.info("✅ HEDERA CONNECTION SUCCESSFUL")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run: python scripts/create_hcs_topics.py")
        logger.info("2. Update .env with HCS topic IDs")
        logger.info("3. Test verification flow")
        logger.info("")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("1. Check HEDERA_OPERATOR_ID in .env")
        logger.error("2. Check HEDERA_OPERATOR_KEY in .env")
        logger.error("3. Ensure accounts have HBAR balance")
        logger.error("4. Visit: https://portal.hedera.com/faucet")
        sys.exit(1)


if __name__ == "__main__":
    main()
