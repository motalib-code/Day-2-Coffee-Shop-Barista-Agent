# Day 6: Fraud Alert Voice Agent

## Overview
A fraud detection voice agent that calls customers to verify suspicious transactions. The agent provides a professional, secure experience while investigating potential fraud cases.

## Features

### Core Functionality
- **Professional Fraud Representative Persona**: Introduces itself as SecureBank's fraud department
- **Customer Verification**: Uses non-sensitive security identifiers to verify customer identity
- **Transaction Review**: Reads out suspicious transaction details
- **Interactive Decision Making**: Asks customers to confirm or deny transactions
- **Database Persistence**: Updates fraud case status in real-time

### Security Best Practices
✅ **Safe:**
- Uses security identifier for verification
- Asks basic security questions
- Reads masked card numbers (e.g., ending in 4242)

❌ **Never Requests:**
- Full card numbers
- PINs or passwords
- CVV codes
- Social Security Numbers

## Database Structure

The fraud cases are stored in `fraud_cases.json` with the following schema:

```json
{
  "id": 1,
  "userName": "John Smith",
  "securityIdentifier": "12345",
  "cardEnding": "4242",
  "status": "pending_review",
  "transactionAmount": 2499.99,
  "transactionCurrency": "USD",
  "transactionName": "Global Electronics Ltd",
  "transactionTime": "2025-11-26T14:23:45Z",
  "transactionCategory": "e-commerce",
  "transactionSource": "globalelectronics.alibaba.com",
  "transactionLocation": "Shenzhen, China",
  "securityQuestion": "What is your favorite color?",
  "securityAnswer": "blue",
  "outcomeNote": ""
}
```

### Status Values
- `pending_review`: Initial state, awaiting investigation
- `confirmed_safe`: Customer confirmed the transaction
- `confirmed_fraud`: Customer denied the transaction
- `verification_failed`: Could not verify customer identity

## Call Flow

### 1. Introduction
The agent introduces itself:
> "Hello, this is SecureBank's fraud detection department. We've detected a suspicious transaction on your account and need to verify it with you."

### 2. Load Fraud Case
The agent asks for the customer's name to load their fraud case:
> "May I have your name please?"

**Tool Used:** `load_fraud_case(username="John Smith")`

### 3. Customer Verification
The agent verifies the customer's identity:
> "For security purposes, can you please provide your security identifier?"

**Tool Used:** `verify_customer(security_identifier="12345")`

**If verification fails:**
> "I'm sorry, but the security identifier doesn't match our records. For security reasons, I cannot proceed."

### 4. Read Transaction Details
Once verified, the agent reads the suspicious transaction:
> "I see a transaction for $2,499.99 at Global Electronics Ltd in Shenzhen, China, made on your card ending in 4242. Did you make this purchase?"

**Tool Used:** `get_transaction_details()`

### 5. Customer Response

**If customer says YES (they made the transaction):**
> "Thank you for confirming. I've marked this transaction as legitimate. Your card is secure and no action is needed."

**Tool Used:** `mark_transaction_safe()`

