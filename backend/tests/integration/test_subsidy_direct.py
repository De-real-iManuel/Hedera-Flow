#!/usr/bin/env python3
"""
Direct test of subsidy calculation logic
"""

def _calculate_subsidies(
    base_charge: float,
    subsidies,  # Can be list or dict
    consumption_kwh: float = 0,
    user_eligible: bool = True
) -> float:
    """Calculate total subsidies"""
    # If user not eligible or no subsidies configured, return 0
    if not user_eligible or not subsidies:
        return 0.0
    
    # Handle both list and dict formats
    if isinstance(subsidies, list):
        subsidy_list = subsidies
    elif isinstance(subsidies, dict):
        subsidy_list = subsidies.get('items', [])
    else:
        subsidy_list = []
    
    if not subsidy_list:
        return 0.0
    
    total_subsidy = 0.0
    
    for subsidy in subsidy_list:
        subsidy_type = subsidy.get('type', '').lower()
        subsidy_value = subsidy.get('value', 0)
        
        # Skip if no value
        if not subsidy_value:
            continue
        
        # Calculate based on subsidy type
        if subsidy_type == 'percentage':
            total_subsidy += base_charge * subsidy_value
        elif subsidy_type == 'fixed':
            total_subsidy += subsidy_value
        elif subsidy_type == 'per_kwh':
            if consumption_kwh > 0:
                total_subsidy += consumption_kwh * subsidy_value
    
    # Ensure subsidy doesn't exceed base charge
    return min(total_subsidy, base_charge)


# Test 1: Percentage subsidy
subsidies1 = [{'type': 'percentage', 'value': 0.25}]
result1 = _calculate_subsidies(100.0, subsidies1)
print(f"Test 1 - Percentage (25%): {result1} (expected: 25.0)")

# Test 2: Fixed subsidy
subsidies2 = [{'type': 'fixed', 'value': 10.0}]
result2 = _calculate_subsidies(100.0, subsidies2)
print(f"Test 2 - Fixed (€10): {result2} (expected: 10.0)")

# Test 3: Per kWh subsidy
subsidies3 = [{'type': 'per_kwh', 'value': 0.05}]
result3 = _calculate_subsidies(100.0, subsidies3, consumption_kwh=200)
print(f"Test 3 - Per kWh (€0.05 × 200): {result3} (expected: 10.0)")

# Test 4: Multiple subsidies
subsidies4 = [
    {'type': 'percentage', 'value': 0.15},
    {'type': 'fixed', 'value': 5.0}
]
result4 = _calculate_subsidies(60.0, subsidies4)
print(f"Test 4 - Multiple (15% + €5): {result4} (expected: 14.0)")

# Test 5: Empty dict
subsidies5 = {}
result5 = _calculate_subsidies(100.0, subsidies5)
print(f"Test 5 - Empty dict: {result5} (expected: 0.0)")
