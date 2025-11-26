#!/usr/bin/env python
"""Quick verification script for Day 6 Fraud Alert Agent."""

import json
from pathlib import Path

FRAUD_CASES_FILE = Path(__file__).parent / "fraud_cases.json"

def main():
    print("\n" + "="*80)
    print("DAY 6 FRAUD ALERT VOICE AGENT - DATABASE STATUS")
    print("="*80)
    
    with open(FRAUD_CASES_FILE, "r") as f:
        cases = json.load(f)
    
    print(f"\nTotal Fraud Cases: {len(cases)}")
    print("\nAvailable Test Cases:\n")
    
    for i, case in enumerate(cases, 1):
        status_emoji = {
            "pending_review": "⏳",
            "confirmed_safe": "✅",
            "confirmed_fraud": "🚨",
            "verification_failed": "❌"
        }.get(case['status'], "❓")
        
        print(f"{i}. {status_emoji} {case['userName']}")
        print(f"   Security ID: {case['securityIdentifier']}")
        print(f"   Card: ****{case['cardEnding']}")
        print(f"   Amount: ${case['transactionAmount']:,.2f} at {case['transactionName']}")
        print(f"   Location: {case['transactionLocation']}")
        print(f"   Status: {case['status']}")
        if case.get('outcomeNote'):
            print(f"   Note: {case['outcomeNote']}")
        print()
    
    print("="*80)
    print("\nTO RUN THE AGENT:")
    print("  Console Mode: uv run python src/day6_agent.py console")
    print("  Dev Mode:     uv run python src/day6_agent.py dev")
    print("\nFor detailed testing instructions, see: DAY6_FRAUD_ALERT.md")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
