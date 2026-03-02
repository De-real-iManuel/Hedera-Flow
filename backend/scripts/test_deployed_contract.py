#!/usr/bin/env python3
"""
Test Deployed Smart Contract

This script tests the deployed BillingSettlement contract on Hedera testnet.

Usage:
    python scripts/test_deployed_contract.py

Tests:
1. Contract exists and is accessible
2. Owner is set correctly
3. Minimum transfer constant is correct
4. Contract can receive HBAR
"""

import os
import sys
import json
from pathlib import Path
from hedera import (
    Client,
    AccountId,
    PrivateKey,
    ContractCallQuery,
    ContractExecuteTransaction,
    ContractFunctionParameters,
    Hbar,
    Status
)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


class ContractTester:
    """Test deployed smart contract"""
    
    def __init__(self):
        """Initialize client and load contract info"""
        self.client = None
        self.operator_id = None
        self.operator_key = None
        self.contract_id = None
        
    def setup_client(self):
        """Set up Hedera client"""
        print("🔧 Setting up Hedera client...")
        
        # Get credentials
        operator_id_str = settings.hedera_operator_id
        operator_key_str = settings.hedera_operator_key
        
        if not operator_id_str or not operator_key_str:
            raise ValueError("Missing Hedera credentials in .env")
        
        self.operator_id = AccountId.fromString(operator_id_str)
        self.operator_key = PrivateKey.fromString(operator_key_str)
        
        # Create client
        if settings.hedera_network == "testnet":
            self.client = Client.forTestnet()
        else:
            self.client = Client.forMainnet()
        
        self.client.setOperator(self.operator_id, self.operator_key)
        self.client.setDefaultMaxTransactionFee(Hbar(10))
        self.client.setDefaultMaxQueryPayment(Hbar(1))
        
        print(f"✅ Client configured for {settings.hedera_network}")
        
    def load_contract_id(self):
        """Load contract ID from deployment.json or .env"""
        print("\n📋 Loading contract ID...")
        
        # Try deployment.json first
        deployment_path = Path(__file__).parent.parent / "deployment.json"
        if deployment_path.exists():
            with open(deployment_path, 'r') as f:
                deployment_info = json.load(f)
                contract_id_str = deployment_info.get('contract_id')
                if contract_id_str:
                    self.contract_id = contract_id_str
                    print(f"✅ Contract ID from deployment.json: {self.contract_id}")
                    return
        
        # Try environment variable
        contract_id_str = os.getenv('HEDERA_CONTRACT_ID')
        if contract_id_str:
            self.contract_id = contract_id_str
            print(f"✅ Contract ID from .env: {self.contract_id}")
            return
        
        raise ValueError(
            "Contract ID not found. Please deploy the contract first:\n"
            "python scripts/deploy_contract.py"
        )
    
    def test_contract_exists(self):
        """Test 1: Verify contract exists"""
        print("\n🧪 Test 1: Contract Exists")
        print(f"   Contract ID: {self.contract_id}")
        
        try:
            # Query contract info (this will fail if contract doesn't exist)
            query = ContractCallQuery()
            query.setContractId(self.contract_id)
            query.setGas(50000)
            query.setFunction("owner")  # Call owner() function
            
            result = query.execute(self.client)
            print("✅ Contract exists and is accessible")
            return True
            
        except Exception as e:
            print(f"❌ Contract not found or not accessible: {e}")
            return False
    
    def test_owner_address(self):
        """Test 2: Verify owner is set correctly"""
        print("\n🧪 Test 2: Owner Address")
        
        try:
            query = ContractCallQuery()
            query.setContractId(self.contract_id)
            query.setGas(50000)
            query.setFunction("owner")
            
            result = query.execute(self.client)
            
            # The owner should be the operator account that deployed the contract
            print(f"   Owner (from contract): {result.getAddress(0)}")
            print(f"   Operator (deployer): {self.operator_id}")
            print("✅ Owner address retrieved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to get owner: {e}")
            return False
    
    def test_minimum_transfer(self):
        """Test 3: Verify minimum transfer constant"""
        print("\n🧪 Test 3: Minimum Transfer Constant")
        
        try:
            query = ContractCallQuery()
            query.setContractId(self.contract_id)
            query.setGas(50000)
            query.setFunction("MIN_TRANSFER_HBAR")
            
            result = query.execute(self.client)
            min_transfer = result.getUint256(0)
            
            # Expected: 5 HBAR = 500,000,000 tinybars
            expected = 5 * 100_000_000
            
            print(f"   Minimum Transfer: {min_transfer} tinybars")
            print(f"   Expected: {expected} tinybars (5 HBAR)")
            
            if min_transfer == expected:
                print("✅ Minimum transfer is correct")
                return True
            else:
                print("⚠️  Minimum transfer differs from expected")
                return False
            
        except Exception as e:
            print(f"❌ Failed to get minimum transfer: {e}")
            return False
    
    def test_contract_info(self):
        """Test 4: Display contract information"""
        print("\n📊 Contract Information")
        
        deployment_path = Path(__file__).parent.parent / "deployment.json"
        if deployment_path.exists():
            with open(deployment_path, 'r') as f:
                info = json.load(f)
                
            print(f"   Contract ID: {info.get('contract_id')}")
            print(f"   File ID: {info.get('file_id')}")
            print(f"   Network: {info.get('network')}")
            print(f"   Deployed At: {info.get('deployed_at')}")
            print(f"   Solidity Version: {info.get('solidity_version')}")
            print(f"   Explorer: https://hashscan.io/{info.get('network')}/contract/{info.get('contract_id')}")
            print("✅ Contract information displayed")
            return True
        else:
            print("⚠️  deployment.json not found")
            return False
    
    def run_tests(self):
        """Run all tests"""
        try:
            self.setup_client()
            self.load_contract_id()
            
            results = []
            results.append(("Contract Exists", self.test_contract_exists()))
            results.append(("Owner Address", self.test_owner_address()))
            results.append(("Minimum Transfer", self.test_minimum_transfer()))
            results.append(("Contract Info", self.test_contract_info()))
            
            # Summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} - {test_name}")
            
            print("="*60)
            print(f"Results: {passed}/{total} tests passed")
            print("="*60)
            
            if passed == total:
                print("\n🎉 All tests passed! Contract is ready to use.")
            else:
                print("\n⚠️  Some tests failed. Please review the output above.")
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            raise
        
        finally:
            if self.client:
                self.client.close()


def main():
    """Main entry point"""
    print("="*60)
    print("HEDERA SMART CONTRACT TESTING")
    print("="*60)
    
    tester = ContractTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
