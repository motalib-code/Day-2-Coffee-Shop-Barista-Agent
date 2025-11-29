import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "day9_data")
SHARED_DATA_DIR = os.path.join(BASE_DIR, "shared-data")
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")
ORDERS_FILE = os.path.join(SHARED_DATA_DIR, "ecommerce_orders.json")

class Catalog:
    def __init__(self):
        self.products = self._load_catalog()

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if not os.path.exists(CATALOG_FILE):
            return []
        with open(CATALOG_FILE, "r") as f:
            return json.load(f)

    def list_products(self, category: Optional[str] = None, max_price: Optional[float] = None, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.products
        
        if category:
            results = [p for p in results if p.get("category", "").lower() == category.lower()]
        
        if max_price:
            results = [p for p in results if p.get("price", 0) <= max_price]
            
        if search_term:
            term = search_term.lower()
            results = [
                p for p in results 
                if term in p.get("name", "").lower() or term in p.get("description", "").lower()
            ]
            
        return results

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        for p in self.products:
            if p["id"] == product_id:
                return p
        return None

class OrderManager:
    def __init__(self):
        self.orders = self._load_orders()

    def _load_orders(self) -> List[Dict[str, Any]]:
        if not os.path.exists(ORDERS_FILE):
            return []
        try:
            with open(ORDERS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_orders(self):
        with open(ORDERS_FILE, "w") as f:
            json.dump(self.orders, f, indent=2)

    def create_order(self, items: List[Dict[str, Any]], buyer_info: Dict[str, str] = None) -> Dict[str, Any]:
        """
        items: List of dicts with {"product_id": str, "quantity": int, "options": dict}
        """
        catalog = Catalog()
        order_items = []
        total_amount = 0.0
        currency = "INR" # Default to INR for TechStyle Store

        for item in items:
            product = catalog.get_product(item["product_id"])
            if not product:
                continue
            
            qty = item.get("quantity", 1)
            price = product["price"]
            total_amount += price * qty
            currency = product.get("currency", "INR")

            order_items.append({
                "product_id": product["id"],
                "name": product["name"],
                "quantity": qty,
                "unit_amount": price, # ACP style naming
                "total_price": price * qty,
                "options": item.get("options", {})
            })

        order = {
            "id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
            "created_at": datetime.now().isoformat(),
            "status": "CONFIRMED",
            "buyer": buyer_info or {"name": "Guest", "email": "guest@example.com"},
            "items": order_items, # keeping 'items' for internal consistency, but could map to line_items
            "line_items": order_items, # ACP style alias
            "total": {
                "amount": round(total_amount, 2),
                "currency": currency
            },
            "total_amount": round(total_amount, 2), # Legacy support
            "currency": currency # Legacy support
        }

        self.orders.append(order)
        self._save_orders()
        return order

    def get_last_order(self) -> Optional[Dict[str, Any]]:
        if not self.orders:
            return None
        return self.orders[-1]

    def get_order_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self.orders[-limit:]

# Global Instances
catalog_instance = Catalog()
order_manager_instance = OrderManager()

# Simple in-memory cart for the demo (single user)
class CartManager:
    def __init__(self):
        self.items = []

    def add_item(self, product_id: str, quantity: int = 1, options: Dict[str, Any] = None):
        product = catalog_instance.get_product(product_id)
        if not product:
            return False, "Product not found."
        
        self.items.append({
            "product_id": product_id,
            "name": product["name"],
            "quantity": quantity,
            "options": options or {},
            "unit_price": product["price"],
            "currency": product["currency"]
        })
        return True, f"Added {quantity}x {product['name']} to cart."

    def view_cart(self) -> str:
        if not self.items:
            return "Your cart is empty."
        
        summary = "--- Your Cart ---\n"
        total = 0.0
        currency = "INR"
        for i, item in enumerate(self.items):
            item_total = item['quantity'] * item['unit_price']
            total += item_total
            currency = item['currency']
            summary += f"{i+1}. {item['quantity']}x {item['name']} ({item['unit_price']} {currency})"
            if item['options']:
                summary += f" | {item['options']}"
            summary += "\n"
        
        summary += f"Total: {round(total, 2)} {currency}"
        return summary

    def clear_cart(self):
        self.items = []

    def get_items(self):
        return self.items

cart_instance = CartManager()

# Public API functions for the Agent
def search_catalog(query: str = None, category: str = None, max_price: float = None) -> str:
    """Searches the product catalog and returns a formatted string of results."""
    products = catalog_instance.list_products(search_term=query, category=category, max_price=max_price)
    if not products:
        return "No products found matching your criteria."
    
    result_str = f"Found {len(products)} products:\n"
    for p in products:
        result_str += f"- {p['name']} ({p['category']}): {p['price']} {p['currency']}\n"
        result_str += f"  ID: {p['id']}\n"
        result_str += f"  {p['description']}\n"
        if "attributes" in p:
            attrs = ", ".join([f"{k}: {v}" for k, v in p["attributes"].items()])
            result_str += f"  Options: {attrs}\n"
        result_str += "\n"
    return result_str

def add_to_cart(product_id: str, quantity: int = 1, options: Dict[str, Any] = None) -> str:
    """Adds an item to the shopping cart."""
    success, msg = cart_instance.add_item(product_id, quantity, options)
    return msg

def view_cart() -> str:
    """Returns the current cart contents."""
    return cart_instance.view_cart()

def checkout(buyer_name: str = "Guest") -> str:
    """Creates an order from the current cart contents and clears the cart."""
    items = cart_instance.get_items()
    if not items:
        return "Cart is empty. Cannot checkout."
    
    # Adapt cart items to create_order format (which expects product_id, quantity, options)
    # create_order re-fetches price to be safe, which is good.
    order_items = []
    for item in items:
        order_items.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "options": item["options"]
        })
    
    buyer_info = {"name": buyer_name, "email": f"{buyer_name.lower().replace(' ', '.')}@example.com"}
    order = order_manager_instance.create_order(order_items, buyer_info)
    cart_instance.clear_cart()
    return f"Order placed successfully! Order ID: {order['id']}. Total: {order['total']['amount']} {order['total']['currency']}."

