# Day 6 Fraud Alert - Quick Test Reference

## 🚀 Quick Start
```bash
cd backend
uv run python src/day6_agent.py console
```

## 🧪 Test Cheat Sheet

### Test 1: Safe Transaction ✅
**Say this:**
1. "John Smith"
2. "12345"
3. "Yes, I made that purchase"

**Expected:** Status → `confirmed_safe`

---

### Test 2: Fraudulent Transaction 🚨
**Say this:**
1. "Sarah Johnson"
2. "67890"
3. "No, I did not make that purchase"

**Expected:** Status → `confirmed_fraud`, card blocked

---

### Test 3: Failed Verification ❌
**Say this:**
1. "Michael Chen"
2. "99999" (wrong ID, correct is 54321)

**Expected:** Verification fails, call ends

---

## 📊 Check Results
```bash
uv run python verify_day6.py
```

## 🔄 Reset Database
Open `fraud_cases.json` and change all `status` fields to `"pending_review"`

## 🎯 All Test Cases

| Name | Security ID | Card | Amount | Merchant |
|------|-------------|------|--------|----------|
| John Smith | 12345 | 4242 | $2,499.99 | Global Electronics Ltd |
| Sarah Johnson | 67890 | 8888 | $15,000.00 | Luxury Watches International |
| Michael Chen | 54321 | 1234 | $899.50 | TechGadgets Pro |
| Emily Rodriguez | 99999 | 5678 | $3,750.00 | International Travel Services |
| David Thompson | 11111 | 9999 | $549.99 | Fashion Boutique Online |