**If customer says NO (they didn't make it):**
> "I understand. For your protection, I have immediately blocked your card, raised a dispute for this transaction, and started the fraud investigation process."

**Tool Used:** `mark_transaction_fraudulent()`

### 6. Call End
The agent thanks the customer and ends the call:
> "Thank you for your time. Have a great day!"

**Tool Used:** `end_call()`

## Running the Agent

### Prerequisites
Ensure you have:
- LiveKit credentials configured in `.env.local`
- Dependencies installed (`uv sync`)
- VAD models downloaded (`uv run python src/agent.py download-files`)

### Start the Agent

**Development Mode (with console):**
```bash
uv run python src/day6_agent.py dev
```

**Console Mode (terminal only):**
```bash
uv run python src/day6_agent.py console
```

**Production Mode:**
```bash
uv run python src/day6_agent.py start
```

## Testing Guide

### Test Scenario 1: Legitimate Transaction (Safe)
1. Start the agent
2. When asked for name, say: "John Smith"
3. When asked for security identifier, say: "12345"
4. When asked if you made the transaction, say: "Yes, I did"
5. ✅ **Expected Result**: Transaction marked as `confirmed_safe`

### Test Scenario 2: Fraudulent Transaction
1. Start the agent
2. When asked for name, say: "Sarah Johnson"
3. When asked for security identifier, say: "67890"
4. When asked if you made the transaction, say: "No, I didn't make that purchase"
5. ✅ **Expected Result**: Transaction marked as `confirmed_fraud`, card blocked

### Test Scenario 3: Failed Verification
1. Start the agent
2. When asked for name, say: "Michael Chen"
3. When asked for security identifier, say: "wrong-id" (incorrect)
4. ✅ **Expected Result**: Verification fails, call ends gracefully

### Verify Database Updates
After each test, check `fraud_cases.json` to verify:
- Status has been updated
- Outcome note has been added with timestamp

Example:
```json
{
  "id": 1,
  "status": "confirmed_safe",
  "outcomeNote": "Customer confirmed transaction as legitimate on 2025-11-26T21:47:31+05:30"
}
```

## Available Fraud Cases

The database includes 5 pre-configured test cases:

| Name | Security ID | Card Ending | Amount | Merchant |
|------|-------------|-------------|--------|----------|
| John Smith | 12345 | 4242 | $2,499.99 | Global Electronics Ltd |
| Sarah Johnson | 67890 | 8888 | $15,000.00 | Luxury Watches International |
| Michael Chen | 54321 | 1234 | $899.50 | TechGadgets Pro |
| Emily Rodriguez | 99999 | 5678 | $3,750.00 | International Travel Services |
| David Thompson | 11111 | 9999 | $549.99 | Fashion Boutique Online |

## Tools Available to the Agent

### 1. `load_fraud_case(username: str)`
Loads a fraud case from the database for the specified customer.

### 2. `verify_customer(security_identifier: str)`
Verifies the customer's identity using their security identifier.

### 3. `get_transaction_details()`
Retrieves the suspicious transaction details to read to the customer.

### 4. `mark_transaction_safe()`
Marks the transaction as safe when customer confirms they made it.

### 5. `mark_transaction_fraudulent()`
Marks the transaction as fraudulent when customer denies making it.

### 6. `end_call()`
Ends the fraud alert call and finalizes the case.

## Advanced: LiveKit Telephony Integration

To use this agent with real phone calls:

### Setup
1. Configure LiveKit Telephony with a phone number
2. Set up SIP trunk (e.g., Plivo, Twilio)
3. Route calls to the Day 6 agent

### Resources
- [LiveKit Telephony Guide](https://docs.livekit.io/agents/start/telephony/)
- [Phone Numbers Setup](https://docs.livekit.io/sip/cloud/phone-numbers/)
- [Plivo Configuration](https://docs.livekit.io/sip/quickstarts/configuring-plivo-trunk/)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (Customer)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ Voice Input/Output
                       │
┌──────────────────────▼──────────────────────────────────┐
│              LiveKit Voice Pipeline                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   STT    │─▶│   LLM    │─▶│   TTS    │             │
│  │ Deepgram │  │  Gemini  │  │   Murf   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ Function Calls
                       │
┌──────────────────────▼──────────────────────────────────┐
│              FraudAlertAgent                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Tools:                                          │   │
│  │  • load_fraud_case()                           │   │
│  │  • verify_customer()                           │   │
│  │  • get_transaction_details()                   │   │
│  │  • mark_transaction_safe()                     │   │
│  │  • mark_transaction_fraudulent()               │   │
│  │  • end_call()                                  │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ Read/Write
                       │
┌──────────────────────▼──────────────────────────────────┐
│              fraud_cases.json                           │
│         (Persistent Database Storage)                   │
└─────────────────────────────────────────────────────────┘
```

## Logging

The agent logs important events:
- Fraud case loaded
- Customer verification success/failure
- Transaction marked safe/fraudulent
- Call completion status

View logs in the console output:
```
INFO:day6_agent:Loaded fraud case for John Smith: Case ID 1
INFO:day6_agent:Customer John Smith verified successfully
INFO:day6_agent:Transaction marked as SAFE for case ID 1
```

## Error Handling

### Case Not Found
If the customer name doesn't match any fraud case:
> "I couldn't find a fraud case for that name. Please verify the name."

### Already Processed
If the fraud case has already been resolved:
> "This fraud case has already been processed. Status: confirmed_safe"

### Verification Failure
If the security identifier is incorrect:
> "I'm sorry, but the security identifier doesn't match our records. For security reasons, I cannot proceed."

### Database Errors
All database errors are logged, and the agent gracefully handles failures.

## Best Practices

### For Testing
1. **Reset Database**: Before testing, reset fraud cases to `pending_review` status
2. **Use Different Cases**: Test all 5 fraud cases to verify different scenarios
3. **Check Logs**: Monitor console output for debugging
4. **Verify Database**: Always check `fraud_cases.json` after each call

### For Production
1. **Real Data**: Replace fake data with actual fraud alerts
2. **Enhanced Security**: Add multi-factor authentication
3. **Audit Logging**: Log all fraud investigations for compliance
4. **Telephony Integration**: Use LiveKit Telephony for real phone calls
5. **Monitoring**: Set up alerts for failed verifications

## Next Steps

### Primary Goal Completion Checklist
- ✅ Created fraud cases database (`fraud_cases.json`)
- ✅ Built fraud alert agent with professional persona
- ✅ Implemented customer verification
- ✅ Added transaction reading functionality
- ✅ Implemented safe/fraudulent marking
- ✅ Persisted results to database

### Optional Advanced Features to Add
- [ ] LiveKit Telephony integration for real phone calls
- [ ] DTMF input support (press 1 for yes, 2 for no)
- [ ] Multiple fraud cases per customer
- [ ] SMS notifications after fraud resolution
- [ ] Advanced fraud scoring algorithm
- [ ] Historical fraud case review

## License
This project is licensed under the MIT License.
