# Hedera-Flow Test Suite

This directory contains comprehensive tests for the Hedera-Flow backend application, organized by test type and scope.

## Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for service interactions
├── e2e/           # End-to-end workflow tests
├── manual/        # Manual testing scripts and debug tools
├── pytest.ini    # Pytest configuration
├── run_tests.py   # Test runner script
└── README.md      # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
Tests for individual functions, classes, and components in isolation:
- `test_auth_utils.py` - Authentication utility functions
- `test_config.py` - Configuration management
- `test_password_hashing.py` - Password security functions
- `test_fraud_detection.py` - Fraud detection algorithms
- `test_ocr_service.py` - OCR processing logic
- `test_cors.py` - CORS configuration
- `test_error_handling.py` - Error handling utilities

### Integration Tests (`tests/integration/`)
Tests for service integrations and API endpoints:
- `test_hedera_integration.py` - Hedera SDK integration
- `test_wallet_connect.py` - HashPack wallet integration
- `test_database_pool.py` - Database connection pooling
- `test_google_vision.py` - Google Vision API integration
- `test_coingecko_integration.py` - Exchange rate API integration
- `test_auth_token.py` - JWT token management
- `test_meters_endpoint.py` - Meter management APIs

### End-to-End Tests (`tests/e2e/`)
Tests for complete user workflows:
- `test_complete_payment_flow.py` - Full payment process
- `test_auth_e2e.py` - Complete authentication flow
- `test_prepaid_flow.py` - Prepaid token purchase and consumption
- `test_verify_endpoint.py` - Meter reading verification workflow

### Manual Tests (`tests/manual/`)
Scripts for manual testing and debugging:
- `test_with_real_image.py` - Test OCR with actual meter images
- `test_exchange_rate_manual.py` - Manual exchange rate testing
- `test_login_debug.py` - Authentication debugging tools

## Running Tests

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# End-to-end tests only
python -m pytest tests/e2e/ -v
```

### Run Specific Test Files
```bash
# Test specific functionality
python -m pytest tests/unit/test_fraud_detection.py -v
python -m pytest tests/integration/test_hedera_integration.py -v
python -m pytest tests/e2e/test_complete_payment_flow.py -v
```

### Run Tests with Coverage
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

## Test Configuration

### Environment Setup
Tests use separate configuration and database:
- Test database: `test_hedera_flow.db` (SQLite for speed)
- Test environment variables in `.env.test`
- Mock services for external APIs during testing

### Required Environment Variables
```bash
# Test configuration
ENVIRONMENT=test
DATABASE_URL=sqlite:///test_hedera_flow.db
HEDERA_MOCK_MODE=true
GOOGLE_APPLICATION_CREDENTIALS=./credentials/test-google-vision-key.json
```

### Test Dependencies
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov
```

## Test Data and Fixtures

### Test Images
- `tests/fixtures/meter_images/` - Sample meter reading images
- `tests/fixtures/tampered_images/` - Images for fraud detection testing

### Test Data
- `tests/fixtures/test_data.json` - Sample API responses
- `tests/fixtures/mock_responses/` - Mock external API responses

## Continuous Integration

Tests are automatically run on:
- Pull requests to main branch
- Commits to main branch
- Nightly builds

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/ -v --cov=app
```

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality>_<expected_outcome>`
- Test classes: `Test<ClassName>`

### Example Test Structure
```python
import pytest
from app.services.example_service import ExampleService

class TestExampleService:
    """Test suite for ExampleService"""
    
    @pytest.fixture
    def service(self):
        """Create service instance for testing"""
        return ExampleService()
    
    def test_example_function_success(self, service):
        """Test successful execution of example function"""
        result = service.example_function("valid_input")
        assert result.success is True
        assert result.data is not None
    
    def test_example_function_invalid_input(self, service):
        """Test error handling with invalid input"""
        with pytest.raises(ValueError):
            service.example_function("invalid_input")
```

### Best Practices
1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external services and APIs
3. **Assertions**: Use clear, specific assertions
4. **Documentation**: Document test purpose and expected behavior
5. **Coverage**: Aim for >90% code coverage
6. **Performance**: Keep tests fast (<1 second per test)

## Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Reset test database
rm test_hedera_flow.db
python -m pytest tests/integration/test_database_pool.py -v
```

**Mock Service Failures**
```bash
# Enable mock mode
export HEDERA_MOCK_MODE=true
python -m pytest tests/integration/test_hedera_integration.py -v
```

**Import Errors**
```bash
# Add backend to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m pytest tests/ -v
```

### Debug Mode
```bash
# Run tests with debug output
python -m pytest tests/ -v -s --tb=long
```

## Test Metrics

Current test coverage and metrics:
- **Total Tests**: 65+ test files
- **Unit Tests**: 15 files
- **Integration Tests**: 25 files  
- **E2E Tests**: 8 files
- **Manual Tests**: 7 files
- **Code Coverage**: Target >90%
- **Test Execution Time**: <5 minutes for full suite

## Contributing

When adding new features:
1. Write unit tests for new functions/classes
2. Add integration tests for new API endpoints
3. Create e2e tests for new user workflows
4. Update this README if adding new test categories
5. Ensure all tests pass before submitting PR

For questions about testing, see the main project documentation or contact the development team.