# Meter ID Formats by Country

## Spain (ES)
- **Format**: ES + 8-10 digits
- **Example**: `ES12345678`, `ES1234567890`
- **Validation**: Must start with "ES" followed by 8-10 digits

## United States (US)
- **Format**: 10-15 alphanumeric characters
- **Example**: `MTR1234567890`, `ABC123XYZ456`
- **Validation**: 10-15 characters, letters and numbers

## India (IN)
- **Format**: 10-12 digits
- **Example**: `1234567890`, `123456789012`
- **Validation**: 10-12 digits only

## Brazil (BR)
- **Format**: 10-14 digits
- **Example**: `12345678901234`
- **Validation**: 10-14 digits only

## Nigeria (NG)
- **Format**: 11-13 digits
- **Example**: `12345678901`, `1234567890123`
- **Validation**: 11-13 digits only
- **Additional**: Requires band classification (A, B, C, D, or E)

## Quick Test Examples

### Spain User
```json
{
  "meter_id": "ES12345678",
  "utility_provider_id": "<provider-uuid>",
  "state_province": "Madrid",
  "utility_provider": "Iberdrola",
  "meter_type": "postpaid",
  "is_primary": true
}
```

### Nigeria User
```json
{
  "meter_id": "12345678901",
  "utility_provider_id": "<provider-uuid>",
  "state_province": "Lagos",
  "utility_provider": "Eko Electricity",
  "meter_type": "prepaid",
  "band_classification": "B",
  "is_primary": true
}
```
