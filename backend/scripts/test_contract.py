#!/usr/bin/env python3
"""
Hedera Smart Contract Testing Script

This script tests all functions of the deployed BillingSettlement contract on Hedera testnet.

Tests:
1. payBill() - Pay a bill with HBAR
2. getBill() - Retrieve bill details
3. createDispute() - Create a dispute with escrow
4. getDispute() - Retrieve dispute details
5. resolveDispute() - Resolve dispute (admin only)

Requirements:
- Deployed contract (deployment.json must exist)
- Hedera operator account with sufficient HBAR (>50 HBAR recommended)
- Test utility account (will be created if needed)

Usage:
    python scripts/test_contract.py
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from hedera import (
    Client,
    AccountId,
    PrivateKey,
    ContractCallQuery,
    ContractExecuteTransaction,
    ContractFunctionParameters,
    ContractId,
    Hbar,
    AccountCreateTransaction,
    TransferTransaction,
    AccountBalanceQuery
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


class ContractTester:
    """Tests BillingSettlement contract functions on Hedera testnet"""
    
    def __init__(self):
        """Initialize test environment"""
        self.client = None
        self.operator_id = None
        self.operator_key = None
        self.contract_id = None
        self.utility_account_id = None
        self.utility_private_key = None
        self.test_results = []
        
    def setup_client(self):
        """Set up Hedera client"""
        print("[*] Setting up Hedera client...")
        
        # Get operator credentials
        operator_id_str = settings.hedera_operator_id
        operator_key_str = settings.hedera_operator_key
        
        if not operator_id_str or not operator_key_str:
            raise ValueError("Missing Hedera credentials in .env file")
        
        self.operator_id = AccountId.fromString(operator_id_str)
        self.operator_key = PrivateKey.fromString(operator_key_str)
        
        # Create client
        if settings.hedera_network == "testnet":
            self.client = Client.forTestnet()
        else:
            self.client = Client.forMainnet()
        
        self.client.setOperator(self.operator_id, self.operator_key)
        self.client.setDefaultMaxTransactionFee(Hbar(100))
        self.client.setDefaultMaxQueryPayment(Hbar(1))
        
        print(f"[+] Client configured for {settings.hedera_network}")
        print(f"    Operator: {self.operator_id}")
        
    def load_contract_id(self):
        """Load deployed contract ID"""
        print("\n[*] Loading contract ID...")
        
        deployment_path = Path(__file__).parent.parent / "deployment.json"
        
        if not deployment_path.exists():
            raise FileNotFoundError(
                "deployment.json not found. Please deploy the contract first."
            )
        
        with open(deployment_path, 'r') as f:
            deployment = json.load(f)
        
        contract_id_str = deployment.get('contract_id')
        if not contract_id_str:
            raise ValueError("No contract_id in deployment.json")
        
        self.contract_id = ContractId.fromString(contract_id_str)
        print(f"[+] Contract ID: {contract_id_str}")
        print(f"    Explorer: https://hashscan.io/testnet/contract/{contract_id_str}")
        
    def create_utility_account(self):
        """Create a test utility account to receive payments"""
        print("\n[*] Creating test utility account...")
        
        # Generate new key pair
        self.utility_private_key = PrivateKey.generateED25519()
        utility_public_key = self.utility_private_key.getPublicKey()
        
        # Create account
        account_create_tx = AccountCreateTransaction()
        account_create_tx.setKey(utility_public_key)
        account_create_tx.setInitialBalance(Hbar(10))  # Fund with 10 HBAR
        
        account_create_submit = account_create_tx.execute(self.client)
        account_create_receipt = account_create_submit.getReceipt(self.client)
        
        self.utility_account_id = account_create_receipt.accountId
        
        print(f"[+] Utility account created: {self.utility_account_id}")
        print(f"    Public key: {utility_public_key}")
        
    def check_balance(self, account_id, label="Account"):
        """Check and display account balance"""
        balance_query = AccountBalanceQuery()
        balance_query.setAccountId(account_id)
        
        balance = balance_query.execute(self.client)
        hbar_balance = balance.hbars.toTinybars() / 100_000_000
        
        print(f"    {label} balance: {hbar_balance:.2f} HBAR")
        return hbar_balance
        
    def test_pay_bill(self):
        """Test 1: Pay a bill using payBill()"""
        print("\n" + "="*60)
        print("TEST 1: payBill() - Pay a bill with HBAR")
        print("="*60)
        
        try:
            # Generate unique bill ID
            bill_id = f"BILL-TEST-{int(time.time())}".encode('utf-8')
            bill_id_bytes32 = bill_id.ljust(32, b'\x00')[:32]
            
            # Test parameters
            amount_hbar = 10  # 10 HBAR
            amount_fiat = int(8540)  # €85.40 in cents (as Python int)
            currency = "EUR"
            
            print(f"\n[*] Test parameters:")
            print(f"    Bill ID: {bill_id.decode('utf-8')}")
            print(f"    Utility: {self.utility_account_id}")
            print(f"    Amount: {amount_hbar} HBAR")
            print(f"    Fiat equivalent: €{amount_fiat/100:.2f}")
            
            # Check balances before
            print(f"\n[*] Balances before payment:")
            operator_balance_before = self.check_balance(self.operator_id, "Operator")
            utility_balance_before = self.check_balance(self.utility_account_id, "Utility")
            
            # Call payBill function
            print(f"\n[*] Calling payBill()...")
            
            contract_exec_tx = ContractExecuteTransaction()
            contract_exec_tx.setContractId(self.contract_id)
            contract_exec_tx.setGas(500000)
            contract_exec_tx.setPayableAmount(Hbar(amount_hbar))
            
            # Function parameters: payBill(bytes32 billId, address utility, uint256 amountFiat, string currency)
            function_params = ContractFunctionParameters()
            function_params.addBytes32(bill_id_bytes32)
            function_params.addAddress(self.utility_account_id.toSolidityAddress())
            function_params.addUint256(amount_fiat)  # Already an int
            function_params.addString(currency)
            
            contract_exec_tx.setFunction("payBill", function_params)
            
            # Execute transaction
            contract_exec_submit = contract_exec_tx.execute(self.client)
            
            print(f"    Transaction submitted, waiting for consensus...")
            contract_exec_receipt = contract_exec_submit.getReceipt(self.client)
            
            # Get transaction record for events
            tx_record = contract_exec_submit.getRecord(self.client)
            
            print(f"[+] Transaction successful!")
            print(f"    Transaction ID: {contract_exec_submit.transactionId}")
            print(f"    Consensus timestamp: {tx_record.consensusTimestamp}")
            
            # Check balances after
            print(f"\n[*] Balances after payment:")
            operator_balance_after = self.check_balance(self.operator_id, "Operator")
            utility_balance_after = self.check_balance(self.utility_account_id, "Utility")
            
            # Verify balance changes
            operator_spent = operator_balance_before - operator_balance_after
            utility_received = utility_balance_after - utility_balance_before
            
            print(f"\n[*] Balance changes:")
            print(f"    Operator spent: {operator_spent:.2f} HBAR (includes {amount_hbar} HBAR + fees)")
            print(f"    Utility received: {utility_received:.2f} HBAR")
            
            # Verify utility received the payment
            if abs(utility_received - amount_hbar) < 0.01:  # Allow small rounding
                print(f"[+] ✓ Utility received correct amount")
                test_passed = True
            else:
                print(f"[!] ✗ Utility received incorrect amount (expected {amount_hbar} HBAR)")
                test_passed = False
            
            self.test_results.append({
                "test": "payBill()",
                "passed": test_passed,
                "bill_id": bill_id.decode('utf-8'),
                "tx_id": str(contract_exec_submit.transactionId)
            })
            
            # Store bill ID for next test
            self.test_bill_id = bill_id_bytes32
            
            return test_passed
            
        except Exception as e:
            print(f"[!] Test failed: {e}")
            self.test_results.append({
                "test": "payBill()",
                "passed": False,
                "error": str(e)
            })
            return False
    
    def test_get_bill(self):
        """Test 2: Retrieve bill details using getBill()"""
        print("\n" + "="*60)
        print("TEST 2: getBill() - Retrieve bill details")
        print("="*60)
        
        try:
            if not hasattr(self, 'test_bill_id'):
                print("[!] Skipping: No bill ID from previous test")
                return False
            
            print(f"\n[*] Querying bill details...")
            
            # Call getBill function
            contract_query = ContractCallQuery()
            contract_query.setContractId(self.contract_id)
            contract_query.setGas(100000)
            
            function_params = ContractFunctionParameters()
            function_params.addBytes32(self.test_bill_id)
            
            contract_query.setFunction("getBill", function_params)
            
            # Execute query
            contract_call_result = contract_query.execute(self.client)
            
            # Parse result (Bill struct)
            # struct Bill { address user, address utility, uint256 amountHbar, uint256 amountFiat, string currency, bool paid, uint256 timestamp }
            user_address = contract_call_result.getAddress(0)
            utility_address = contract_call_result.getAddress(1)
            amount_hbar = contract_call_result.getUint256(2)
            amount_fiat = contract_call_result.getUint256(3)
            currency = contract_call_result.getString(4)
            paid = contract_call_result.getBool(5)
            timestamp = contract_call_result.getUint256(6)
            
            print(f"\n[+] Bill details retrieved:")
            print(f"    User: {user_address}")
            print(f"    Utility: {utility_address}")
            print(f"    Amount HBAR: {amount_hbar / 100_000_000:.2f} HBAR")
            print(f"    Amount Fiat: {amount_fiat / 100:.2f} {currency}")
            print(f"    Paid: {paid}")
            print(f"    Timestamp: {timestamp}")
            
            # Verify data
            test_passed = (
                paid == True and
                amount_hbar == 10 * 100_000_000 and  # 10 HBAR in tinybars
                currency == "EUR"
            )
            
            if test_passed:
                print(f"[+] ✓ Bill data is correct")
            else:
                print(f"[!] ✗ Bill data mismatch")
            
            self.test_results.append({
                "test": "getBill()",
                "passed": test_passed,
                "bill_paid": paid
            })
            
            return test_passed
            
        except Exception as e:
            print(f"[!] Test failed: {e}")
            self.test_results.append({
                "test": "getBill()",
                "passed": False,
                "error": str(e)
            })
            return False
    
    def test_create_dispute(self):
        """Test 3: Create a dispute using createDispute()"""
        print("\n" + "="*60)
        print("TEST 3: createDispute() - Create dispute with escrow")
        print("="*60)
        
        try:
            if not hasattr(self, 'test_bill_id'):
                print("[!] Skipping: No bill ID from previous test")
                return False
            
            # Generate unique dispute ID
            dispute_id = f"DISP-TEST-{int(time.time())}".encode('utf-8')
            dispute_id_bytes32 = dispute_id.ljust(32, b'\x00')[:32]
            
            escrow_amount = 5  # 5 HBAR escrow
            
            print(f"\n[*] Test parameters:")
            print(f"    Dispute ID: {dispute_id.decode('utf-8')}")
            print(f"    Bill ID: {self.test_bill_id.decode('utf-8').strip()}")
            print(f"    Escrow: {escrow_amount} HBAR")
            
            # Check balance before
            print(f"\n[*] Balance before dispute:")
            operator_balance_before = self.check_balance(self.operator_id, "Operator")
            
            # Call createDispute function
            print(f"\n[*] Calling createDispute()...")
            
            contract_exec_tx = ContractExecuteTransaction()
            contract_exec_tx.setContractId(self.contract_id)
            contract_exec_tx.setGas(500000)
            contract_exec_tx.setPayableAmount(Hbar(escrow_amount))
            
            # Function parameters: createDispute(bytes32 disputeId, bytes32 billId)
            function_params = ContractFunctionParameters()
            function_params.addBytes32(dispute_id_bytes32)
            function_params.addBytes32(self.test_bill_id)
            
            contract_exec_tx.setFunction("createDispute", function_params)
            
            # Execute transaction
            contract_exec_submit = contract_exec_tx.execute(self.client)
            
            print(f"    Transaction submitted, waiting for consensus...")
            contract_exec_receipt = contract_exec_submit.getReceipt(self.client)
            
            print(f"[+] Transaction successful!")
            print(f"    Transaction ID: {contract_exec_submit.transactionId}")
            
            # Check balance after
            print(f"\n[*] Balance after dispute:")
            operator_balance_after = self.check_balance(self.operator_id, "Operator")
            
            escrow_sent = operator_balance_before - operator_balance_after
            print(f"    Escrow sent: {escrow_sent:.2f} HBAR (includes {escrow_amount} HBAR + fees)")
            
            test_passed = True
            print(f"[+] ✓ Dispute created successfully")
            
            self.test_results.append({
                "test": "createDispute()",
                "passed": test_passed,
                "dispute_id": dispute_id.decode('utf-8'),
                "tx_id": str(contract_exec_submit.transactionId)
            })
            
            # Store dispute ID for next test
            self.test_dispute_id = dispute_id_bytes32
            
            return test_passed
            
        except Exception as e:
            print(f"[!] Test failed: {e}")
            self.test_results.append({
                "test": "createDispute()",
                "passed": False,
                "error": str(e)
            })
            return False
    
    def test_get_dispute(self):
        """Test 4: Retrieve dispute details using getDispute()"""
        print("\n" + "="*60)
        print("TEST 4: getDispute() - Retrieve dispute details")
        print("="*60)
        
        try:
            if not hasattr(self, 'test_dispute_id'):
                print("[!] Skipping: No dispute ID from previous test")
                return False
            
            print(f"\n[*] Querying dispute details...")
            
            # Call getDispute function
            contract_query = ContractCallQuery()
            contract_query.setContractId(self.contract_id)
            contract_query.setGas(100000)
            
            function_params = ContractFunctionParameters()
            function_params.addBytes32(self.test_dispute_id)
            
            contract_query.setFunction("getDispute", function_params)
            
            # Execute query
            contract_call_result = contract_query.execute(self.client)
            
            # Parse result (Dispute struct)
            # struct Dispute { bytes32 billId, address user, uint256 escrowAmount, bool resolved, address winner }
            bill_id = contract_call_result.getBytes32(0)
            user_address = contract_call_result.getAddress(1)
            escrow_amount = contract_call_result.getUint256(2)
            resolved = contract_call_result.getBool(3)
            winner_address = contract_call_result.getAddress(4)
            
            print(f"\n[+] Dispute details retrieved:")
            print(f"    Bill ID: {bill_id.decode('utf-8').strip()}")
            print(f"    User: {user_address}")
            print(f"    Escrow: {escrow_amount / 100_000_000:.2f} HBAR")
            print(f"    Resolved: {resolved}")
            print(f"    Winner: {winner_address if resolved else 'N/A'}")
            
            # Verify data
            test_passed = (
                resolved == False and
                escrow_amount == 5 * 100_000_000  # 5 HBAR in tinybars
            )
            
            if test_passed:
                print(f"[+] ✓ Dispute data is correct")
            else:
                print(f"[!] ✗ Dispute data mismatch")
            
            self.test_results.append({
                "test": "getDispute()",
                "passed": test_passed,
                "dispute_resolved": resolved
            })
            
            return test_passed
            
        except Exception as e:
            print(f"[!] Test failed: {e}")
            self.test_results.append({
                "test": "getDispute()",
                "passed": False,
                "error": str(e)
            })
            return False
    
    def test_resolve_dispute(self):
        """Test 5: Resolve dispute using resolveDispute() (admin only)"""
        print("\n" + "="*60)
        print("TEST 5: resolveDispute() - Resolve dispute (admin)")
        print("="*60)
        
        try:
            if not hasattr(self, 'test_dispute_id'):
                print("[!] Skipping: No dispute ID from previous test")
                return False
            
            # Resolve in favor of user (operator account)
            winner = self.operator_id
            
            print(f"\n[*] Test parameters:")
            print(f"    Dispute ID: {self.test_dispute_id.decode('utf-8').strip()}")
            print(f"    Winner: {winner} (user)")
            
            # Check winner balance before
            print(f"\n[*] Winner balance before resolution:")
            winner_balance_before = self.check_balance(winner, "Winner")
            
            # Call resolveDispute function
            print(f"\n[*] Calling resolveDispute()...")
            
            contract_exec_tx = ContractExecuteTransaction()
            contract_exec_tx.setContractId(self.contract_id)
            contract_exec_tx.setGas(500000)
            
            # Function parameters: resolveDispute(bytes32 disputeId, address winner)
            function_params = ContractFunctionParameters()
            function_params.addBytes32(self.test_dispute_id)
            function_params.addAddress(winner.toSolidityAddress())
            
            contract_exec_tx.setFunction("resolveDispute", function_params)
            
            # Execute transaction
            contract_exec_submit = contract_exec_tx.execute(self.client)
            
            print(f"    Transaction submitted, waiting for consensus...")
            contract_exec_receipt = contract_exec_submit.getReceipt(self.client)
            
            print(f"[+] Transaction successful!")
            print(f"    Transaction ID: {contract_exec_submit.transactionId}")
            
            # Check winner balance after
            print(f"\n[*] Winner balance after resolution:")
            winner_balance_after = self.check_balance(winner, "Winner")
            
            escrow_received = winner_balance_after - winner_balance_before
            print(f"    Escrow received: {escrow_received:.2f} HBAR")
            
            # Verify winner received escrow (approximately 5 HBAR minus fees)
            if escrow_received > 4.5:  # Allow for fees
                print(f"[+] ✓ Winner received escrow")
                test_passed = True
            else:
                print(f"[!] ✗ Winner did not receive expected escrow")
                test_passed = False
            
            self.test_results.append({
                "test": "resolveDispute()",
                "passed": test_passed,
                "escrow_received": escrow_received,
                "tx_id": str(contract_exec_submit.transactionId)
            })
            
            return test_passed
            
        except Exception as e:
            print(f"[!] Test failed: {e}")
            self.test_results.append({
                "test": "resolveDispute()",
                "passed": False,
                "error": str(e)
            })
            return False
    
    def test_minimum_transfer_validation(self):
        """Test 6: Verify minimum transfer amount enforcement"""
        print("\n" + "="*60)
        print("TEST 6: Minimum Transfer Validation")
        print("="*60)
        
        try:
            # Try to pay with less than minimum (5 HBAR)
            bill_id = f"BILL-MIN-{int(time.time())}".encode('utf-8')
            bill_id_bytes32 = bill_id.ljust(32, b'\x00')[:32]
            
            amount_hbar = 2  # 2 HBAR (below 5 HBAR minimum)
            
            print(f"\n[*] Attempting payment below minimum:")
            print(f"    Amount: {amount_hbar} HBAR (minimum is 5 HBAR)")
            
            contract_exec_tx = ContractExecuteTransaction()
            contract_exec_tx.setContractId(self.contract_id)
            contract_exec_tx.setGas(500000)
            contract_exec_tx.setPayableAmount(Hbar(amount_hbar))
            
            function_params = ContractFunctionParameters()
            function_params.addBytes32(bill_id_bytes32)
            function_params.addAddress(self.utility_account_id.toSolidityAddress())
            function_params.addUint256(2000)  # $20.00 in cents (Python int)
            function_params.addString("USD")
            
            contract_exec_tx.setFunction("payBill", function_params)
            
            # This should fail
            try:
                contract_exec_submit = contract_exec_tx.execute(self.client)
                contract_exec_receipt = contract_exec_submit.getReceipt(self.client)
                
                # If we get here, the transaction succeeded (should not happen)
                print(f"[!] ✗ Transaction succeeded (should have failed)")
                test_passed = False
                
            except Exception as tx_error:
                # Transaction should fail with "Below minimum transfer amount"
                error_msg = str(tx_error)
                if "minimum" in error_msg.lower() or "CONTRACT_REVERT_EXECUTED" in error_msg:
                    print(f"[+] ✓ Transaction correctly rejected")
                    print(f"    Error: {error_msg[:100]}...")
                    test_passed = True
                else:
                    print(f"[!] ✗ Transaction failed with unexpected error")
                    print(f"    Error: {error_msg}")
                    test_passed = False
            
            self.test_results.append({
                "test": "Minimum Transfer Validation",
                "passed": test_passed
            })
            
            return test_passed
            
        except Exception as e:
            print(f"[!] Test setup failed: {e}")
            self.test_results.append({
                "test": "Minimum Transfer Validation",
                "passed": False,
                "error": str(e)
            })
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        print(f"\nTotal tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetailed results:")
        for i, result in enumerate(self.test_results, 1):
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"  {i}. {result['test']}: {status}")
            if 'error' in result:
                print(f"     Error: {result['error']}")
        
        # Save results to file
        results_path = Path(__file__).parent.parent / "test_results.json"
        with open(results_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "contract_id": str(self.contract_id),
                "network": settings.hedera_network,
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n[+] Results saved to: {results_path}")
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """Execute all contract tests"""
        try:
            self.setup_client()
            self.load_contract_id()
            self.create_utility_account()
            
            # Run tests in sequence
            self.test_pay_bill()
            self.test_get_bill()
            self.test_create_dispute()
            self.test_get_dispute()
            self.test_resolve_dispute()
            self.test_minimum_transfer_validation()
            
            # Print summary
            all_passed = self.print_summary()
            
            if all_passed:
                print("\n" + "="*60)
                print("SUCCESS! ALL TESTS PASSED!")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("SOME TESTS FAILED - SEE DETAILS ABOVE")
                print("="*60)
            
            return all_passed
            
        except Exception as e:
            print(f"\n[!] Test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.client:
                self.client.close()


def main():
    """Main entry point"""
    print("="*60)
    print("HEDERA SMART CONTRACT TESTING")
    print("="*60)
    print(f"Network: {settings.hedera_network}")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)
    
    # Check if contract is deployed
    deployment_path = Path(__file__).parent.parent / "deployment.json"
    if not deployment_path.exists():
        print("\n[!] Contract not deployed!")
        print("Please run: python scripts/deploy_contract.py")
        sys.exit(1)
    
    print("\nWARNING: This will execute transactions on Hedera testnet.")
    print("   Estimated cost: ~30-40 HBAR for all tests")
    print("   Tests include:")
    print("   - Pay bill (10 HBAR)")
    print("   - Create dispute (5 HBAR escrow)")
    print("   - Resolve dispute")
    print("   - Minimum transfer validation")
    
    print("\nProceeding with tests automatically...")
    
    # Run tests
    tester = ContractTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
