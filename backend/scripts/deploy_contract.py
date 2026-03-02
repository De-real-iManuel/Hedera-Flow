#!/usr/bin/env python3
"""
Hedera Smart Contract Deployment Script

This script deploys the BillingSettlement.sol contract to Hedera testnet.

Requirements:
- Compiled contract bytecode (from hardhat compilation)
- Hedera operator account with sufficient HBAR
- Environment variables configured (.env file)

Usage:
    python scripts/deploy_contract.py

The script will:
1. Load compiled contract bytecode from artifacts
2. Create a FileCreateTransaction to upload bytecode
3. Create a ContractCreateTransaction to deploy the contract
4. Save the deployed contract ID to .env and a deployment log file
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from hedera import (
    Client,
    AccountId,
    PrivateKey,
    FileCreateTransaction,
    FileAppendTransaction,
    ContractCreateTransaction,
    ContractFunctionParameters,
    Hbar,
    Status
)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


class ContractDeployer:
    """Handles deployment of smart contracts to Hedera testnet"""
    
    def __init__(self):
        """Initialize Hedera client and load configuration"""
        self.client = None
        self.operator_id = None
        self.operator_key = None
        self.contract_bytecode = None
        self.contract_id = None
        self.file_id = None
        
    def setup_client(self):
        """Set up Hedera client with operator credentials"""
        print("[*] Setting up Hedera client...")
        
        # Get operator credentials from environment
        operator_id_str = settings.hedera_operator_id
        operator_key_str = settings.hedera_operator_key
        
        if not operator_id_str or not operator_key_str:
            raise ValueError(
                "Missing Hedera credentials. Please set HEDERA_OPERATOR_ID "
                "and HEDERA_OPERATOR_KEY in .env file"
            )
        
        # Parse operator ID and key
        self.operator_id = AccountId.fromString(operator_id_str)
        self.operator_key = PrivateKey.fromString(operator_key_str)
        
        # Create client for testnet
        if settings.hedera_network == "testnet":
            self.client = Client.forTestnet()
        elif settings.hedera_network == "mainnet":
            self.client = Client.forMainnet()
        else:
            raise ValueError(f"Invalid network: {settings.hedera_network}")
        
        # Set operator
        self.client.setOperator(self.operator_id, self.operator_key)
        
        # Set default max transaction fee (100 HBAR)
        self.client.setDefaultMaxTransactionFee(Hbar(100))
        
        # Set default max query payment (1 HBAR)
        self.client.setDefaultMaxQueryPayment(Hbar(1))
        
        # Note: Request timeout is set via Java Duration, but we'll rely on default for now
        # The default timeout should be sufficient for testnet operations
        
        print(f"[+] Client configured for {settings.hedera_network}")
        print(f"    Operator: {self.operator_id}")
        
    def load_contract_bytecode(self):
        """Load compiled contract bytecode from artifacts"""
        print("\n[*] Loading contract bytecode...")
        
        # Path to compiled contract
        artifact_path = Path(__file__).parent.parent / "artifacts" / "contracts" / "BillingSettlement.sol" / "BillingSettlement.json"
        
        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Contract artifact not found at {artifact_path}\n"
                "Please compile the contract first using: npx hardhat compile"
            )
        
        # Load artifact
        with open(artifact_path, 'r') as f:
            artifact = json.load(f)
        
        # Get bytecode (remove '0x' prefix if present)
        bytecode_hex = artifact.get('bytecode', '')
        
        if not bytecode_hex or bytecode_hex == '0x':
            raise ValueError(
                "Contract bytecode is empty. This usually means:\n"
                "1. Contract has compilation errors\n"
                "2. Contract is abstract or interface\n"
                "Please check the contract and recompile."
            )
        
        if bytecode_hex.startswith('0x'):
            bytecode_hex = bytecode_hex[2:]
        
        # Validate hex string
        if len(bytecode_hex) % 2 != 0:
            raise ValueError("Bytecode hex string has odd length - corrupted bytecode")
        
        # Convert hex to bytes
        try:
            self.contract_bytecode = bytes.fromhex(bytecode_hex)
        except ValueError as e:
            raise ValueError(f"Invalid bytecode hex string: {e}")
        
        bytecode_size_kb = len(self.contract_bytecode) / 1024
        print(f"[+] Bytecode loaded: {bytecode_size_kb:.2f} KB")
        print(f"    Bytecode length: {len(self.contract_bytecode)} bytes")
        print(f"    First 20 bytes: {self.contract_bytecode[:20].hex()}")
        
        if bytecode_size_kb > 100:
            print("[!] Warning: Bytecode is large, may require multiple append transactions")
        
    def upload_bytecode_to_file(self):
        """Upload contract bytecode to Hedera File Service"""
        print("\n[*] Uploading bytecode to Hedera File Service...")
        
        # Hedera file size limit per transaction
        # Use smaller chunks to avoid issues
        chunk_size = 2048  # 2KB chunks (safer for Hedera)
        
        # Create file with first chunk
        first_chunk = self.contract_bytecode[:chunk_size]
        
        file_create_tx = FileCreateTransaction()
        # Note: setKeys expects individual keys, not a list
        file_create_tx.setKeys(self.operator_key.getPublicKey())
        file_create_tx.setContents(first_chunk)
        file_create_tx.setMaxTransactionFee(Hbar(2))
        
        print("    Creating file...")
        file_create_submit = file_create_tx.execute(self.client)
        file_create_receipt = file_create_submit.getReceipt(self.client)
        
        # Get status name
        try:
            status_name = file_create_receipt.status.name()
            print(f"    File creation status: {status_name}")
            
            if status_name != "SUCCESS":
                raise Exception(f"File creation failed with status: {status_name}")
        except AttributeError:
            # If name() doesn't work, just proceed and check if we got a file ID
            print(f"    Status check skipped, verifying file ID...")
        
        self.file_id = file_create_receipt.fileId
        if not self.file_id:
            raise Exception("File creation failed: No file ID returned")
            
        print(f"[+] File created: {self.file_id}")
        
        # Append remaining chunks if needed
        remaining_bytes = self.contract_bytecode[chunk_size:]
        if remaining_bytes:
            print(f"    Appending {len(remaining_bytes)} remaining bytes...")
            
            # Split into chunks
            chunks = [
                remaining_bytes[i:i + chunk_size]
                for i in range(0, len(remaining_bytes), chunk_size)
            ]
            
            for i, chunk in enumerate(chunks, 1):
                print(f"    Appending chunk {i}/{len(chunks)}...")
                
                file_append_tx = FileAppendTransaction()
                file_append_tx.setFileId(self.file_id)
                file_append_tx.setContents(chunk)
                file_append_tx.setMaxTransactionFee(Hbar(2))
                
                file_append_submit = file_append_tx.execute(self.client)
                file_append_receipt = file_append_submit.getReceipt(self.client)
                
                # Check status
                try:
                    status_name = file_append_receipt.status.name()
                    if status_name != "SUCCESS":
                        raise Exception(f"File append failed with status: {status_name}")
                except AttributeError:
                    # Status check not critical for append
                    pass
            
            print(f"[+] All chunks appended successfully")
        
    def deploy_contract(self):
        """Deploy contract from uploaded bytecode file"""
        print("\n[*] Deploying contract...")
        
        # Create contract
        contract_create_tx = ContractCreateTransaction()
        contract_create_tx.setBytecodeFileId(self.file_id)
        contract_create_tx.setGas(500000)  # Increased gas limit
        # Don't set constructor parameters if constructor has no params
        contract_create_tx.setMaxTransactionFee(Hbar(100))  # Higher fee limit
        
        print("    Submitting contract creation transaction...")
        contract_create_submit = contract_create_tx.execute(self.client)
        
        print("    Waiting for consensus (this may take 30-60 seconds)...")
        contract_create_receipt = contract_create_submit.getReceipt(self.client)
        
        # Check status
        try:
            status_name = contract_create_receipt.status.name()
            print(f"    Contract creation status: {status_name}")
            
            if status_name != "SUCCESS":
                raise Exception(f"Contract deployment failed with status: {status_name}")
        except AttributeError:
            print(f"    Status check skipped, verifying contract ID...")
        
        self.contract_id = contract_create_receipt.contractId
        if not self.contract_id:
            raise Exception("Contract deployment failed: No contract ID returned")
            
        print(f"[+] Contract deployed: {self.contract_id}")
        
    def save_deployment_info(self):
        """Save deployment information to files"""
        print("\n[*] Saving deployment information...")
        
        # Create deployment log
        deployment_info = {
            "contract_id": str(self.contract_id),
            "file_id": str(self.file_id),
            "network": settings.hedera_network,
            "operator_id": str(self.operator_id),
            "deployed_at": datetime.utcnow().isoformat(),
            "contract_name": "BillingSettlement",
            "solidity_version": "0.8.0"
        }
        
        # Save to JSON file
        deployment_log_path = Path(__file__).parent.parent / "deployment.json"
        with open(deployment_log_path, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"[+] Deployment info saved to: {deployment_log_path}")
        
        # Update .env file with contract ID
        env_path = Path(__file__).parent.parent / ".env"
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Check if HEDERA_CONTRACT_ID already exists
            if 'HEDERA_CONTRACT_ID=' in env_content:
                # Replace existing value
                lines = env_content.split('\n')
                new_lines = []
                for line in lines:
                    if line.startswith('HEDERA_CONTRACT_ID='):
                        new_lines.append(f'HEDERA_CONTRACT_ID={self.contract_id}')
                    else:
                        new_lines.append(line)
                env_content = '\n'.join(new_lines)
            else:
                # Append new variable
                if not env_content.endswith('\n'):
                    env_content += '\n'
                env_content += f'\n# Smart Contract\nHEDERA_CONTRACT_ID={self.contract_id}\n'
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            print(f"[+] Contract ID added to .env file")
        
        # Print summary
        print("\n" + "="*60)
        print("SUCCESS! DEPLOYMENT COMPLETE!")
        print("="*60)
        print(f"Contract ID:  {self.contract_id}")
        print(f"File ID:      {self.file_id}")
        print(f"Network:      {settings.hedera_network}")
        print(f"Explorer:     https://hashscan.io/{settings.hedera_network}/contract/{self.contract_id}")
        print("="*60)
        
    def deploy(self):
        """Execute full deployment process"""
        try:
            self.setup_client()
            self.load_contract_bytecode()
            self.upload_bytecode_to_file()
            self.deploy_contract()
            self.save_deployment_info()
            
        except Exception as e:
            print(f"\n[!] Deployment failed: {e}")
            raise
        
        finally:
            if self.client:
                self.client.close()


def main():
    """Main entry point"""
    print("="*60)
    print("HEDERA SMART CONTRACT DEPLOYMENT")
    print("="*60)
    print(f"Network: {settings.hedera_network}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print("="*60)
    
    # Check if contract is already compiled
    artifact_path = Path(__file__).parent.parent / "artifacts" / "contracts" / "BillingSettlement.sol" / "BillingSettlement.json"
    if not artifact_path.exists():
        print("\n[!] Contract not compiled!")
        print("Please run: npx hardhat compile")
        sys.exit(1)
    
    # Confirm deployment
    print("\nWARNING: This will deploy the BillingSettlement contract to Hedera testnet.")
    print("   This operation will cost HBAR for:")
    print("   - File creation and storage")
    print("   - Contract deployment")
    print("   - Estimated cost: ~20-30 HBAR")
    
    # Auto-confirm for automated deployment
    print("\nProceeding with deployment automatically...")
    
    # Deploy
    deployer = ContractDeployer()
    deployer.deploy()


if __name__ == "__main__":
    main()
