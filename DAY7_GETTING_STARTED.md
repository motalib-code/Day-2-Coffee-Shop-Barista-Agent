# Day 7 - Getting Started Guide

## 🚀 Quick Setup

### 1. Prerequisites
- LiveKit account and credentials
- Python 3.10+
- `uv` package manager
- Web browser

### 2. Environment Setup

Ensure your `.env.local` file in `backend/` has:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
MURF_API_KEY=your_murf_key
GOOGLE_API_KEY=your_google_key
DEEPGRAM_API_KEY=your_deepgram_key
```

### 3. Install Dependencies

```bash
cd backend
uv sync
```

### 4. Verify Files

Check that these files exist:
```
backend/
├── catalog.json              ✓ Product catalog
├── order_history.json        ✓ Order history & recipes
└── src/
    └── day7_agent.py         ✓ Agent implementation
```

### 5. Run Tests (Optional)

```bash
cd backend
uv run pytest test_day7.py -v
```

### 6. Start the Agent

```bash
cd backend
uv run python src/day7_agent.py dev
```

You should see:
```
[INFO] Agent started
[INFO] Loaded 25 items from catalog
[INFO] Loaded N orders from history
```

### 7. Connect to Agent

1. Open browser to: `http://localhost:3000`
2. Allow microphone access
3. Click "Connect" or "Join"
4. Start speaking!

---

## 🎤 First Conversation

Try this flow:

**You:** "Hi!"

**Agent:** "Welcome to FreshMart! I'm your grocery shopping assistant. I can help you order groceries, snacks, and prepared food. What would you like today?"

**You:** "Search for bread"

**Agent:** "I found 2 items matching 'bread':
- Whole Wheat Bread (Nature's Own, 20 oz) - $3.49
- White Bread (Wonder Bread, 20 oz) - $2.99"

**You:** "Add whole wheat bread"

**Agent:** "Added 1 x Whole Wheat Bread (Nature's Own, 20 oz) at $3.49 to your cart. Cart total: $3.49"

**You:** "I need ingredients for pasta"

**Agent:** "I've added these ingredients for pasta:
- Pasta Spaghetti
- Marinara Sauce

Cart total: $5.98"

**You:** "Show my cart"

**Agent:** "Here's what's in your cart (3 items):
- 1 x Whole Wheat Bread (Nature's Own, 20 oz) = $3.49
- 1 x Pasta Spaghetti (Barilla, 16 oz) = $1.99
- 1 x Marinara Sauce (Prego, 24 oz) = $3.99

**Total: $9.47**"

**You:** "Place my order"

**Agent:** "✅ Order placed successfully!

**Order ID: abc12345**
**Order Time: 10:00 PM, January 27, 2025**

Items:
- 1 x Whole Wheat Bread = $3.49
- 1 x Pasta Spaghetti = $1.99
- 1 x Marinara Sauce = $3.99

**Total: $9.47**

Your order has been received and will be prepared shortly. You can track it using the order ID."

---

## 🧪 Testing Features

### Test Cart Management
```
"Add 2 apples"
"Change apple quantity to 5"
"Remove apples"
```

### Test Ingredient Bundling
```
"I need ingredients for peanut butter sandwich"
"Get me what I need for breakfast"
"I want to make salad"
```

### Test Dietary Restrictions
```
"I'm vegan"
[Agent will now filter/warn about non-vegan items]
```

### Test Budget
```
"Set my budget to 20 dollars"
[Agent will warn when cart exceeds $20]
```

### Test Order Tracking
```
"Track my order"
[Wait 2+ minutes]
"Where is my order?"
[Status should progress]
```

### Test Order History
```
"Show my order history"
"What did I order last time?"
"Reorder my last order"
```

---

## 📊 Understanding Order Status

Orders automatically progress:

| Time | Status | Emoji |
|------|--------|-------|
| 0-2 min | Received | 📦 |
| 2-4 min | Confirmed | ✅ |
| 4-6 min | Being Prepared | 👨‍🍳 |
| 6-8 min | Out for Delivery | 🚚 |
| 8+ min | Delivered | 🎉 |

---

## 📁 Checking Saved Orders

After placing an order, check `backend/order_history.json`:

```json
{
  "orders": [
    {
      "id": "abc12345",
      "timestamp": "2025-01-27T22:00:00",
      "items": [...],
      "total": 9.47,
      "status": "received",
      "status_history": [...]
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Agent doesn't start
```bash
# Check dependencies
cd backend
uv sync

# Verify environment
cat .env.local
```

### Can't hear agent
- Check browser microphone permissions
- Verify Murf API key is valid
- Check browser console for errors

### Items not found
- Verify `catalog.json` exists
- Check spelling (fuzzy matching works)
- Try searching by category

### Order not saving
- Check file permissions on `backend/`
- Verify `order_history.json` is not read-only
- Check logs for errors

### Tests fail
```bash
# Make sure you're in backend directory
cd backend

# Run with verbose output
uv run pytest test_day7.py -v -s
```

---

## 🎯 Challenge Checklist

### Primary Goal ✅
- [x] Create catalog.json with 25+ items
- [x] Implement cart management
- [x] Add ingredient bundling
- [x] Place orders and save to JSON
- [x] Confirm order receipt

### Advanced Goal 1 - Order Tracking ✅
- [x] Status progression over time
- [x] Track order by ID
- [x] Answer "where is my order?"

### Advanced Goal 2 - Order History ✅
- [x] Store all orders in JSON
- [x] View past orders
- [x] Reference previous orders

### Advanced Goal 3 - Multiple Orders ✅
- [x] Support multiple active orders
- [x] Track specific orders by ID
- [x] Maintain history

### Advanced Goal 4 - Smart Reorder ✅
- [x] Reorder from last order
- [x] Access order history

### Advanced Goal 5 - Budget & Constraints ✅
- [x] Set budget limit
- [x] Dietary restrictions
- [x] Filter items by tags

---

## 📹 Recording Your Demo

### What to Show:
1. **Greeting** - Start conversation
2. **Add items** - Add individual items with quantities
3. **Ingredient bundling** - "I need ingredients for pasta"
4. **View cart** - Show cart contents and total
5. **Update cart** - Change quantities, remove items
6. **Place order** - Complete checkout
7. **Show JSON** - Open `order_history.json` in editor
8. **Track order** - Wait a few minutes, track status
9. **Reorder** - "Reorder my last order"

### Recording Tips:
- Use screen recording software (OBS, QuickTime, etc.)
- Keep video under 2 minutes
- Show both browser and terminal
- Demonstrate natural conversation
- Highlight the JSON file with saved order

---

## 🎉 You're Ready!

Start the agent and begin testing. Once everything works:
1. Record your demo video
2. Post on LinkedIn
3. Tag @Murf AI
4. Use hashtags: #MurfAIVoiceAgentsChallenge #10DaysofAIVoiceAgents

Good luck! 🚀
