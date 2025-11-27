import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import uuid

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
    metrics,
    tokenize,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("day7_agent")

load_dotenv(".env.local")

# Paths
CATALOG_FILE = Path(__file__).parent.parent / "catalog.json"
ORDER_HISTORY_FILE = Path(__file__).parent.parent / "order_history.json"


class FoodGroceryAgent(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(
            instructions="""You are a friendly food and grocery ordering assistant for FreshMart, a premier food delivery service.
            
            **Your Role:**
            Help customers order groceries, snacks, and prepared food from our catalog.
            
            **Your Tone:**
            - Warm, friendly, and helpful
            - Enthusiastic about food
            - Patient and understanding
            - Proactive in making suggestions
            
            **What You Can Do:**
            1. Help customers add items to their cart
            2. Suggest ingredients for specific dishes (e.g., "I need ingredients for pasta")
            3. Show what's in their cart
            4. Update quantities or remove items
            5. Place orders when ready
            6. Track existing orders
            7. Show order history
            8. Suggest reorders based on past purchases
            
            **Conversation Flow:**
            1. **Greeting**: Welcome the customer warmly and ask how you can help.
            2. **Shopping**: Help them browse, add items, and build their cart.
            3. **Clarification**: Ask about quantities, sizes, brands when needed.
            4. **Confirmation**: Confirm additions/changes to the cart.
            5. **Checkout**: When ready, review the cart and place the order.
            6. **Tracking**: Answer questions about order status.
            
            **Important Rules:**
            - Always confirm item additions with quantity
            - Be specific about brand and size
            - Calculate and mention the running total
            - When suggesting ingredients for a dish, explain what you're adding
            - Keep track of budget if customer mentions one
            - Respect dietary restrictions (vegan, vegetarian, gluten-free)
            
            **Current State:**
            - Cart: Empty
            - Budget: No limit set
            - Dietary restrictions: None set
            
            Start by greeting the customer and offering to help them shop!
            """,
        )
        self.room = room
        self.cart: List[Dict] = []
        self.catalog: List[Dict] = []
        self.order_history: Dict = {}
        self.budget: Optional[float] = None
        self.dietary_restrictions: List[str] = []
        
        # Load catalog and order history
        self._load_catalog()
        self._load_order_history()

    def _load_catalog(self):
        """Load the product catalog from JSON."""
        try:
            if not CATALOG_FILE.exists():
                logger.error(f"Catalog file not found: {CATALOG_FILE}")
                return
            
            with open(CATALOG_FILE, "r") as f:
                self.catalog = json.load(f)
            
            logger.info(f"Loaded {len(self.catalog)} items from catalog")
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")

    def _load_order_history(self):
        """Load order history from JSON."""
        try:
            if not ORDER_HISTORY_FILE.exists():
                # Create empty history
                self.order_history = {"orders": [], "recipes": {}}
                self._save_order_history()
                return
            
            with open(ORDER_HISTORY_FILE, "r") as f:
                self.order_history = json.load(f)
            
            logger.info(f"Loaded {len(self.order_history.get('orders', []))} orders from history")
        except Exception as e:
            logger.error(f"Error loading order history: {e}")
            self.order_history = {"orders": [], "recipes": {}}

    def _save_order_history(self):
        """Save order history to JSON."""
        try:
            with open(ORDER_HISTORY_FILE, "w") as f:
                json.dump(self.order_history, f, indent=2)
            logger.info(f"Saved order history with {len(self.order_history.get('orders', []))} orders")
        except Exception as e:
            logger.error(f"Error saving order history: {e}")

    def _find_item_by_name(self, item_name: str) -> Optional[Dict]:
        """Find an item in the catalog by name (fuzzy matching)."""
        item_name_lower = item_name.lower()
        
        # Try exact match first
        for item in self.catalog:
            if item["name"].lower() == item_name_lower:
                return item
        
        # Try partial match
        for item in self.catalog:
            if item_name_lower in item["name"].lower():
                return item
        
        return None

    def _find_item_by_id(self, item_id: str) -> Optional[Dict]:
        """Find an item in the catalog by ID."""
        for item in self.catalog:
            if item["id"] == item_id:
                return item
        return None

    def _calculate_cart_total(self) -> float:
        """Calculate the total cost of items in the cart."""
        total = 0.0
        for cart_item in self.cart:
            total += cart_item["price"] * cart_item["quantity"]
        return round(total, 2)

    def _check_dietary_restrictions(self, item: Dict) -> bool:
        """Check if an item meets dietary restrictions."""
        if not self.dietary_restrictions:
            return True
        
        item_tags = item.get("tags", [])
        for restriction in self.dietary_restrictions:
            if restriction not in item_tags:
                return False
        return True

    @function_tool
    async def search_items(
        self, 
        context: RunContext, 
        search_term: str
    ) -> str:
        """Search for items in the catalog.
        
        Args:
            search_term: The product name, category, or keyword to search for.
        """
        search_lower = search_term.lower()
        matching_items = []
        
        for item in self.catalog:
            if (search_lower in item["name"].lower() or 
                search_lower in item["category"].lower() or
                search_lower in item.get("subcategory", "").lower() or
                any(search_lower in tag for tag in item.get("tags", []))):
                matching_items.append(item)
        
        if not matching_items:
            return f"I couldn't find any items matching '{search_term}'. Try searching for categories like 'bread', 'milk', 'snacks', or 'pizza'."
        
        # Limit to top 5 results
        result_items = matching_items[:5]
        result = f"I found {len(matching_items)} items"
        if len(matching_items) > 5:
            result += f" (showing top 5)"
        result += f" matching '{search_term}':\n\n"
        
        for item in result_items:
            result += f"- {item['name']} ({item['brand']}, {item['size']}) - ${item['price']}\n"
        
        return result

    @function_tool
    async def add_to_cart(
        self, 
        context: RunContext, 
        item_name: str, 
        quantity: int = 1
    ) -> str:
        """Add an item to the cart.
        
        Args:
            item_name: The name of the item to add.
            quantity: How many units to add (default is 1).
        """
        item = self._find_item_by_name(item_name)
        
        if not item:
            return f"I couldn't find '{item_name}' in our catalog. Would you like me to search for similar items?"
        
        if not item.get("in_stock", False):
            return f"Sorry, {item['name']} is currently out of stock. Can I suggest an alternative?"
        
        # Check dietary restrictions
        if self.dietary_restrictions and not self._check_dietary_restrictions(item):
            return f"Note: {item['name']} doesn't match your dietary restrictions ({', '.join(self.dietary_restrictions)}). Would you still like to add it?"
        
        # Check if item already in cart
        existing_item = None
        for cart_item in self.cart:
            if cart_item["id"] == item["id"]:
                existing_item = cart_item
                break
        
        if existing_item:
            existing_item["quantity"] += quantity
            response = f"Updated {item['name']} quantity to {existing_item['quantity']}."
        else:
            cart_entry = {
                "id": item["id"],
                "name": item["name"],
                "brand": item["brand"],
                "size": item["size"],
                "price": item["price"],
                "quantity": quantity
            }
            self.cart.append(cart_entry)
            response = f"Added {quantity} x {item['name']} ({item['brand']}, {item['size']}) at ${item['price']} each to your cart."
        
        total = self._calculate_cart_total()
        response += f" Cart total: ${total}"
        
        # Check budget
        if self.budget and total > self.budget:
            response += f" ⚠️ Warning: You've exceeded your budget of ${self.budget} by ${round(total - self.budget, 2)}."
        
        logger.info(f"Added to cart: {item['name']} x {quantity}")
        return response

    @function_tool
    async def add_ingredients_for_dish(
        self, 
        context: RunContext, 
        dish_name: str
    ) -> str:
        """Add ingredients needed for a specific dish.
        
        Args:
            dish_name: The name of the dish (e.g., "pasta", "peanut butter sandwich", "salad").
        """
        dish_lower = dish_name.lower()
        recipes = self.order_history.get("recipes", {})
        
        # Find matching recipe
        recipe_items = None
        matched_recipe = None
        for recipe_name, item_ids in recipes.items():
            if dish_lower in recipe_name or recipe_name in dish_lower:
                recipe_items = item_ids
                matched_recipe = recipe_name
                break
        
        if not recipe_items:
            return f"I don't have a specific recipe for '{dish_name}'. Try searching for individual items or ask me to add specific ingredients."
        
        added_items = []
        for item_id in recipe_items:
            item = self._find_item_by_id(item_id)
            if item and item.get("in_stock", False):
                # Check if already in cart
                existing = None
                for cart_item in self.cart:
                    if cart_item["id"] == item["id"]:
                        existing = cart_item
                        break
                
                if not existing:
                    cart_entry = {
                        "id": item["id"],
                        "name": item["name"],
                        "brand": item["brand"],
                        "size": item["size"],
                        "price": item["price"],
                        "quantity": 1
                    }
                    self.cart.append(cart_entry)
                    added_items.append(item["name"])
        
        if not added_items:
            return f"All ingredients for {matched_recipe} are already in your cart!"
        
        total = self._calculate_cart_total()
        response = f"I've added these ingredients for {matched_recipe}:\n"
        response += "\n".join([f"- {name}" for name in added_items])
        response += f"\n\nCart total: ${total}"
        
        logger.info(f"Added ingredients for {matched_recipe}: {added_items}")
        return response

    @function_tool
    async def view_cart(self, context: RunContext) -> str:
        """View all items currently in the cart."""
        if not self.cart:
            return "Your cart is empty. Would you like to add some items?"
        
        response = f"Here's what's in your cart ({len(self.cart)} items):\n\n"
        for item in self.cart:
            item_total = item["price"] * item["quantity"]
            response += f"- {item['quantity']} x {item['name']} ({item['brand']}, {item['size']}) = ${item_total}\n"
        
        total = self._calculate_cart_total()
        response += f"\n**Total: ${total}**"
        
        if self.budget:
            remaining = self.budget - total
            response += f"\nBudget: ${self.budget} (${remaining} remaining)" if remaining >= 0 else f"\nBudget: ${self.budget} (${abs(remaining)} over budget)"
        
        return response

    @function_tool
    async def update_quantity(
        self, 
        context: RunContext, 
        item_name: str, 
        new_quantity: int
    ) -> str:
        """Update the quantity of an item in the cart.
        
        Args:
            item_name: The name of the item to update.
            new_quantity: The new quantity (use 0 to remove the item).
        """
        cart_item = None
        for item in self.cart:
            if item_name.lower() in item["name"].lower():
                cart_item = item
                break
        
        if not cart_item:
            return f"'{item_name}' is not in your cart. Would you like to add it?"
        
        if new_quantity <= 0:
            self.cart.remove(cart_item)
            return f"Removed {cart_item['name']} from your cart. Cart total: ${self._calculate_cart_total()}"
        
        old_quantity = cart_item["quantity"]
        cart_item["quantity"] = new_quantity
        
        response = f"Updated {cart_item['name']} from {old_quantity} to {new_quantity}. "
        response += f"Cart total: ${self._calculate_cart_total()}"
        
        logger.info(f"Updated quantity: {cart_item['name']} {old_quantity} -> {new_quantity}")
        return response

    @function_tool
    async def remove_from_cart(
        self, 
        context: RunContext, 
        item_name: str
    ) -> str:
        """Remove an item from the cart.
        
        Args:
            item_name: The name of the item to remove.
        """
        cart_item = None
        for item in self.cart:
            if item_name.lower() in item["name"].lower():
                cart_item = item
                break
        
        if not cart_item:
            return f"'{item_name}' is not in your cart."
        
        self.cart.remove(cart_item)
        total = self._calculate_cart_total()
        
        logger.info(f"Removed from cart: {cart_item['name']}")
        return f"Removed {cart_item['name']} from your cart. Cart total: ${total}"

    @function_tool
    async def set_budget(
        self, 
        context: RunContext, 
        budget_amount: float
    ) -> str:
        """Set a budget limit for the order.
        
        Args:
            budget_amount: The maximum amount to spend.
        """
        self.budget = budget_amount
        current_total = self._calculate_cart_total()
        
        response = f"Budget set to ${budget_amount}. "
        if current_total > 0:
            remaining = budget_amount - current_total
            if remaining >= 0:
                response += f"Current cart total is ${current_total}. You have ${remaining} remaining."
            else:
                response += f"Your current cart total (${current_total}) exceeds your budget by ${abs(remaining)}."
        
        logger.info(f"Budget set to ${budget_amount}")
        return response

    @function_tool
    async def set_dietary_restrictions(
        self, 
        context: RunContext, 
        restrictions: str
    ) -> str:
        """Set dietary restrictions for filtering items.
        
        Args:
            restrictions: Comma-separated list (e.g., "vegan, gluten-free").
        """
        self.dietary_restrictions = [r.strip().lower() for r in restrictions.split(",")]
        
        response = f"I'll filter items to match your dietary needs: {', '.join(self.dietary_restrictions)}."
        
        logger.info(f"Dietary restrictions set: {self.dietary_restrictions}")
        return response

    @function_tool
    async def place_order(self, context: RunContext) -> str:
        """Place the current order and save it."""
        if not self.cart:
            return "Your cart is empty. Add some items before placing an order!"
        
        order_id = str(uuid.uuid4())[:8]
        order = {
            "id": order_id,
            "timestamp": datetime.now().isoformat(),
            "items": self.cart.copy(),
            "total": self._calculate_cart_total(),
            "status": "received",
            "status_history": [
                {"status": "received", "timestamp": datetime.now().isoformat()}
            ]
        }
        
        # Add to order history
        if "orders" not in self.order_history:
            self.order_history["orders"] = []
        self.order_history["orders"].append(order)
        self._save_order_history()
        
        # Generate receipt
        response = f"✅ Order placed successfully!\n\n"
        response += f"**Order ID: {order_id}**\n"
        response += f"**Order Time: {datetime.now().strftime('%I:%M %p, %B %d, %Y')}**\n\n"
        response += "Items:\n"
        for item in order["items"]:
            response += f"- {item['quantity']} x {item['name']} = ${item['price'] * item['quantity']}\n"
        response += f"\n**Total: ${order['total']}**\n\n"
        response += "Your order has been received and will be prepared shortly. You can track it using the order ID."
        
        # Clear cart
        self.cart = []
        
        logger.info(f"Order placed: {order_id}, Total: ${order['total']}")
        return response

    @function_tool
    async def track_order(
        self, 
        context: RunContext, 
        order_id: Optional[str] = None
    ) -> str:
        """Track an order's status.
        
        Args:
            order_id: The order ID to track. If not provided, tracks the most recent order.
        """
        orders = self.order_history.get("orders", [])
        
        if not orders:
            return "You don't have any orders yet. Place your first order to get started!"
        
        # Find order
        if order_id:
            order = None
            for o in orders:
                if o["id"] == order_id:
                    order = o
                    break
            if not order:
                return f"I couldn't find an order with ID '{order_id}'."
        else:
            # Get most recent order
            order = orders[-1]
        
        # Update status (mock progression)
        self._update_order_status(order)
        
        status_emoji = {
            "received": "📦",
            "confirmed": "✅",
            "being_prepared": "👨‍🍳",
            "out_for_delivery": "🚚",
            "delivered": "🎉"
        }
        
        emoji = status_emoji.get(order["status"], "📋")
        status_text = order["status"].replace("_", " ").title()
        
        response = f"{emoji} **Order Status: {status_text}**\n\n"
        response += f"Order ID: {order['id']}\n"
        response += f"Order Time: {order['timestamp'][:19]}\n"
        response += f"Total: ${order['total']}\n"
        response += f"Items: {len(order['items'])}\n"
        
        if order["status"] == "delivered":
            response += "\nYour order has been delivered! Enjoy your food! 🎉"
        elif order["status"] == "out_for_delivery":
            response += "\nYour order is on the way! Expected delivery in 15-30 minutes."
        elif order["status"] == "being_prepared":
            response += "\nYour order is being prepared. It should be ready soon!"
        
        return response

    def _update_order_status(self, order: Dict):
        """Update order status based on elapsed time (mock progression)."""
        status_progression = ["received", "confirmed", "being_prepared", "out_for_delivery", "delivered"]
        current_status = order["status"]
        
        if current_status == "delivered":
            return
        
        # Calculate time elapsed since order
        order_time = datetime.fromisoformat(order["timestamp"])
        elapsed_minutes = (datetime.now() - order_time).total_seconds() / 60
        
        # Progress status every 2 minutes (for demo purposes)
        current_index = status_progression.index(current_status)
        new_index = min(int(elapsed_minutes / 2), len(status_progression) - 1)
        
        if new_index > current_index:
            new_status = status_progression[new_index]
            order["status"] = new_status
            order["status_history"].append({
                "status": new_status,
                "timestamp": datetime.now().isoformat()
            })
            self._save_order_history()
            logger.info(f"Order {order['id']} status updated: {current_status} -> {new_status}")

    @function_tool
    async def view_order_history(self, context: RunContext) -> str:
        """View past orders."""
        orders = self.order_history.get("orders", [])
        
        if not orders:
            return "You don't have any order history yet. Place your first order to get started!"
        
        response = f"You have {len(orders)} past order(s):\n\n"
        
        # Show last 5 orders
        recent_orders = orders[-5:]
        for order in reversed(recent_orders):
            order_date = datetime.fromisoformat(order["timestamp"]).strftime("%b %d, %I:%M %p")
            response += f"- Order {order['id']}: ${order['total']} ({len(order['items'])} items) - {order_date} - Status: {order['status']}\n"
        
        if len(orders) > 5:
            response += f"\n(Showing 5 most recent orders)"
        
        return response

    @function_tool
    async def reorder_last(self, context: RunContext) -> str:
        """Reorder items from the last order."""
        orders = self.order_history.get("orders", [])
        
        if not orders:
            return "You don't have any previous orders to reorder from."
        
        last_order = orders[-1]
        items_added = []
        
        for order_item in last_order["items"]:
            # Find item in current catalog
            item = self._find_item_by_id(order_item["id"])
            if item and item.get("in_stock", False):
                # Check if already in cart
                existing = None
                for cart_item in self.cart:
                    if cart_item["id"] == item["id"]:
                        existing = cart_item
                        break
                
                if existing:
                    existing["quantity"] += order_item["quantity"]
                else:
                    cart_entry = {
                        "id": item["id"],
                        "name": item["name"],
                        "brand": item["brand"],
                        "size": item["size"],
                        "price": item["price"],
                        "quantity": order_item["quantity"]
                    }
                    self.cart.append(cart_entry)
                items_added.append(f"{order_item['quantity']} x {item['name']}")
        
        if not items_added:
            return "None of the items from your last order are currently available."
        
        response = "I've added items from your last order to your cart:\n"
        response += "\n".join([f"- {item}" for item in items_added])
        response += f"\n\nCart total: ${self._calculate_cart_total()}"
        
        logger.info(f"Reordered {len(items_added)} items from last order")
        return response


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Initialize TTS
    murf_tts = murf.TTS(
        voice="en-US-emma-falcon",
        style="Conversation",
        tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
        text_pacing=True,
    )

    # Set up voice AI pipeline
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=murf_tts,
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Metrics collection
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session
    agent = FoodGroceryAgent(room=ctx.room)
    
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
