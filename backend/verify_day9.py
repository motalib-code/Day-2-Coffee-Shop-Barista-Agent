import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from day9_merchant import search_catalog, place_order, get_last_order_summary, OrderManager, add_to_cart, view_cart, checkout

def test_ecommerce_flow():
    print("--- Testing Day 9 E-commerce Logic (TechStyle Store) ---")

    # 1. Search
    print("\n1. Searching for 'mug'...")
    results = search_catalog(query="mug")
    print(results)
    assert "Developer Coffee Mug" in results

    # 2. Place Order (Direct)
    print("\n2. Placing Order (Direct)...")
    # Find the mug ID first to be dynamic, or hardcode if we know it (mug_001)
    items = [
        {"product_id": "mug_001", "quantity": 2, "options": {"color": "white"}},
        {"product_id": "tshirt_001", "quantity": 1, "options": {"size": "L", "color": "grey"}}
    ]
    order_result = place_order(items, buyer_name="Test User")
    print(order_result)
    assert "Order placed successfully" in order_result

    # 3. Cart Flow
    print("\n3. Testing Cart Flow...")
    print(add_to_cart("hoodie_001", 1, {"size": "M", "color": "black"}))
    print(add_to_cart("sticker_001", 1))
    cart_view = view_cart()
    print(cart_view)
    assert "Code Ninja Hoodie" in cart_view
    assert "Developer Sticker Pack" in cart_view
    
    print("Checking out...")
    checkout_result = checkout(buyer_name="Cart User")
    print(checkout_result)
    assert "Order placed successfully" in checkout_result
    
    # Verify cart is empty
    assert "empty" in view_cart()

    # 4. Get Last Order
    print("\n4. Getting Last Order Summary...")
    summary = get_last_order_summary()
    print(summary)
    # Should be the cart order now
    assert "Code Ninja Hoodie" in summary
    assert "Cart User" in summary

    # 5. Verify Persistence
    print("\n5. Verifying Persistence in shared-data/ecommerce_orders.json...")
    # shared-data is in backend/shared-data
    orders_file = os.path.join(os.path.dirname(__file__), "shared-data", "ecommerce_orders.json")
         
    with open(orders_file, "r") as f:
        orders = json.load(f)
        print(f"Found {len(orders)} orders in file.")
        last_order = orders[-1]
        assert len(last_order["items"]) == 2 # Hoodie + Sticker
        assert last_order["buyer"]["name"] == "Cart User"
        print("Persistence verified.")

    print("\n--- Day 9 Verification Passed! ---")

if __name__ == "__main__":
    test_ecommerce_flow()
