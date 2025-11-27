# DAY 7 QUICK REFERENCE

## Start Agent
```bash
cd backend
uv run python src/day7_agent.py dev
```

## Connect
Browser: `http://localhost:3000`

## Voice Commands

### Shopping
- "Search for milk"
- "Add bread to cart"
- "Add 3 apples"
- "I need ingredients for pasta"
- "Show me my cart"

### Cart Management
- "Remove bread"
- "Update milk quantity to 2"
- "Change eggs to 3"

### Orders
- "Place my order"
- "Track my order"
- "Where is my order?"
- "Show order history"
- "Reorder my last order"

### Preferences
- "Set budget to 50 dollars"
- "I'm vegan" (sets dietary restrictions)

## Files
- `backend/catalog.json` - Product catalog
- `backend/order_history.json` - Orders & recipes
- `backend/src/day7_agent.py` - Agent code

## Recipe Triggers
- "peanut butter sandwich" → bread + peanut butter
- "pb&j sandwich" → bread + peanut butter + jam
- "pasta" → spaghetti + marinara sauce
- "pasta for two" → spaghetti + marinara + parmesan
- "breakfast" → bread + eggs + milk
- "salad" → lettuce + tomatoes + olive oil

## Order Status
📦 Received → ✅ Confirmed → 👨‍🍳 Being Prepared → 🚚 Out for Delivery → 🎉 Delivered

Auto-progresses every 2 minutes

## Quick Test Flow
1. Start agent
2. "Hi, search for bread"
3. "Add whole wheat bread"
4. "I need ingredients for pasta"
5. "Show my cart"
6. "Place my order"
7. Wait 4+ minutes
8. "Track my order" (should show "Being Prepared")
9. "Show order history"
10. "Reorder my last order"
