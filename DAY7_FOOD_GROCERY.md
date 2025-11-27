# Day 7 – Food & Grocery Ordering Voice Agent

## 🎯 Overview

A complete voice-powered food and grocery ordering system built with LiveKit Agents. This agent helps users shop for groceries, build carts, place orders, and track deliveries through natural conversation.

---

## ✨ Features

### Primary Features (MVP)
- ✅ **Product Catalog** - 25+ items across groceries, snacks, and prepared food
- ✅ **Cart Management** - Add, remove, update quantities, view cart
- ✅ **Intelligent Ingredient Bundling** - "I need ingredients for pasta" adds multiple related items
- ✅ **Order Placement** - Save orders to JSON with unique IDs and timestamps
- ✅ **Natural Conversation** - Friendly, helpful ordering assistant

### Advanced Features
- ✅ **Order Tracking** - Mock status progression (received → confirmed → being prepared → out for delivery → delivered)
- ✅ **Order History** - View past orders with details
- ✅ **Smart Reordering** - "Reorder my last order" functionality
- ✅ **Budget Tracking** - Set budget limits and get warnings
- ✅ **Dietary Restrictions** - Filter items by vegan, vegetarian, gluten-free tags
- ✅ **Status Updates** - Orders progress automatically based on elapsed time

---

## 📁 Files Created

### Core Files
```
backend/
├── catalog.json              # Product catalog (25 items)
├── order_history.json        # Order history & recipe mappings
└── src/
    └── day7_agent.py         # Main agent implementation
```

### Catalog Structure
```json
{
  "id": "grocery_001",
  "name": "Whole Wheat Bread",
  "category": "Groceries",
  "subcategory": "Bakery",
  "price": 3.49,
  "brand": "Nature's Own",
  "size": "20 oz",
  "tags": ["vegetarian", "whole-grain"],
  "in_stock": true
}
```

### Order Structure
```json
{
  "id": "abc123",
  "timestamp": "2025-01-27T22:00:00",
  "items": [...],
  "total": 24.99,
  "status": "being_prepared",
  "status_history": [...]
}
```

---

## 🎭 Agent Capabilities

### Shopping Tools
1. **search_items** - Search catalog by name, category, or tags
2. **add_to_cart** - Add items with quantity
3. **add_ingredients_for_dish** - Intelligently add bundled items for recipes
4. **view_cart** - See current cart with totals
5. **update_quantity** - Change item quantities
6. **remove_from_cart** - Remove items

### Order Management
7. **place_order** - Save order to JSON and generate receipt
8. **track_order** - Check order status (auto-updates over time)
9. **view_order_history** - See past orders
10. **reorder_last** - Quickly reorder previous items

### Preferences
11. **set_budget** - Set spending limit with warnings
12. **set_dietary_restrictions** - Filter by dietary needs

---

## 🍝 Recipe Mappings

Pre-configured ingredient bundles:

| Recipe | Includes |
|--------|----------|
| Peanut butter sandwich | Whole wheat bread, peanut butter |
| PB&J sandwich | Whole wheat bread, peanut butter, strawberry jam |
| Pasta for two | Spaghetti, marinara sauce, parmesan cheese |
| Pasta | Spaghetti, marinara sauce |
| Breakfast | White bread, eggs, organic milk |
| Salad | Lettuce, tomatoes, olive oil |

---

## 🚀 Quick Start

### 1. Run the Agent

```bash
cd backend
uv run python src/day7_agent.py dev
```

### 2. Connect to Agent

1. Open browser to: `http://localhost:3000`
2. Join the room when prompted
3. Start speaking!

---

## 💬 Example Conversations

### Simple Order
```
User: Hi!
Agent: Welcome to FreshMart! How can I help you shop today?

User: I need milk and bread.
Agent: I found Organic Milk (Organic Valley, 1 gallon) at $5.99. 
      How many would you like?

User: Just one.
Agent: Added 1 x Organic Milk at $5.99 to your cart. 
      Cart total: $5.99. What else?

User: Add whole wheat bread.
Agent: Added 1 x Whole Wheat Bread (Nature's Own, 20 oz) at $3.49. 
      Cart total: $9.48

User: That's all, place my order.
Agent: ✅ Order placed successfully!
      Order ID: abc12345
      Total: $9.48
      Your order will be prepared shortly!
```

### Ingredient Bundle
```
User: I need ingredients for pasta.
Agent: I've added these ingredients for pasta:
      - Pasta Spaghetti
      - Marinara Sauce
      
      Cart total: $5.98
```

