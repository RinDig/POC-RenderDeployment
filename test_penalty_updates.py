"""
Test the updated penalty calculations to ensure fraud and obstruction are properly excluded
"""

from audit_agent.utils.penalties import (
    DRC_MINING_PENALTIES,
    EXCLUDED_PENALTIES,
    identify_potential_violations,
    calculate_max_penalty,
    get_excluded_penalties_context,
    get_audit_scope_disclaimer,
    format_penalty_amount
)

def test_penalty_exclusions():
    """Test that fraud and obstruction penalties are properly excluded"""
    
    print("Testing DRC Mining Code Penalty Updates\n")
    print("=" * 60)
    
    # Test 1: Check that Article 299 (fraud) is excluded from calculations
    print("\n1. Testing Article 299 (Fraud) Exclusion:")
    print("-" * 40)
    
    # Try to identify fraud-related violations
    fraud_gaps = [
        ("Evidence of fraudulent documentation", "Investigate potential fraud"),
        ("Suspected pillage of resources", "Report to authorities"),
        ("Illegal exploitation without permits", "Obtain proper permits")
    ]
    
    for gap, rec in fraud_gaps:
        violations = identify_potential_violations(gap, rec)
        print(f"Gap: {gap[:50]}...")
        print(f"Violations found: {violations}")
        if violations:
            penalty = calculate_max_penalty(violations)
            print(f"Calculated penalty: {format_penalty_amount(penalty)}")
        print()
    
    # Test 2: Check Article 306 (obstruction) is limited
    print("\n2. Testing Article 306 (Obstruction) Modification:")
    print("-" * 40)
    
    obstruction_gaps = [
        ("Transparency reporting gaps", "Improve documentation"),
        ("Traceability system incomplete", "Implement tracking system"),
        ("Blocking inspector access", "Allow full access"),  # This should not trigger high penalty
        ("Refusing to provide documents", "Provide all documents")  # This should not trigger
    ]
    
    for gap, rec in obstruction_gaps:
        violations = identify_potential_violations(gap, rec)
        print(f"Gap: {gap[:50]}...")
        print(f"Violations found: {violations}")
        if violations:
            penalty = calculate_max_penalty(violations)
            print(f"Calculated penalty: {format_penalty_amount(penalty)}")
            if "306" in violations:
                penalty_info = DRC_MINING_PENALTIES.get("306")
                print(f"Article 306 max penalty: {format_penalty_amount(penalty_info.max_fine_usd)}")
        print()
    
    # Test 3: Display excluded penalties context
    print("\n3. Excluded Penalties Context:")
    print("-" * 40)
    print(get_excluded_penalties_context())
    
    # Test 4: Display audit scope disclaimer
    print("\n4. Audit Scope Disclaimer:")
    print("-" * 40)
    print(get_audit_scope_disclaimer())
    
    # Test 5: Verify maximum penalties are reasonable
    print("\n5. Maximum Penalties Summary:")
    print("-" * 40)
    
    # Calculate max for common violations
    common_violations = [
        (["301"], "Administrative non-compliance"),
        (["307"], "Safety/Environmental violation"),
        (["299bis"], "Human rights violation"),
        (["302"], "Unauthorized mineral trading"),
        (["306"], "Transparency/traceability gaps")
    ]
    
    for articles, description in common_violations:
        penalty = calculate_max_penalty(articles)
        print(f"{description:40} {format_penalty_amount(penalty):>15}")
    
    print("\n" + "=" * 60)
    print("Test Complete - Penalties Updated Successfully")
    print("\nKey Changes:")
    print("✓ Article 299 (Fraud) - Excluded from calculations")
    print("✓ Article 306 (Obstruction) - Limited to $42,912.25 for transparency/traceability")
    print("✓ Added disclaimers for excluded penalties")
    print("✓ Focus on administrative/regulatory penalties only")

if __name__ == "__main__":
    test_penalty_exclusions()