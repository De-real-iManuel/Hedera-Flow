"""
USDC Service
Handles USDC payment operations for both Hedera and Ethereum networks
"""
from decimal import Decimal
from typing import Dict, Literal, Optional
import logging
import os

logger = logging.getLogger(__name__)

PaymentNetwork = Literal["hedera", "ethereum"]


class USDCService:
    """Service for USDC payment operations across multiple networks"""
    
    # USDC token addresses/IDs
    USDC_HEDERA_TESTNET = "0.0.456858"
    USDC_HEDERA_MAINNET = "0.0.456858"  # Update with actual mainnet ID when available
    USDC_ETHEREUM_MAINNET = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    USDC_ETHEREUM_SEPOLIA = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
    
    # USDC has 6 decimal places
    USDC_DECIMALS = 6
    
    def __init__(self, network: str = "testnet"):
        """
        Initialize USDC service
        
        Args:
            network: Network environment ('testnet' or 'mainnet')
        """
        self.network = network
        self.logger = logging.getLogger(__name__)
    
    def get_usdc_token_id(self, payment_network: PaymentNetwork) -> str:
        """
        Get USDC token address/ID for the specified network
        
        Args:
            payment_network: Target payment network ('hedera' or 'ethereum')
            
        Returns:
            Token ID (Hedera) or contract address (Ethereum)
        """
        if payment_network == "hedera":
            return self.USDC_HEDERA_TESTNET if self.network == "testnet" else self.USDC_HEDERA_MAINNET
        else:  # ethereum
            return self.USDC_ETHEREUM_SEPOLIA if self.network == "testnet" else self.USDC_ETHEREUM_MAINNET
    
    def calculate_usdc_amount(self, fiat_amount: Decimal, currency: str) -> Dict:
        """
        Calculate USDC amount from fiat currency
        
        USDC is pegged 1:1 with USD, so we convert fiat to USD first.
        
        Args:
            fiat_amount: Amount in fiat currency
            currency: Fiat currency code (EUR, USD, INR, BRL, NGN)
            
        Returns:
            Dictionary with USDC amount details:
            - usdc_amount: USDC amount as float
            - usdc_amount_raw: USDC amount in smallest units (6 decimals)
            - exchange_rate: Fiat to USD exchange rate
            - currency: Original currency code
        """
        # Exchange rates to USD (approximate - should be fetched from API in production)
        fiat_to_usd = {
            "USD": Decimal("1.0"),
            "EUR": Decimal("1.08"),      # 1 EUR ≈ 1.08 USD
            "INR": Decimal("0.012"),     # 1 INR ≈ 0.012 USD
            "BRL": Decimal("0.20"),      # 1 BRL ≈ 0.20 USD
            "NGN": Decimal("0.0013")     # 1 NGN ≈ 0.0013 USD
        }
        
        rate = fiat_to_usd.get(currency, Decimal("1.0"))
        usdc_amount = fiat_amount * rate
        
        # Round to 6 decimal places (USDC precision)
        usdc_amount_rounded = usdc_amount.quantize(Decimal("0.000001"))
        
        # Convert to smallest unit (multiply by 10^6)
        usdc_amount_raw = int(usdc_amount_rounded * Decimal(10 ** self.USDC_DECIMALS))
        
        self.logger.info(f"Calculated USDC amount: {fiat_amount} {currency} = {usdc_amount_rounded} USDC")
        
        return {
            "usdc_amount": float(usdc_amount_rounded),
            "usdc_amount_raw": usdc_amount_raw,
            "exchange_rate": float(rate),
            "currency": currency,
            "source": "fixed_rates"  # In production, use live rates
        }
    
    def verify_usdc_balance(
        self,
        account: str,
        required_amount: Decimal,
        network: PaymentNetwork
    ) -> Dict[str, any]:
        """
        Verify user has sufficient USDC balance
        
        Args:
            account: User's account ID (Hedera) or address (Ethereum)
            required_amount: Required USDC amount
            network: Payment network ('hedera' or 'ethereum')
            
        Returns:
            Dictionary with verification result:
            - has_sufficient_balance: Boolean
            - current_balance: Current USDC balance
            - required_amount: Required amount
            - deficit: Shortfall if insufficient
        """
        if network == "hedera":
            return self._verify_hedera_usdc_balance(account, required_amount)
        else:
            return self._verify_ethereum_usdc_balance(account, required_amount)
    
    def _verify_hedera_usdc_balance(self, account_id: str, required_amount: Decimal) -> Dict:
        """
        Check USDC balance on Hedera network
        
        Args:
            account_id: Hedera account ID (0.0.xxxxx format)
            required_amount: Required USDC amount
            
        Returns:
            Balance verification result
        """
        try:
            from hedera import AccountBalanceQuery, AccountId, TokenId
            from app.services.hedera_service import get_hedera_service
            
            self.logger.info(f"Checking Hedera USDC balance for account {account_id}")
            
            hedera_service = get_hedera_service()
            account = AccountId.fromString(account_id)
            token_id = TokenId.fromString(self.get_usdc_token_id("hedera"))
            
            # Query account balance
            balance_query = AccountBalanceQuery().setAccountId(account)
            balance = balance_query.execute(hedera_service.client)
            
            # Get USDC token balance (in smallest units)
            token_balance_raw = balance.tokens.get(token_id, 0)
            usdc_balance = Decimal(token_balance_raw) / Decimal(10 ** self.USDC_DECIMALS)
            
            has_sufficient = usdc_balance >= required_amount
            deficit = max(Decimal("0"), required_amount - usdc_balance)
            
            self.logger.info(f"Hedera USDC balance: {usdc_balance}, required: {required_amount}, sufficient: {has_sufficient}")
            
            return {
                "has_sufficient_balance": has_sufficient,
                "current_balance": float(usdc_balance),
                "required_amount": float(required_amount),
                "deficit": float(deficit),
                "network": "hedera"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check Hedera USDC balance: {e}")
            return {
                "has_sufficient_balance": False,
                "current_balance": 0.0,
                "required_amount": float(required_amount),
                "deficit": float(required_amount),
                "network": "hedera",
                "error": str(e)
            }
    
    def _verify_ethereum_usdc_balance(self, address: str, required_amount: Decimal) -> Dict:
        """
        Check USDC balance on Ethereum network
        
        Args:
            address: Ethereum address (0x... format)
            required_amount: Required USDC amount
            
        Returns:
            Balance verification result
        """
        try:
            from web3 import Web3
            
            self.logger.info(f"Checking Ethereum USDC balance for address {address}")
            
            # Get RPC URL from environment
            rpc_url = os.getenv(
                "ETHEREUM_RPC_URL",
                "https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
            )
            
            # Connect to Ethereum node
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                raise Exception("Failed to connect to Ethereum node")
            
            # USDC contract ABI (minimal - just balanceOf function)
            usdc_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            # Get USDC contract
            usdc_address = Web3.to_checksum_address(self.get_usdc_token_id("ethereum"))
            usdc_contract = w3.eth.contract(address=usdc_address, abi=usdc_abi)
            
            # Get balance (in smallest units)
            balance_raw = usdc_contract.functions.balanceOf(
                Web3.to_checksum_address(address)
            ).call()
            
            usdc_balance = Decimal(balance_raw) / Decimal(10 ** self.USDC_DECIMALS)
            
            has_sufficient = usdc_balance >= required_amount
            deficit = max(Decimal("0"), required_amount - usdc_balance)
            
            self.logger.info(f"Ethereum USDC balance: {usdc_balance}, required: {required_amount}, sufficient: {has_sufficient}")
            
            return {
                "has_sufficient_balance": has_sufficient,
                "current_balance": float(usdc_balance),
                "required_amount": float(required_amount),
                "deficit": float(deficit),
                "network": "ethereum"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check Ethereum USDC balance: {e}")
            return {
                "has_sufficient_balance": False,
                "current_balance": 0.0,
                "required_amount": float(required_amount),
                "deficit": float(required_amount),
                "network": "ethereum",
                "error": str(e)
            }
    
    def verify_usdc_transaction_hedera(
        self,
        transaction_id: str,
        expected_amount: Decimal,
        expected_recipient: str
    ) -> Dict:
        """
        Verify USDC transaction on Hedera network via Mirror Node
        
        Args:
            transaction_id: Hedera transaction ID
            expected_amount: Expected USDC amount
            expected_recipient: Expected recipient account ID
            
        Returns:
            Verification result with transaction details
        """
        try:
            import requests
            from datetime import datetime
            
            self.logger.info(f"Verifying Hedera USDC transaction: {transaction_id}")
            
            # Get Mirror Node URL
            mirror_url = os.getenv(
                "HEDERA_MIRROR_NODE_URL",
                "https://testnet.mirrornode.hedera.com"
            )
            
            # Query transaction
            url = f"{mirror_url}/api/v1/transactions/{transaction_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("transactions"):
                raise Exception("Transaction not found")
            
            tx = data["transactions"][0]
            
            # Verify transaction succeeded
            if tx.get("result") != "SUCCESS":
                raise Exception(f"Transaction failed: {tx.get('result')}")
            
            # Find token transfer in transaction
            token_transfers = tx.get("token_transfers", [])
            usdc_token_id = self.get_usdc_token_id("hedera")
            
            usdc_transfer = None
            for transfer in token_transfers:
                if transfer.get("token_id") == usdc_token_id:
                    if transfer.get("account") == expected_recipient and transfer.get("amount", 0) > 0:
                        usdc_transfer = transfer
                        break
            
            if not usdc_transfer:
                raise Exception("USDC transfer not found in transaction")
            
            # Verify amount (convert from smallest units)
            amount_raw = usdc_transfer.get("amount", 0)
            amount_usdc = Decimal(amount_raw) / Decimal(10 ** self.USDC_DECIMALS)
            
            # Allow 1% tolerance for rounding
            tolerance = expected_amount * Decimal("0.01")
            amount_diff = abs(amount_usdc - expected_amount)
            
            if amount_diff > tolerance:
                raise Exception(
                    f"Amount mismatch: expected {expected_amount}, got {amount_usdc}"
                )
            
            # Parse consensus timestamp
            consensus_timestamp = datetime.fromisoformat(
                tx.get("consensus_timestamp", "").replace("Z", "+00:00")
            )
            
            self.logger.info(f"✅ Hedera USDC transaction verified: {amount_usdc} USDC")
            
            return {
                "verified": True,
                "amount_usdc": float(amount_usdc),
                "recipient": expected_recipient,
                "consensus_timestamp": consensus_timestamp,
                "transaction_id": transaction_id,
                "network": "hedera"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to verify Hedera USDC transaction: {e}")
            return {
                "verified": False,
                "error": str(e),
                "network": "hedera"
            }
    
    def verify_usdc_transaction_ethereum(
        self,
        tx_hash: str,
        expected_amount: Decimal,
        expected_recipient: str
    ) -> Dict:
        """
        Verify USDC transaction on Ethereum network
        
        Args:
            tx_hash: Ethereum transaction hash
            expected_amount: Expected USDC amount
            expected_recipient: Expected recipient address
            
        Returns:
            Verification result with transaction details
        """
        try:
            from web3 import Web3
            from datetime import datetime
            
            self.logger.info(f"Verifying Ethereum USDC transaction: {tx_hash}")
            
            # Connect to Ethereum node
            rpc_url = os.getenv(
                "ETHEREUM_RPC_URL",
                "https://sepolia.infura.io/v3/YOUR_INFURA_KEY"
            )
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                raise Exception("Failed to connect to Ethereum node")
            
            # Get transaction receipt
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            if not tx_receipt:
                raise Exception("Transaction not found")
            
            if tx_receipt.status != 1:
                raise Exception("Transaction failed")
            
            # Parse Transfer event from logs
            # Transfer event signature: Transfer(address,address,uint256)
            transfer_topic = Web3.keccak(text="Transfer(address,address,uint256)").hex()
            
            usdc_address = Web3.to_checksum_address(self.get_usdc_token_id("ethereum"))
            
            transfer_log = None
            for log in tx_receipt.logs:
                if (log.address.lower() == usdc_address.lower() and
                    log.topics[0].hex() == transfer_topic):
                    transfer_log = log
                    break
            
            if not transfer_log:
                raise Exception("USDC transfer event not found")
            
            # Decode transfer amount (last 32 bytes of data)
            amount_raw = int.from_bytes(transfer_log.data, byteorder='big')
            amount_usdc = Decimal(amount_raw) / Decimal(10 ** self.USDC_DECIMALS)
            
            # Verify recipient (second topic)
            recipient_from_log = "0x" + transfer_log.topics[2].hex()[-40:]
            
            if recipient_from_log.lower() != expected_recipient.lower():
                raise Exception(
                    f"Recipient mismatch: expected {expected_recipient}, got {recipient_from_log}"
                )
            
            # Verify amount (allow 1% tolerance)
            tolerance = expected_amount * Decimal("0.01")
            amount_diff = abs(amount_usdc - expected_amount)
            
            if amount_diff > tolerance:
                raise Exception(
                    f"Amount mismatch: expected {expected_amount}, got {amount_usdc}"
                )
            
            # Get block timestamp
            block = w3.eth.get_block(tx_receipt.blockNumber)
            timestamp = datetime.fromtimestamp(block.timestamp)
            
            self.logger.info(f"✅ Ethereum USDC transaction verified: {amount_usdc} USDC")
            
            return {
                "verified": True,
                "amount_usdc": float(amount_usdc),
                "recipient": expected_recipient,
                "timestamp": timestamp,
                "transaction_hash": tx_hash,
                "block_number": tx_receipt.blockNumber,
                "network": "ethereum"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to verify Ethereum USDC transaction: {e}")
            return {
                "verified": False,
                "error": str(e),
    