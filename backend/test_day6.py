#!/usr/bin/env python
"""
Test script for Day 6 Fraud Alert Voice Agent.
This script simulates different fraud alert scenarios and verifies database updates.
"""

import json
from pathlib import Path

# Path to fraud cases database
FRAUD_CASES_FILE = Path(__file__).parent / "fraud_cases.json"


def load_fraud_cases():
    """Load fraud cases from database."""
    with open(FRAUD_CASES_FILE, "r") as f:
        return json.load(f)


def save_fraud_cases(cases):
    """Save fraud cases to database."""
    with open(FRAUD_CASES_FILE, "w") as f:
        json.dump(cases, f, indent=2)


def reset_all_cases_to_pending():
    """Reset all fraud cases to pending_review status for testing."""
    cases = load_fraud_cases()
    for case in cases:
        case["status"] = "pending_review"
        case["outcomeNote"] = ""
    save_fraud_cases(cases)
    print("✓ All fraud cases reset to pending_review status")


def display_fraud_cases():
    """Display all fraud cases with their current status."""
    cases = load_fraud_cases()
    
    print("\n" + "="*80)
    print("FRAUD CASES DATABASE")
    print("="*80)
    
    for i, case in enumerate(cases, 1):
        print(f"\n{i}. {case['userName']} (ID: {case['id']})")
        print(f"   Security ID: {case['securityIdentifier']}")
        print(f"   Card: ****{case['cardEnding']}")
        print(f"   Transaction: ${case['transactionAmount']} at {case['transactionName']}")
        print(f"   Location: {case['transactionLocation']}")
        print(f"   Status: {case['status']}")
        if case['outcomeNote']:
            print(f"   Outcome: {case['outcomeNote']}")
    
    print("\n" + "="*80)


def test_scenario_safe_transaction():
    """Test Scenario 1: Customer confirms legitimate transaction."""
    print("\n" + "="*80)
    print("TEST SCENARIO 1: LEGITIMATE TRANSACTION")
    print("="*80)
    print("\nScenario:")
    print("  - Customer: John Smith")
    print("  - Security ID: 12345")
    print("  - Transaction: $2,499.99 at Global Electronics Ltd")
    print("  - Customer Response: YES (they made the transaction)")
    print("\nExpected Outcome:")
    print("  - Status: confirmed_safe")
    print("  - Outcome Note: Customer confirmed transaction as legitimate")
    print("\nTo test:")
    print("  1. Run: uv run python src/day6_agent.py console")
    print("  2. Say: 'John Smith'")
    print("  3. Say: '12345'")
    print("  4. Say: 'Yes, I made that purchase'")
    print("\nAfter the call, check the database to verify the status was updated.")


def test_scenario_fraudulent_transaction():
    """Test Scenario 2: Customer denies fraudulent transaction."""
    print("\n" + "="*80)
    print("TEST SCENARIO 2: FRAUDULENT TRANSACTION")
    print("="*80)
    print("\nScenario:")
    print("  - Customer: Sarah Johnson")
    print("  - Security ID: 67890")
    print("  - Transaction: $15,000.00 at Luxury Watches International")
    print("  - Customer Response: NO (they did NOT make the transaction)")
    print("\nExpected Outcome:")
    print("  - Status: confirmed_fraud")
    print("  - Outcome Note: Customer denied transaction. Card blocked and dispute initiated")
    print("\nTo test:")
    print("  1. Run: uv run python src/day6_agent.py console")
    print("  2. Say: 'Sarah Johnson'")
    print("  3. Say: '67890'")
    print("  4. Say: 'No, I did not make that purchase'")
    print("\nAfter the call, check the database to verify the status was updated.")


def test_scenario_verification_failed():
    """Test Scenario 3: Failed customer verification."""
    print("\n" + "="*80)
    print("TEST SCENARIO 3: VERIFICATION FAILURE")
    print("="*80)
    print("\nScenario:")
    print("  - Customer: Michael Chen")
    print("  - Security ID provided: 99999 (WRONG, correct is 54321)")
    print("  - Transaction: $899.50 at TechGadgets Pro")
    print("\nExpected Outcome:")
    print("  - Verification fails")
    print("  - Call ends gracefully")
    print("  - Status: verification_failed")
    print("\nTo test:")
    print("  1. Run: uv run python src/day6_agent.py console")
    print("  2. Say: 'Michael Chen'")
    print("  3. Say: '99999' (incorrect security ID)")
    print("  4. Agent should refuse to proceed")
    print("\nAfter the call, check the database to verify the status was updated.")


def show_menu():
    """Display the test menu."""
    print("\n" + "="*80)
    print("DAY 6 FRAUD ALERT VOICE AGENT - TEST SUITE")
    print("="*80)
    print("\nOptions:")
    print("  1. Display all fraud cases")
    print("  2. Reset all cases to pending_review")
    print("  3. Show Test Scenario 1: Legitimate Transaction")
    print("  4. Show Test Scenario 2: Fraudulent Transaction")
    print("  5. Show Test Scenario 3: Verification Failure")
    print("  6. Exit")
    print("\nEnter your choice (1-6): ", end="")


def main():
    """Main test menu."""
    while True:
        show_menu()
        choice = input().strip()
        
        if choice == "1":
            display_fraud_cases()
        elif choice == "2":
            reset_all_cases_to_pending()
        elif choice == "3":
            test_scenario_safe_transaction()
        elif choice == "4":
            test_scenario_fraudulent_transaction()
        elif choice == "5":
            test_scenario_verification_failed()
        elif choice == "6":
            print("\nExiting test suite. Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 6.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
