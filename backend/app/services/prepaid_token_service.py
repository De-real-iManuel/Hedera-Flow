"""
Prepaid Token Service for Hedera Flow MVP

Implements prepaid electricity token management:
- Token purchase with HBAR/USDC payment
- Token ID generation (TOKEN-{COUNTRY}-{YEAR}-{SEQ})
- Units calculation based on tariff rates
- FIFO token deduction for consumption
- Low balance alerts and status management
- HCS logging for token issuance

Requirements: FR-8.1 to FR-8.12, US-13 to US-15
Spec: prepaid-smart-meter-mvp
"""
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import uuid
import time

from app.services.tariff_service import get_tariff, TariffNotFoundError
from app.services.exchange_rate_service import get_hbar_price
# from app.services.hedera_service import get_hedera_service  # Temporarily disabled
from app.services.sts_token_generator import STSTokenGenerator

logger = logging.getLogger(__name__)


class PrepaidTokenError(Exception):
    """Raised when prepaid token operation fails"""
    pass


class PrepaidTokenService:
    """Service for prepaid electricity token management"""
    
    def __init__(self, db: Session):
        """
        Initialize prepaid token service
        
        Args:
            db: Database session
        """
        self.db = db
        self.hedera_service = get_hedera_service()
    
    def get_topic_for_country(self, country_code: str) -> Optional[str]:
        """
        Get HCS topic ID based on country code.
        
        Maps country codes to regional HCS topics for logging prepaid token
        issuance and consumption events. This enables regional audit trails
        and compliance with data sovereignty requirements.
        
        Regional Topic Mapping:
        - EU: Spain (ES) → HCS_TOPIC_EU
        - US: United States (US) → HCS_TOPIC_US
        - Asia: India (IN) → HCS_TOPIC_ASIA
        - South America: Brazil (BR) → HCS_TOPIC_SA
        - Africa: Nigeria (NG) → HCS_TOPIC_AFRICA
        
        Args:
            country_code: ISO 3166-1 alpha-2 country code (ES, US, IN, BR, NG)
        
        Returns:
            HCS topic ID string (e.g., "0.0.5078302") or None if not configured
        
        Raises:
            PrepaidTokenError: If country code is not supported
        
        Requirements: FR-8.7 (HCS logging), Task 1.4
        """
        from config import settings
        
        # Country to region mapping
        country_to_region = {
            'ES': settings.hcs_topic_eu,      # Spain → EU
            'US': settings.hcs_topic_us,      # USA → US
            'IN': settings.hcs_topic_asia,    # India → Asia
            'BR': settings.hcs_topic_sa,      # Brazil → South America
            'NG': settings.hcs_topic_africa   # Nigeria → Africa
        }
        
        # Validate country code
        if country_code not in country_to_region:
            raise PrepaidTokenError(
                f"Unsupported country code: {country_code}. "
                f"Supported countries: {', '.join(country_to_region.keys())}"
            )
        
        topic_id = country_to_region[country_code]
        
        # Log warning if topic not configured
        if not topic_id or topic_id == "0.0.xxxxx":
            logger.warning(
                f"HCS topic not configured for country {country_code}. "
                f"Token issuance will proceed without HCS logging."
            )
            return None
        
        logger.info(f"Selected HCS topic {topic_id} for country {country_code}")
        return topic_id
    
    def calculate_units_from_fiat(
        self,
        amount_fiat: float,
        country_code: str,
        utility_provider: str
    ) -> Dict[str, Any]:
        """
        Calculate kWh units from fiat amount based on tariff rate.
        
        Uses the base tariff rate to calculate units. For tiered/time-of-use
        tariffs, uses the first tier or average rate.
        
        Args:
            amount_fiat: Amount in fiat currency
            country_code: Country code (ES, US, IN, BR, NG)
            utility_provider: Utility provider name
        
        Returns:
            Dictionary containing:
                - units_kwh: Calculated kWh units
                - tariff_rate: Rate used for calculation (per kWh)
                - currency: Currency code
        
        Raises:
            PrepaidTokenError: If calculation fails
            TariffNotFoundError: If no active tariff found
        
        Requirements: FR-8.3
        """
        try:
            # Fetch tariff data
            tariff_data = get_tariff(
                db=self.db,
                country_code=country_code,
                utility_provider=utility_provider,
                use_cache=True
            )
            
            rate_structure = tariff_data.get('rate_structure', {})
            rate_type = rate_structure.get('type')
            currency = tariff_data.get('currency', 'USD')
            
            # Extract base rate based on tariff type
            if rate_type == 'flat':
                tariff_rate = rate_structure.get('rate', 0)
            elif rate_type == 'tiered':
                # Use first tier rate
                tiers = rate_structure.get('tiers', [])
                if not tiers:
                    raise PrepaidTokenError("No tiers defined in tariff")
                tariff_rate = tiers[0].get('price', 0)
            elif rate_type == 'time_of_use':
                # Use average of all period rates
                periods = rate_structure.get('periods', [])
                if not periods:
                    raise PrepaidTokenError("No periods defined in tariff")
                tariff_rate = sum(p.get('price', 0) for p in periods) / len(periods)
            elif rate_type == 'band_based':
                # Use first band rate
                bands = rate_structure.get('bands', [])
                if not bands:
                    raise PrepaidTokenError("No bands defined in tariff")
                tariff_rate = bands[0].get('price', 0)
            else:
                raise PrepaidTokenError(f"Unknown tariff type: {rate_type}")
            
            if tariff_rate <= 0:
                raise PrepaidTokenError("Invalid tariff rate")
            
            # Calculate units: amount / rate
            units_kwh = Decimal(str(amount_fiat)) / Decimal(str(tariff_rate))
            
            logger.info(
                f"Calculated units: {amount_fiat} {currency} / "
                f"{tariff_rate} per kWh = {units_kwh} kWh"
            )
            
            return {
                'units_kwh': float(units_kwh.quantize(Decimal('0.01'))),
                'tariff_rate': float(Decimal(str(tariff_rate)).quantize(Decimal('0.000001'))),
                'currency': currency
            }
            
        except TariffNotFoundError:
            raise
        except PrepaidTokenError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate units from fiat: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to calculate units: {str(e)}")
    
    def get_hbar_exchange_rate(
        self,
        currency: str,
        use_cache: bool = True
    ) -> float:
        """
        Get current HBAR exchange rate for specified currency.
        
        Reuses existing ExchangeRateService to fetch HBAR price.
        
        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use Redis cache (default: True)
        
        Returns:
            HBAR price in specified currency (e.g., 0.34 for EUR)
        
        Raises:
            PrepaidTokenError: If exchange rate fetch fails
        
        Requirements: FR-8.1, US-13
        """
        try:
            # Use existing exchange rate service
            hbar_price = get_hbar_price(
                db=self.db,
                currency=currency,
                use_cache=use_cache
            )
            
            logger.info(f"Fetched HBAR exchange rate: 1 HBAR = {hbar_price} {currency}")
            return hbar_price
            
        except Exception as e:
            logger.error(f"Failed to fetch HBAR exchange rate: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to fetch exchange rate: {str(e)}")
    
    def calculate_hbar_amount(
        self,
        amount_fiat: float,
        currency: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate HBAR amount needed for fiat payment.
        
        Args:
            amount_fiat: Amount in fiat currency
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use cached exchange rate
        
        Returns:
            Dictionary containing:
                - amount_hbar: HBAR amount needed
                - exchange_rate: Exchange rate used (fiat per HBAR)
                - currency: Currency code
        
        Raises:
            PrepaidTokenError: If calculation fails
        
        Requirements: FR-8.1, US-13
        """
        try:
            # Get current HBAR price
            hbar_price = self.get_hbar_exchange_rate(currency, use_cache)
            
            # Calculate HBAR amount: fiat_amount / hbar_price
            amount_hbar = Decimal(str(amount_fiat)) / Decimal(str(hbar_price))
            
            logger.info(
                f"Calculated HBAR amount: {amount_fiat} {currency} / "
                f"{hbar_price} per HBAR = {amount_hbar} HBAR"
            )
            
            return {
                'amount_hbar': float(amount_hbar.quantize(Decimal('0.00000001'))),
                'exchange_rate': float(Decimal(str(hbar_price)).quantize(Decimal('0.000001'))),
                'currency': currency
            }
            
        except PrepaidTokenError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate HBAR amount: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to calculate HBAR amount: {str(e)}")

    def generate_token_id(
        self,
        country_code: str,
        year: Optional[int] = None
    ) -> str:
        """
        Generate unique token ID in format: TOKEN-{COUNTRY}-{YEAR}-{SEQ}
        
        Example: TOKEN-ES-2026-001
        
        Args:
            country_code: Country code (ES, US, IN, BR, NG)
            year: Year (defaults to current year)
        
        Returns:
            Generated token ID
        
        Requirements: FR-8.4
        """
        try:
            if year is None:
                year = datetime.now().year
            
            # Get next sequence number for this country/year
            query = text("""
                SELECT COUNT(*) + 1
                FROM prepaid_tokens
                WHERE token_id LIKE :pattern
            """)
            
            pattern = f"TOKEN-{country_code}-{year}-%"
            result = self.db.execute(query, {'pattern': pattern}).fetchone()
            sequence = result[0] if result else 1
            
            # Format: TOKEN-{COUNTRY}-{YEAR}-{SEQ:03d}
            token_id = f"TOKEN-{country_code}-{year}-{sequence:03d}"
            
            logger.info(f"Generated token ID: {token_id}")
            return token_id
            
        except Exception as e:
            logger.error(f"Failed to generate token ID: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to generate token ID: {str(e)}")
    def get_hbar_exchange_rate(
        self,
        currency: str,
        use_cache: bool = True
    ) -> float:
        """
        Get current HBAR exchange rate for specified currency.

        Reuses existing ExchangeRateService to fetch HBAR price.

        Args:
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use Redis cache (default: True)

        Returns:
            HBAR price in specified currency (e.g., 0.34 for EUR)

        Raises:
            PrepaidTokenError: If exchange rate fetch fails

        Requirements: FR-8.1, US-13
        """
        try:
            # Use existing exchange rate service
            hbar_price = get_hbar_price(
                db=self.db,
                currency=currency,
                use_cache=use_cache
            )

            logger.info(f"Fetched HBAR exchange rate: 1 HBAR = {hbar_price} {currency}")
            return hbar_price

        except Exception as e:
            logger.error(f"Failed to fetch HBAR exchange rate: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to fetch exchange rate: {str(e)}")

    def calculate_hbar_amount(
        self,
        amount_fiat: float,
        currency: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate HBAR amount needed for fiat payment.

        Args:
            amount_fiat: Amount in fiat currency
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            use_cache: Whether to use cached exchange rate

        Returns:
            Dictionary containing:
                - amount_hbar: HBAR amount needed
                - exchange_rate: Exchange rate used (fiat per HBAR)
                - currency: Currency code

        Raises:
            PrepaidTokenError: If calculation fails

        Requirements: FR-8.1, US-13
        """
        try:
            # Get current HBAR price
            hbar_price = self.get_hbar_exchange_rate(currency, use_cache)

            # Calculate HBAR amount: fiat_amount / hbar_price
            amount_hbar = Decimal(str(amount_fiat)) / Decimal(str(hbar_price))

            logger.info(
                f"Calculated HBAR amount: {amount_fiat} {currency} / "
                f"{hbar_price} per HBAR = {amount_hbar} HBAR"
            )

            return {
                'amount_hbar': float(amount_hbar.quantize(Decimal('0.00000001'))),
                'exchange_rate': float(Decimal(str(hbar_price)).quantize(Decimal('0.000001'))),
                'currency': currency
            }

        except PrepaidTokenError:
            raise
        except Exception as e:
            logger.error(f"Failed to calculate HBAR amount: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to calculate HBAR amount: {str(e)}")


    
    def create_token(
        self,
        user_id: str,
        meter_id: str,
        amount_fiat: float,
        currency: str,
        country_code: str,
        utility_provider: str,
        payment_method: str = 'HBAR',
        amount_crypto: Optional[float] = None,
        exchange_rate: Optional[float] = None,
        hedera_tx_id: Optional[str] = None,
        hcs_topic_id: Optional[str] = None,
        hcs_sequence_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new prepaid token after successful payment.

        Args:
            user_id: User UUID
            meter_id: Meter UUID
            amount_fiat: Amount paid in fiat currency
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            country_code: Country code (ES, US, IN, BR, NG)
            utility_provider: Utility provider name
            payment_method: Payment method ('HBAR' or 'USDC')
            amount_crypto: Amount paid in crypto (HBAR or USDC)
            exchange_rate: Exchange rate used
            hedera_tx_id: Hedera transaction ID
            hcs_topic_id: HCS topic ID where token issuance was logged
            hcs_sequence_number: HCS sequence number from token issuance log

        Returns:
            Dictionary containing token details

        Raises:
            PrepaidTokenError: If token creation fails

        Requirements: FR-8.1, FR-8.5, FR-8.6, FR-8.7, US-13, Task 1.4
        """
        try:
            # Calculate units from fiat amount
            units_calc = self.calculate_units_from_fiat(
                amount_fiat=amount_fiat,
                country_code=country_code,
                utility_provider=utility_provider
            )

            units_purchased = units_calc['units_kwh']
            tariff_rate = units_calc['tariff_rate']
            
            # Fetch exchange rate if not provided
            if exchange_rate is None:
                try:
                    exchange_rate = self.get_hbar_exchange_rate(currency)
                except Exception as e:
                    logger.warning(f"Failed to fetch exchange rate for {currency}: {e}")
                    # Use a default exchange rate of 1.0 if fetch fails
                    exchange_rate = 1.0

            # Generate token ID
            token_id = self.generate_token_id(country_code)
            
            # Generate STS token (20-digit electricity meter token)
            sts_generator = STSTokenGenerator(utility_provider=utility_provider, country_code=country_code)
            
            # Get meter number from database
            meter_query = text("SELECT meter_id FROM meters WHERE id = :meter_id")
            meter_result = self.db.execute(meter_query, {'meter_id': meter_id}).fetchone()
            
            if not meter_result:
                raise PrepaidTokenError(f"Meter not found: {meter_id}")
            
            meter_number = meter_result[0]  # This should be the physical meter number
            
            # Generate 20-digit STS token
            sts_token, sts_metadata = sts_generator.generate_token(
                meter_number=meter_number,
                units_kwh=units_purchased,
                amount_paid=amount_fiat,
                currency=currency
            )
            
            logger.info(f"Generated STS token: {sts_token} for meter {meter_number}")
            logger.info(f"STS metadata: {sts_metadata}")

            # Set expiry to 1 year from now
            issued_at = datetime.utcnow()
            expires_at = issued_at + timedelta(days=365)

            # Create token record with HCS information
            insert_query = text("""
                INSERT INTO prepaid_tokens (
                    id, token_id, sts_token, user_id, meter_id,
                    units_purchased, units_remaining,
                    amount_paid_hbar, amount_paid_usdc,
                    amount_paid_fiat, currency,
                    exchange_rate, tariff_rate,
                    status, hedera_tx_id,
                    hcs_topic_id, hcs_sequence_number,
                    issued_at, expires_at
                ) VALUES (
                    :id, :token_id, :sts_token, :user_id, :meter_id,
                    :units_purchased, :units_remaining,
                    :amount_paid_hbar, :amount_paid_usdc,
                    :amount_paid_fiat, :currency,
                    :exchange_rate, :tariff_rate,
                    :status, :hedera_tx_id,
                    :hcs_topic_id, :hcs_sequence_number,
                    :issued_at, :expires_at
                )
                RETURNING id, token_id, sts_token, issued_at, expires_at
            """)

            token_uuid = str(uuid.uuid4())

            params = {
                'id': token_uuid,
                'token_id': token_id,
                'sts_token': sts_token,
                'user_id': user_id,
                'meter_id': meter_id,
                'units_purchased': units_purchased,
                'units_remaining': units_purchased,
                'amount_paid_hbar': amount_crypto if payment_method == 'HBAR' else None,
                'amount_paid_usdc': amount_crypto if payment_method == 'USDC' else None,
                'amount_paid_fiat': amount_fiat,
                'currency': currency,
                'exchange_rate': exchange_rate,
                'tariff_rate': tariff_rate,
                'status': 'pending',
                'hedera_tx_id': hedera_tx_id,
                'hcs_topic_id': hcs_topic_id,
                'hcs_sequence_number': hcs_sequence_number,
                'issued_at': issued_at,
                'expires_at': expires_at
            }

            result = self.db.execute(insert_query, params).fetchone()
            self.db.commit()

            logger.info(f"✅ Created prepaid token: {token_id}")
            logger.info(f"   Units: {units_purchased} kWh")
            logger.info(f"   Amount: {amount_fiat} {currency}")
            logger.info(f"   Expires: {expires_at.date()}")
            if hcs_sequence_number:
                logger.info(f"   HCS Sequence: {hcs_sequence_number}")
            
            # Calculate crypto amount if not provided
            if amount_crypto is None and exchange_rate:
                amount_crypto = amount_fiat / exchange_rate
            
            # Prepare transaction details for payment
            # TODO: Get actual utility provider Hedera account from database
            utility_hedera_account = "0.0.UTILITY_PROVIDER"  # Placeholder
            
            transaction_details = {
                'to': utility_hedera_account,
                'amount_hbar': amount_crypto if payment_method == 'HBAR' else None,
                'amount_usdc': amount_crypto if payment_method == 'USDC' else None,
                'memo': f"Prepaid token purchase - {token_id}"
            }

            return {
                'id': str(result[0]),
                'token_id': result[1],
                'sts_token': result[2],
                'user_id': user_id,
                'meter_id': meter_id,
                'units_purchased': units_purchased,
                'units_remaining': units_purchased,
                'amount_paid_fiat': amount_fiat,
                'amount_paid_hbar': amount_crypto if payment_method == 'HBAR' else None,
                'amount_paid_usdc': amount_crypto if payment_method == 'USDC' else None,
                'currency': currency,
                'exchange_rate': exchange_rate,
                'tariff_rate': tariff_rate,
                'status': 'pending',
                'hcs_topic_id': hcs_topic_id,
                'hcs_sequence_number': hcs_sequence_number,
                'issued_at': result[3],
                'expires_at': result[4],
                'transaction': transaction_details
            }

        except PrepaidTokenError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create prepaid token: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to create token: {str(e)}")


    
    def get_user_tokens(
        self,
        user_id: str,
        status: Optional[str] = None,
        meter_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tokens for a user with optional filters.
        
        Args:
            user_id: User UUID
            status: Filter by status (active, depleted, expired, cancelled)
            meter_id: Filter by meter UUID
        
        Returns:
            List of token dictionaries
        
        Requirements: FR-8.8, US-15
        """
        try:
            # Build query with filters
            conditions = ["user_id = :user_id"]
            params = {'user_id': user_id}
            
            if status:
                conditions.append("status = :status")
                params['status'] = status
            
            if meter_id:
                conditions.append("meter_id = :meter_id")
                params['meter_id'] = meter_id
            
            where_clause = " AND ".join(conditions)
            
            query = text(f"""
                SELECT 
                    id, token_id, meter_id,
                    units_purchased, units_remaining,
                    amount_paid_hbar, amount_paid_usdc,
                    amount_paid_fiat, currency,
                    exchange_rate, tariff_rate,
                    status, hedera_tx_id,
                    issued_at, expires_at, depleted_at
                FROM prepaid_tokens
                WHERE {where_clause}
                ORDER BY issued_at DESC
            """)
            
            results = self.db.execute(query, params).fetchall()
            
            tokens = []
            for row in results:
                tokens.append({
                    'id': str(row[0]),
                    'token_id': row[1],
                    'meter_id': str(row[2]),
                    'units_purchased': float(row[3]),
                    'units_remaining': float(row[4]),
                    'units_consumed': float(row[3] - row[4]),
                    'amount_paid_hbar': float(row[5]) if row[5] else None,
                    'amount_paid_usdc': float(row[6]) if row[6] else None,
                    'amount_paid_fiat': float(row[7]),
                    'currency': row[8],
                    'exchange_rate': float(row[9]),
                    'tariff_rate': float(row[10]),
                    'status': row[11],
                    'hedera_tx_id': row[12],
                    'issued_at': row[13].isoformat() if row[13] else None,
                    'expires_at': row[14].isoformat() if row[14] else None,
                    'depleted_at': row[15].isoformat() if row[15] else None
                })
            
            return tokens
            
        except Exception as e:
            logger.error(f"Failed to get user tokens: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to get tokens: {str(e)}")
    
    def deduct_units(
        self,
        meter_id: str,
        consumption_kwh: float
    ) -> Dict[str, Any]:
        """
        Deduct units from prepaid tokens using FIFO (oldest token first).
        
        Args:
            meter_id: Meter UUID
            consumption_kwh: Consumption amount in kWh
        
        Returns:
            Dictionary containing:
                - tokens_deducted: List of tokens that were deducted from
                - total_deducted: Total units deducted
                - remaining_consumption: Consumption not covered by tokens
        
        Raises:
            PrepaidTokenError: If deduction fails
        
        Requirements: FR-8.9, FR-8.10, FR-8.11, US-16
        """
        try:
            # Get active tokens for meter (FIFO order)
            query = text("""
                SELECT id, token_id, units_remaining
                FROM prepaid_tokens
                WHERE meter_id = :meter_id
                  AND status = 'active'
                  AND units_remaining > 0
                ORDER BY issued_at ASC
                FOR UPDATE
            """)
            
            tokens = self.db.execute(query, {'meter_id': meter_id}).fetchall()
            
            if not tokens:
                logger.warning(f"No active tokens found for meter {meter_id}")
                return {
                    'tokens_deducted': [],
                    'total_deducted': 0,
                    'remaining_consumption': consumption_kwh
                }
            
            remaining_consumption = Decimal(str(consumption_kwh))
            tokens_deducted = []
            
            for token in tokens:
                if remaining_consumption <= 0:
                    break
                
                token_id = token[0]
                token_name = token[1]
                units_available = Decimal(str(token[2]))
                
                # Calculate deduction amount
                deduction = min(units_available, remaining_consumption)
                new_balance = units_available - deduction
                
                # Update token
                update_query = text("""
                    UPDATE prepaid_tokens
                    SET units_remaining = :new_balance,
                        status = CASE 
                            WHEN :new_balance <= 0 THEN 'depleted'
                            ELSE status
                        END,
                        depleted_at = CASE
                            WHEN :new_balance <= 0 THEN NOW()
                            ELSE depleted_at
                        END
                    WHERE id = :token_id
                """)
                
                self.db.execute(update_query, {
                    'token_id': token_id,
                    'new_balance': float(new_balance)
                })
                
                tokens_deducted.append({
                    'token_id': token_name,
                    'deducted': float(deduction),
                    'remaining': float(new_balance),
                    'depleted': new_balance <= 0
                })
                
                remaining_consumption -= deduction
                
                # Check for low balance alert (< 10 kWh)
                if 0 < new_balance < 10:
                    logger.warning(
                        f"⚠️ Low balance alert: Token {token_name} "
                        f"has {new_balance} kWh remaining"
                    )
            
            self.db.commit()
            
            total_deducted = consumption_kwh - float(remaining_consumption)
            
            logger.info(f"Deducted {total_deducted} kWh from {len(tokens_deducted)} token(s)")
            
            return {
                'tokens_deducted': tokens_deducted,
                'total_deducted': total_deducted,
                'remaining_consumption': float(remaining_consumption)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deduct units: {e}", exc_info=True)
            raise PrepaidTokenError(f"Failed to deduct units: {str(e)}")

    def _categorize_payment_failure(self, error: Exception) -> tuple[str, str]:
        """
        Categorize payment failure as transient or permanent.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Tuple of (failure_type, failure_reason)
            failure_type: "transient" or "permanent"
            failure_reason: Human-readable description
        """
        error_str = str(error).lower()
        
        # Permanent failures - don't retry
        permanent_indicators = [
            "insufficient balance",
            "insufficient funds",
            "invalid account",
            "account not found",
            "invalid signature",
            "unauthorized",
            "account deleted",
            "account frozen"
        ]
        
        for indicator in permanent_indicators:
            if indicator in error_str:
                return ("permanent", f"Permanent failure: {indicator}")
        
        # Transient failures - can retry
        transient_indicators = [
            "timeout",
            "network",
            "connection",
            "unavailable",
            "busy",
            "rate limit",
            "consensus",
            "temporary"
        ]
        
        for indicator in transient_indicators:
            if indicator in error_str:
                return ("transient", f"Transient failure: {indicator}")
        
        # Default to transient for unknown errors (safer to retry)
        return ("transient", f"Unknown error: {str(error)[:100]}")

    def log_token_issuance_to_hcs(
        self,
        topic_id: str,
        token_id: str,
        user_id: str,
        meter_id: str,
        units_purchased: float,
        amount_hbar: Optional[float],
        amount_usdc: Optional[float],
        amount_fiat: float,
        currency: str,
        exchange_rate: float,
        tariff_rate: float,
        tx_id: str
    ) -> Dict[str, Any]:
        """
        Log prepaid token issuance to HCS (Hedera Consensus Service).
        
        Creates an immutable blockchain record of token issuance with all
        relevant details for audit and transparency purposes.
        
        Message Format:
        {
            "type": "PREPAID_TOKEN_ISSUED",
            "token_id": "TOKEN-ES-2026-001",
            "user_id": "anonymized-uuid",
            "meter_id": "ESP-12345678",
            "units_purchased": 125.0,
            "amount_hbar": 147.0,
            "amount_usdc": null,
            "amount_fiat": 50.0,
            "currency": "EUR",
            "exchange_rate": 0.34,
            "tariff_rate": 0.40,
            "tx_id": "0.0.123456@1234567890.123",
            "timestamp": 1234567890
        }
        
        Args:
            topic_id: HCS topic ID (e.g., "0.0.5078302" for EU)
            token_id: Generated token ID (TOKEN-{COUNTRY}-{YEAR}-{SEQ})
            user_id: User UUID (will be anonymized)
            meter_id: Meter ID (e.g., "ESP-12345678")
            units_purchased: kWh units purchased
            amount_hbar: HBAR amount paid (None if USDC)
            amount_usdc: USDC amount paid (None if HBAR)
            amount_fiat: Fiat amount paid
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            exchange_rate: Exchange rate used (fiat per crypto)
            tariff_rate: Tariff rate used (fiat per kWh)
            tx_id: Hedera transaction ID
        
        Returns:
            Dictionary containing:
                - topic_id: HCS topic ID
                - sequence_number: HCS sequence number (None if logging failed)
                - message: The logged message (None if logging failed)
                - error: Error message (only present if logging failed)
                - status: "failed" (only present if logging failed)
        
        Note:
            This method does NOT raise exceptions on HCS failures. Instead, it returns
            a result dictionary with status="failed" to allow token creation to proceed
            even if audit logging fails. The payment has already been processed, so we
            don't want to lose the token due to HCS issues.
        
        Requirements: FR-8.7, US-13, Task 1.4
        """
        try:
            from hedera import TopicMessageSubmitTransaction, TopicId
            import json
            from datetime import datetime
            import hashlib
            
            logger.info(f"Logging token issuance to HCS topic {topic_id}...")
            
            # Anonymize user ID for privacy (hash with salt)
            user_id_hash = hashlib.sha256(f"{user_id}:prepaid_token".encode()).hexdigest()[:16]
            anonymized_user_id = f"user-{user_id_hash}"
            
            # Create token issuance log message per specification
            token_log = {
                "type": "PREPAID_TOKEN_ISSUED",
                "token_id": token_id,
                "user_id": anonymized_user_id,
                "meter_id": meter_id,
                "units_purchased": units_purchased,
                "amount_hbar": amount_hbar,
                "amount_usdc": amount_usdc,
                "amount_fiat": amount_fiat,
                "currency": currency,
                "exchange_rate": exchange_rate,
                "tariff_rate": tariff_rate,
                "tx_id": tx_id,
                "timestamp": int(datetime.utcnow().timestamp())
            }
            
            # Convert to JSON
            message_json = json.dumps(token_log)
            
            # Parse topic ID
            topic = TopicId.fromString(topic_id)
            
            # Create and execute HCS message submission
            transaction = (
                TopicMessageSubmitTransaction()
                .setTopicId(topic)
                .setMessage(message_json)
            )
            
            response = transaction.execute(self.hedera_service.client)
            receipt = response.getReceipt(self.hedera_service.client)
            
            sequence_number = receipt.topicSequenceNumber
            
            logger.info(f"✅ Token issuance logged to HCS topic {topic_id}")
            logger.info(f"   Sequence Number: {sequence_number}")
            logger.info(f"   Token ID: {token_id}")
            logger.info(f"   Units: {units_purchased} kWh")
            logger.info(f"   Amount: {amount_fiat} {currency}")
            
            return {
                "topic_id": topic_id,
                "sequence_number": sequence_number,
                "message": token_log
            }
            
        except Exception as e:
            logger.error(f"Failed to log token issuance to HCS: {e}", exc_info=True)
            logger.warning(
                f"⚠️ HCS logging failed for token {token_id}, but token creation will proceed. "
                f"Manual audit log entry may be required."
            )
            
            # Return partial result indicating failure
            # This allows token creation to proceed even if HCS logging fails
            return {
                "topic_id": topic_id,
                "sequence_number": None,
                "message": None,
                "error": str(e),
                "status": "failed"
            }

    def process_hbar_payment(
        self,
        user_account_id: str,
        treasury_account_id: str,
        amount_fiat: float,
        currency: str,
        meter_id: str,
        token_id: str,
        use_cache: bool = True,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Process HBAR payment for prepaid token purchase with retry logic.

        This method handles the complete HBAR payment flow:
        1. Fetch current HBAR exchange rate
        2. Calculate HBAR amount needed
        3. Submit HBAR transfer transaction to Hedera testnet
        4. Wait for consensus (max 5 seconds)
        5. Retry on transient failures with exponential backoff
        6. Return transaction details for database storage

        Args:
            user_account_id: User's Hedera account ID (0.0.xxxxx)
            treasury_account_id: Treasury/operator account ID (0.0.xxxxx)
            amount_fiat: Amount in fiat currency
            currency: Currency code (EUR, USD, INR, BRL, NGN)
            meter_id: Meter UUID (for memo)
            token_id: Token ID (for memo)
            use_cache: Whether to use cached exchange rate
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Dictionary containing:
                - amount_hbar: HBAR amount transferred
                - exchange_rate: Exchange rate used
                - tx_id: Hedera transaction ID
                - consensus_timestamp: Consensus timestamp
                - status: Transaction status
                - retry_count: Number of retries performed
                - failure_type: Type of failure if any (transient/permanent)
                - failure_reason: Reason for failure if any

        Raises:
            PrepaidTokenError: If payment processing fails after all retries

        Requirements: FR-8.1, US-13, Task 1.3
        """
        retry_count = 0
        last_error = None
        failure_type = None
        failure_reason = None
        
        while retry_count <= max_retries:
            try:
                from hedera import (
                    TransferTransaction,
                    Hbar,
                    AccountId
                )

                if retry_count > 0:
                    # Exponential backoff: 1s, 2s, 4s
                    backoff_time = 2 ** (retry_count - 1)
                    logger.info(f"Retry attempt {retry_count}/{max_retries} after {backoff_time}s backoff")
                    time.sleep(backoff_time)

                logger.info(f"Processing HBAR payment: {amount_fiat} {currency} (attempt {retry_count + 1}/{max_retries + 1})")

                # Step 1: Fetch HBAR exchange rate
                exchange_rate = self.get_hbar_exchange_rate(currency, use_cache)
                logger.info(f"Exchange rate: 1 HBAR = {exchange_rate} {currency}")

                # Step 2: Calculate HBAR amount needed
                hbar_calc = self.calculate_hbar_amount(amount_fiat, currency, use_cache)
                amount_hbar = hbar_calc['amount_hbar']
                logger.info(f"HBAR amount needed: {amount_hbar} HBAR")

                # Step 3: Create and submit HBAR transfer transaction
                logger.info(f"Submitting HBAR transfer from {user_account_id} to {treasury_account_id}")

                # Parse account IDs
                from_account = AccountId.fromString(user_account_id)
                to_account = AccountId.fromString(treasury_account_id)

                # Create transfer transaction with memo
                memo = f"Prepaid token: {token_id}"
                transaction = (
                    TransferTransaction()
                    .addHbarTransfer(from_account, Hbar(-amount_hbar))  # Debit from user
                    .addHbarTransfer(to_account, Hbar(amount_hbar))     # Credit to treasury
                    .setTransactionMemo(memo)
                    .setMaxTransactionFee(Hbar(2))  # Max fee for transfer
                )

                # Execute transaction
                start_time = time.time()
                response = transaction.execute(self.hedera_service.client)

                # Step 4: Wait for consensus (with timeout)
                logger.info("Waiting for consensus...")
                receipt = response.getReceipt(self.hedera_service.client)
                consensus_time = time.time() - start_time

                if consensus_time > 5:
                    logger.warning(f"Consensus took {consensus_time:.2f}s (> 5s threshold)")
                else:
                    logger.info(f"✅ Consensus reached in {consensus_time:.2f}s")

                # Get transaction ID and consensus timestamp
                tx_id = str(response.transactionId)
                consensus_timestamp = receipt.consensusTimestamp

                logger.info(f"✅ HBAR payment successful")
                logger.info(f"   Transaction ID: {tx_id}")
                logger.info(f"   Amount: {amount_hbar} HBAR ({amount_fiat} {currency})")
                logger.info(f"   Exchange rate: {exchange_rate} {currency}/HBAR")
                logger.info(f"   Retries: {retry_count}")

                # Step 5: Return transaction details
                return {
                    'amount_hbar': amount_hbar,
                    'exchange_rate': exchange_rate,
                    'tx_id': tx_id,
                    'consensus_timestamp': str(consensus_timestamp),
                    'status': 'SUCCESS',
                    'consensus_time_seconds': consensus_time,
                    'retry_count': retry_count,
                    'failure_type': None,
                    'failure_reason': None
                }

            except Exception as e:
                last_error = e
                failure_type, failure_reason = self._categorize_payment_failure(e)
                
                logger.error(f"Payment attempt {retry_count + 1} failed: {failure_reason}")
                logger.error(f"Error details: {str(e)}", exc_info=True)
                
                # If permanent failure, don't retry
                if failure_type == "permanent":
                    logger.error(f"Permanent failure detected, aborting retries")
                    break
                
                # If transient failure and retries remaining, continue
                if retry_count < max_retries:
                    retry_count += 1
                    continue
                else:
                    logger.error(f"Max retries ({max_retries}) reached, giving up")
                    break
        
        # All retries exhausted or permanent failure
        error_message = f"HBAR payment failed after {retry_count} retries: {failure_reason}"
        logger.error(error_message)
        
        # Store failure details for debugging
        failure_details = {
            'failure_type': failure_type,
            'failure_reason': failure_reason,
            'retry_count': retry_count,
            'max_retries': max_retries,
            'last_error': str(last_error),
            'user_account_id': user_account_id,
            'treasury_account_id': treasury_account_id,
            'amount_fiat': amount_fiat,
            'currency': currency,
            'token_id': token_id
        }
        
        raise PrepaidTokenError(
            f"{error_message}\nDetails: {failure_details}"
        )

    def get_topic_for_country(self, country_code: str) -> Optional[str]:
        """
        Get HCS topic ID based on country code.

        Maps country codes to regional HCS topics for logging prepaid token
        issuance and consumption events. This enables regional audit trails
        and compliance with data sovereignty requirements.

        Regional Topic Mapping:
        - EU: Spain (ES) → HCS_TOPIC_EU
        - US: United States (US) → HCS_TOPIC_US
        - Asia: India (IN) → HCS_TOPIC_ASIA
        - South America: Brazil (BR) → HCS_TOPIC_SA
        - Africa: Nigeria (NG) → HCS_TOPIC_AFRICA

        Args:
            country_code: ISO 3166-1 alpha-2 country code (ES, US, IN, BR, NG)

        Returns:
            HCS topic ID string (e.g., "0.0.5078302") or None if not configured

        Raises:
            PrepaidTokenError: If country code is not supported

        Requirements: FR-8.7 (HCS logging), Task 1.4
        """
        from config import settings

        # Country to region mapping
        country_to_region = {
            'ES': settings.hcs_topic_eu,      # Spain → EU
            'US': settings.hcs_topic_us,      # USA → US
            'IN': settings.hcs_topic_asia,    # India → Asia
            'BR': settings.hcs_topic_sa,      # Brazil → South America
            'NG': settings.hcs_topic_africa   # Nigeria → Africa
        }

        # Validate country code
        if country_code not in country_to_region:
            raise PrepaidTokenError(
                f"Unsupported country code: {country_code}. "
                f"Supported countries: {', '.join(country_to_region.keys())}"
            )

        topic_id = country_to_region[country_code]

        # Log warning if topic not configured
        if not topic_id or topic_id == "0.0.xxxxx":
            logger.warning(
                f"HCS topic not configured for country {country_code}. "
                f"Token issuance will proceed without HCS logging."
            )
            return None

        logger.info(f"Selected HCS topic {topic_id} for country {country_code}")
        return topic_id


