# Prepaid Token Service Tests

This directory contains comprehensive unit tests for the `PrepaidTokenService` class, organized by method for better maintainability.

## Test Structure

The tests are split into separate files based on the methods they test:

### 1. `test_calculate_units.py` (9 tests)
Tests for the `calculate_units_from_fiat()` method:
- Flat rate calculation
- Tiered rate calculation
- Time-of-use calculation
- Zero amount handling
- Error handling (tariff not found, invalid rate, missing tiers, unknown type)
- Decimal precision handling

### 2. `test_generate_token_id.py` (8 tests)
Tests for the `generate_token_id()` method:
- Token ID format validation (TOKEN-{COUNTRY}-{YEAR}-{SEQ})
- Sequence number increment
- Default year handling
- Different country codes
- Sequence padding (001, 010, 100, etc.)
- Query pattern verification
- Database error handling
- Empty result handling

### 3. `test_create_token.py` (11 tests)
Tests for the `create_token()` method:
- HBAR payment success
- USDC payment success
- Token expiry (1 year from issuance)
- Optional Hedera transaction ID
- Database error handling
- Calculation error propagation
- Token ID generation error propagation
- Initial units_remaining equals units_purchased
- Status is 'active' on creation
- Multiple currencies support

### 4. `test_deduct_units.py` (15 tests)
Tests for the `deduct_units()` method (FIFO logic):
- Partial deduction from single token
- Full depletion of single token
- FIFO deduction from multiple tokens (oldest first)
- Insufficient balance handling
- No active tokens scenario
- Low balance alert (< 10 kWh)
- No alert when balance >= 10 kWh
- No alert when fully depleted
- Zero consumption handling
- Decimal precision
- Database error rollback
- FOR UPDATE lock verification
- Active token filtering
- FIFO ordering (issued_at ASC)
- depleted_at timestamp update
- Deduction from all available tokens

### 5. `test_get_user_tokens.py` (13 tests)
Tests for the `get_user_tokens()` method:
- Retrieve all user tokens
- Filter by status (active, depleted, expired, cancelled)
- Filter by meter_id
- Combined filters (status + meter_id)
- Empty result handling
- Ordering by issued_at DESC (newest first)
- units_consumed calculation
- All fields included in response
- Datetime serialization to ISO format
- Database error handling
- Different statuses
- Multiple meters
- Numeric precision

## Total Test Coverage

- **Total Tests**: 56
- **All tests passing**: ✅

## Running the Tests

### Run all prepaid token tests:
```bash
pytest backend/tests/prepaid_token/
```

### Run specific test file:
```bash
pytest backend/tests/prepaid_token/test_calculate_units.py
pytest backend/tests/prepaid_token/test_generate_token_id.py
pytest backend/tests/prepaid_token/test_create_token.py
pytest backend/tests/prepaid_token/test_deduct_units.py
pytest backend/tests/prepaid_token/test_get_user_tokens.py
```

### Run specific test class:
```bash
pytest backend/tests/prepaid_token/test_deduct_units.py::TestDeductUnits
```

### Run specific test:
```bash
pytest backend/tests/prepaid_token/test_deduct_units.py::TestDeductUnits::test_deduct_from_multiple_tokens_fifo
```

### Run with verbose output:
```bash
pytest backend/tests/prepaid_token/ -v
```

### Run with coverage:
```bash
pytest backend/tests/prepaid_token/ --cov=app.services.prepaid_token_service --cov-report=html
```

## Acceptance Criteria Coverage

All acceptance criteria from the spec are covered:

✅ Token ID generation follows format (TOKEN-{COUNTRY}-{YEAR}-{SEQ})  
✅ Units calculated correctly based on tariff  
✅ FIFO deduction works (oldest token first)  
✅ Low balance alert triggered at < 10 kWh  
✅ Status changes to "depleted" when units reach 0  
✅ All methods have comprehensive unit test coverage  
✅ Edge cases and error handling tested

## Migration from Original File

The original `test_prepaid_token_service.py` file (1847 lines) has been split into 5 focused files for better organization and maintainability. You can safely delete the original file after verifying all tests pass.
