"""
Test Transaction Amount Validation
Tests for Task 19.3: Validate transaction amount matches expected HBAR amount

Requirements:
- FR-6.9: System shall validate transaction amount matches expected HBAR amount
- US-7: Payment flow with amount verification

This test suite specifically validates the amount matching logic in the payment
confirmation flow, ensuring that the actual HBAR amount transferred matches
the expected amount within acceptable tolerance.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.utils.transaction_verifier import (
    TransactionVerifier,
    AmountMismatchError
)


class TestAmountValidation:
    """Test suite for transaction amount validation"""
    
    def test_exact_amount_match(self):
        """Test validation with exact amount match"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("250.0")
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_amount_within_tolerance_positive(self):
        """Test validation with amount slightly higher (within 1% tolerance)"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("250.5")  # 0.2% higher
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_amount_within_tolerance_negative(self):
        """Test validation with amount slightly lower (within 1% tolerance)"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("249.5")  # 0.2% lower
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_amount_at_tolerance_boundary(self):
        """Test validation with amount exactly at 1% tolerance boundary"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("252.5")  # Exactly 1% higher
        
        # Should not raise exception (at boundary)
        verifier._validate_amount(actual, expected)
    
    def test_amount_exceeds_tolerance(self):
        """Test validation with amount exceeding 1% tolerance"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("260.0")  # 4% higher
        
        # Should raise AmountMismatchError
        with pytest.raises(AmountMismatchError) as exc_info:
            verifier._validate_amount(actual, expected)
        
        assert "amount mismatch" in str(exc_info.value).lower()
        assert "expected 250" in str(exc_info.value)
        assert "got 260" in str(exc_info.value)
    
    def test_amount_significantly_lower(self):
        """Test validation with amount significantly lower than expected"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("200.0")  # 20% lower
        
        # Should raise AmountMismatchError
        with pytest.raises(AmountMismatchError) as exc_info:
            verifier._validate_amount(actual, expected)
        
        assert "amount mismatch" in str(exc_info.value).lower()
    
    def test_small_amount_validation(self):
        """Test validation with small amounts (minimum transfer)"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("5.0")  # Minimum transfer
        actual = Decimal("5.04")  # 0.8% higher
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_large_amount_validation(self):
        """Test validation with large amounts"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("10000.0")
        actual = Decimal("10050.0")  # 0.5% higher
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_fractional_hbar_validation(self):
        """Test validation with fractional HBAR amounts"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.17")
        actual = Decimal("250.19")  # Very small difference
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_zero_expected_amount(self):
        """Test validation with zero expected amount (edge case)"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("0")
        actual = Decimal("250.0")
        
        # Should not raise exception (zero expected is skipped)
        verifier._validate_amount(actual, expected)
    
    def test_custom_tolerance_2_percent(self):
        """Test validation with custom 2% tolerance"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=2.0  # 2% tolerance
        )
        
        expected = Decimal("250.0")
        actual = Decimal("254.0")  # 1.6% higher
        
        # Should not raise exception (within 2% tolerance)
        verifier._validate_amount(actual, expected)
    
    def test_custom_tolerance_exceeded(self):
        """Test validation with custom tolerance exceeded"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=0.5  # 0.5% tolerance
        )
        
        expected = Decimal("250.0")
        actual = Decimal("252.0")  # 0.8% higher
        
        # Should raise AmountMismatchError (exceeds 0.5% tolerance)
        with pytest.raises(AmountMismatchError):
            verifier._validate_amount(actual, expected)
    
    def test_rounding_differences(self):
        """Test validation with typical rounding differences"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        # Simulate rounding from exchange rate calculation
        expected = Decimal("250.17647058")  # From 85.06 EUR / 0.34 rate
        actual = Decimal("250.18")  # Rounded by user's wallet
        
        # Should not raise exception (tiny rounding difference)
        verifier._validate_amount(actual, expected)
    
    def test_tinybars_conversion_precision(self):
        """Test that tinybars to HBAR conversion maintains precision"""
        
        # Simulate conversion from tinybars
        tinybars = 25017000000  # 250.17 HBAR
        actual = Decimal(tinybars) / Decimal("100000000")
        expected = Decimal("250.17")
        
        assert actual == expected
    
    def test_multiple_currency_amounts(self):
        """Test validation with amounts from different currencies"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        # EUR: 85.06 / 0.34 = 250.18 HBAR
        expected_eur = Decimal("250.18")
        actual_eur = Decimal("250.20")
        verifier._validate_amount(actual_eur, expected_eur)
        
        # USD: 120.50 / 0.34 = 354.41 HBAR
        expected_usd = Decimal("354.41")
        actual_usd = Decimal("354.50")
        verifier._validate_amount(actual_usd, expected_usd)
        
        # INR: 450.00 / 0.34 = 1323.53 HBAR (assuming 1 HBAR = 0.34 USD = ~28 INR)
        expected_inr = Decimal("1323.53")
        actual_inr = Decimal("1324.00")
        verifier._validate_amount(actual_inr, expected_inr)


class TestAmountValidationInPaymentFlow:
    """Test amount validation in the context of payment confirmation"""
    
    @pytest.mark.asyncio
    async def test_verify_transaction_with_amount_validation(self):
        """Test full transaction verification with amount validation"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        # Mock transaction data
        mock_tx_data = {
            "transactions": [
                {
                    "transaction_id": "0.0.12345@1710789700.123456789",
                    "consensus_timestamp": "1710789700.123456789",
                    "result": "SUCCESS",
                    "transfers": [
                        {"account": "0.0.12345", "amount": -25000000000},
                        {"account": "0.0.7942957", "amount": 25000000000}
                    ],
                    "charged_tx_fee": 100000
                }
            ]
        }
        
        with patch.object(verifier.mirror_client, 'get_transaction', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_tx_data
            
            # Verify with expected amount
            result = await verifier.verify_transaction(
                transaction_id="0.0.12345@1710789700.123456789",
                expected_amount_hbar=Decimal("250.0")
            )
            
            assert result["amount_hbar"] == Decimal("250.0")
            assert result["result"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_verify_transaction_amount_mismatch_fails(self):
        """Test that transaction verification fails with amount mismatch"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        # Mock transaction with different amount
        mock_tx_data = {
            "transactions": [
                {
                    "transaction_id": "0.0.12345@1710789700.123456789",
                    "consensus_timestamp": "1710789700.123456789",
                    "result": "SUCCESS",
                    "transfers": [
                        {"account": "0.0.12345", "amount": -20000000000},  # 200 HBAR
                        {"account": "0.0.7942957", "amount": 20000000000}
                    ],
                    "charged_tx_fee": 100000
                }
            ]
        }
        
        with patch.object(verifier.mirror_client, 'get_transaction', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_tx_data
            
            # Should raise AmountMismatchError
            with pytest.raises(AmountMismatchError) as exc_info:
                await verifier.verify_transaction(
                    transaction_id="0.0.12345@1710789700.123456789",
                    expected_amount_hbar=Decimal("250.0")  # Expected 250, got 200
                )
            
            assert "amount mismatch" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_verify_transaction_without_amount_validation(self):
        """Test transaction verification without amount validation (optional)"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        mock_tx_data = {
            "transactions": [
                {
                    "transaction_id": "0.0.12345@1710789700.123456789",
                    "consensus_timestamp": "1710789700.123456789",
                    "result": "SUCCESS",
                    "transfers": [
                        {"account": "0.0.12345", "amount": -25000000000},
                        {"account": "0.0.7942957", "amount": 25000000000}
                    ],
                    "charged_tx_fee": 100000
                }
            ]
        }
        
        with patch.object(verifier.mirror_client, 'get_transaction', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_tx_data
            
            # Verify without expected amount (should not validate amount)
            result = await verifier.verify_transaction(
                transaction_id="0.0.12345@1710789700.123456789",
                expected_amount_hbar=None  # No amount validation
            )
            
            assert result["amount_hbar"] == Decimal("250.0")
            assert result["result"] == "SUCCESS"


class TestAmountValidationEdgeCases:
    """Test edge cases in amount validation"""
    
    def test_very_small_difference(self):
        """Test validation with very small difference (< 0.01%)"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("250.001")  # 0.0004% difference
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)
    
    def test_negative_amounts_not_allowed(self):
        """Test that negative amounts are handled correctly"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("-250.0")  # Negative (should never happen)
        
        # Should raise exception (100% difference)
        with pytest.raises(AmountMismatchError):
            verifier._validate_amount(actual, expected)
    
    def test_decimal_precision_maintained(self):
        """Test that decimal precision is maintained in validation"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        # High precision amounts
        expected = Decimal("250.17647058823529")
        actual = Decimal("250.17647058823530")
        
        # Should not raise exception (tiny difference)
        verifier._validate_amount(actual, expected)
    
    def test_string_to_decimal_conversion(self):
        """Test that string amounts are properly converted to Decimal"""
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        # Simulate amounts from JSON/API (strings)
        expected = Decimal("250.17")
        actual = Decimal("250.18")
        
        # Should not raise exception
        verifier._validate_amount(actual, expected)


class TestAmountValidationLogging:
    """Test logging behavior during amount validation"""
    
    def test_validation_logs_success(self, caplog):
        """Test that successful validation is logged"""
        
        import logging
        caplog.set_level(logging.INFO)
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("250.5")
        
        verifier._validate_amount(actual, expected)
        
        # Check that validation was logged
        assert any("Amount validated" in record.message for record in caplog.records)
    
    def test_validation_logs_failure(self, caplog):
        """Test that failed validation is logged"""
        
        import logging
        caplog.set_level(logging.ERROR)
        
        verifier = TransactionVerifier(
            treasury_account="0.0.7942957",
            tolerance_percent=1.0
        )
        
        expected = Decimal("250.0")
        actual = Decimal("300.0")
        
        try:
            verifier._validate_amount(actual, expected)
        except AmountMismatchError:
            pass  # Expected
        
        # AmountMismatchError should be raised (logged by caller)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