def place_order(items: List[Dict[str, Any]], buyer_name: str = "Guest") -> str:
    """
    Directly places an order (bypassing cart).
    items: List of dicts, e.g., [{"product_id": "prod_001", "quantity": 1, "options": {"color": "black"}}]
    """
    if not items:
        return "Cannot place an empty order."
    
    buyer_info = {"name": buyer_name, "email": f"{buyer_name.lower().replace(' ', '.')}@example.com"}
    order = order_manager_instance.create_order(items, buyer_info)
    return f"Order placed successfully! Order ID: {order['id']}. Total: {order['total']['amount']} {order['total']['currency']}."

def get_last_order_summary() -> str:
    """Returns a summary of the last placed order."""
    order = order_manager_instance.get_last_order()
    if not order:
        return "No recent orders found."
    
    summary = f"Last Order ({order['id']}) - {order['created_at']}:\n"
    summary += f"Status: {order.get('status', 'Unknown')}\n"
    summary += f"Buyer: {order.get('buyer', {}).get('name', 'Guest')}\n"
    
    for item in order['items']:
        summary += f"- {item['quantity']}x {item['name']} @ {item.get('unit_amount', item.get('unit_price'))} = {item['total_price']}\n"
        if item.get("options"):
            summary += f"  Options: {item['options']}\n"
    
    total = order.get('total', {})
    summary += f"Total: {total.get('amount', order.get('total_amount'))} {total.get('currency', order.get('currency'))}"
    return summary

if __name__ == "__main__":
    # Test
    print(search_catalog(query="mug"))
    print(add_to_cart("prod_004", 2, {"color": "blue"}))
    print(view_cart())
    print(checkout())
    print(get_last_order_summary())