### Order Tracking
```
User: Where's my order?
Agent: 👨‍🍳 Order Status: Being Prepared
      
      Order ID: abc12345
      Total: $9.48
      Items: 2
      
      Your order is being prepared. It should be ready soon!
```

---

## 📊 Order Status Progression

Orders automatically progress every **2 minutes** (configurable):

1. **Received** (0-2 min) 📦
2. **Confirmed** (2-4 min) ✅
3. **Being Prepared** (4-6 min) 👨‍🍳
4. **Out for Delivery** (6-8 min) 🚚
5. **Delivered** (8+ min) 🎉

---

## 🧪 Testing Checklist

### Primary Features
- [ ] Add single item to cart
- [ ] Add multiple items with quantities
- [ ] Update quantity (increase/decrease)
- [ ] Remove item from cart
- [ ] View cart details
- [ ] Add ingredients for dish (e.g., "pasta")
- [ ] Place order and verify JSON saved
- [ ] Check order receipt has correct items/total

### Advanced Features
- [ ] Track order status
- [ ] Verify status auto-updates over time
- [ ] View order history
- [ ] Reorder from last order
- [ ] Set budget and get warnings
- [ ] Set dietary restrictions
- [ ] Search items by category/tag

---

## 🏗️ Architecture

### Agent Class: `FoodGroceryAgent`

**State Management:**
- `cart` - Current shopping cart (list of items)
- `catalog` - Product catalog (loaded from JSON)
- `order_history` - All orders and recipes (loaded from JSON)
- `budget` - Optional spending limit
- `dietary_restrictions` - List of dietary tags to filter by

**Key Methods:**
- `_load_catalog()` - Load products from catalog.json
- `_load_order_history()` - Load orders from order_history.json
- `_save_order_history()` - Persist orders to JSON
- `_find_item_by_name()` - Fuzzy search for items
- `_calculate_cart_total()` - Sum cart prices
- `_update_order_status()` - Progress order status based on time

---

## 📝 Data Persistence

### catalog.json
- **Purpose**: Product inventory
- **Format**: Array of product objects
- **Read**: On agent initialization
- **Write**: Never (static catalog)

### order_history.json
- **Purpose**: Store all orders and recipe mappings
- **Format**: Object with `orders` array and `recipes` object
- **Read**: On agent initialization
- **Write**: When order is placed or status updated

---

## 🎨 Voice & Personality

**Voice**: Emma Falcon (Murf TTS)  
**Style**: Conversational, warm, enthusiastic  
**Tone**: Friendly shopping assistant who loves helping customers find great food

---

## 🔧 Configuration

### Modify Recipe Mappings

Edit `order_history.json`:
```json
{
  "recipes": {
    "your_dish_name": ["item_id_1", "item_id_2"]
  }
}
```

### Adjust Status Progression Speed

In `day7_agent.py`, change the progression interval:
```python
# Progress every N minutes
new_index = min(int(elapsed_minutes / N), len(status_progression) - 1)
```

---

## 🐛 Troubleshooting

### Issue: "Catalog file not found"
- Ensure `catalog.json` exists in `backend/`
- Check file permissions

### Issue: Order not saving
- Check `order_history.json` is writable
- Verify JSON format is valid

### Issue: Items not found
- Use fuzzy matching - partial names work
- Try searching by category first

---

## 🎯 Challenge Completion

### ✅ Primary Goal Complete
- [x] Product catalog created
- [x] Cart management working
- [x] Intelligent ingredient bundling
- [x] Orders saved to JSON

### ✅ Advanced Goals Complete
- [x] Order tracking with status progression
- [x] Order history
- [x] Reorder functionality
- [x] Budget tracking
- [x] Dietary restrictions

---

## 📹 Demo Video

When recording your demo:
1. Show adding items to cart
2. Demonstrate ingredient bundling ("I need ingredients for pasta")
3. View cart and update quantities
4. Place order
5. Show saved order JSON file
6. Track order status
7. Reorder from history

---

## 🙌 Next Steps

1. ✅ Complete primary goal
2. ✅ Complete advanced goals
3. [ ] Record demo video
4. [ ] Post to LinkedIn with hashtags:
   - #MurfAIVoiceAgentsChallenge
   - #10DaysofAIVoiceAgents
   - Tag @Murf AI

---

## 📚 Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Building Tools](https://docs.livekit.io/agents/build/tools/)
- [Prompting Guide](https://docs.livekit.io/agents/build/prompting/)

---

**Built with:** LiveKit Agents, Murf Falcon TTS, Google Gemini 2.5 Flash, Deepgram STT
