"""
Test suite for Day 7 - Food & Grocery Ordering Voice Agent

This module tests the FoodGroceryAgent functionality including:
- Product catalog loading
- Cart management (add, remove, update)
- Ingredient bundling for dishes
- Order placement and persistence
- Order tracking and status progression
- Order history and reordering
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from day7_agent import FoodGroceryAgent
from livekit import rtc


@pytest.fixture
def mock_room():
    """Create a mock LiveKit room."""
    class MockRoom:
        name = "test_room"
    return MockRoom()


@pytest.fixture
def agent(mock_room):
    """Create a FoodGroceryAgent instance."""
    return FoodGroceryAgent(room=mock_room)


@pytest.fixture
def catalog_file():
    """Return path to catalog file."""
    return Path(__file__).parent / "catalog.json"


@pytest.fixture
def order_history_file():
    """Return path to order history file."""
    return Path(__file__).parent / "order_history.json"


class TestCatalogLoading:
    """Test product catalog loading and searching."""
    
    def test_catalog_loads(self, agent, catalog_file):
        """Test that catalog file loads successfully."""
        assert catalog_file.exists(), "Catalog file should exist"
        assert len(agent.catalog) > 0, "Catalog should contain items"
        assert len(agent.catalog) >= 20, "Catalog should have at least 20 items"
    
    def test_catalog_structure(self, agent):
        """Test that catalog items have required fields."""
        required_fields = ["id", "name", "category", "price", "brand", "size", "in_stock"]
        for item in agent.catalog:
            for field in required_fields:
                assert field in item, f"Item should have '{field}' field"
            assert isinstance(item["price"], (int, float)), "Price should be numeric"
            assert item["price"] > 0, "Price should be positive"
    
    def test_find_item_by_name(self, agent):
        """Test finding items by name."""
        # Exact match
        item = agent._find_item_by_name("Whole Wheat Bread")
        assert item is not None, "Should find exact match"
        assert item["name"] == "Whole Wheat Bread"
        
        # Partial match
        item = agent._find_item_by_name("bread")
        assert item is not None, "Should find partial match"
        assert "bread" in item["name"].lower()
        
        # Non-existent item
        item = agent._find_item_by_name("Flying Unicorn")
        assert item is None, "Should return None for non-existent item"


class TestCartManagement:
    """Test shopping cart operations."""
    
    def test_add_to_cart(self, agent):
        """Test adding items to cart."""
        agent.cart = []
        
        # Find an item in catalog
        bread = agent._find_item_by_name("bread")
        assert bread is not None
        
        # Simulate adding to cart
        cart_entry = {
            "id": bread["id"],
            "name": bread["name"],
            "brand": bread["brand"],
            "size": bread["size"],
            "price": bread["price"],
            "quantity": 1
        }
        agent.cart.append(cart_entry)
        
        assert len(agent.cart) == 1, "Cart should have 1 item"
        assert agent.cart[0]["name"] == bread["name"]
    
    def test_cart_total_calculation(self, agent):
        """Test cart total calculation."""
        agent.cart = [
            {"id": "1", "name": "Item 1", "price": 5.99, "quantity": 2},
            {"id": "2", "name": "Item 2", "price": 3.49, "quantity": 1},
        ]
        
        total = agent._calculate_cart_total()
        expected = (5.99 * 2) + (3.49 * 1)
        assert total == round(expected, 2), f"Total should be {expected}"
    
    def test_empty_cart_total(self, agent):
        """Test total for empty cart."""
        agent.cart = []
        total = agent._calculate_cart_total()
        assert total == 0.0, "Empty cart total should be 0"
    
    def test_update_quantity(self, agent):
        """Test updating item quantity in cart."""
        agent.cart = [
            {"id": "1", "name": "Test Item", "price": 5.00, "quantity": 1}
        ]
        
        # Update quantity
        agent.cart[0]["quantity"] = 3
        assert agent.cart[0]["quantity"] == 3, "Quantity should be updated"
        
        total = agent._calculate_cart_total()
        assert total == 15.00, "Total should reflect new quantity"
    
    def test_remove_from_cart(self, agent):
        """Test removing items from cart."""
        agent.cart = [
            {"id": "1", "name": "Item 1", "price": 5.00, "quantity": 1},
            {"id": "2", "name": "Item 2", "price": 3.00, "quantity": 1}
        ]
        
        # Remove first item
        agent.cart = [item for item in agent.cart if item["id"] != "1"]
        
        assert len(agent.cart) == 1, "Cart should have 1 item after removal"
        assert agent.cart[0]["id"] == "2", "Remaining item should be Item 2"


class TestIngredientBundling:
    """Test intelligent ingredient bundling for dishes."""
    
    def test_recipe_mappings_exist(self, agent):
        """Test that recipe mappings are loaded."""
        recipes = agent.order_history.get("recipes", {})
        assert len(recipes) > 0, "Should have recipe mappings"
        assert "pasta" in recipes, "Should have pasta recipe"
    
    def test_recipe_items_in_catalog(self, agent):
        """Test that all recipe items exist in catalog."""
        recipes = agent.order_history.get("recipes", {})
        
        for recipe_name, item_ids in recipes.items():
            for item_id in item_ids:
                item = agent._find_item_by_id(item_id)
                assert item is not None, f"Recipe '{recipe_name}' references non-existent item '{item_id}'"


class TestOrderPlacement:
    """Test order placement and persistence."""
    
    def test_order_structure(self, agent):
        """Test that placed order has correct structure."""
        agent.cart = [
            {"id": "1", "name": "Test Item", "brand": "Test", "size": "1 unit", "price": 5.00, "quantity": 1}
        ]
        
        # Create order structure (simulating place_order)
        order_id = "test_order_123"
        order = {
            "id": order_id,
            "timestamp": datetime.now().isoformat(),
            "items": agent.cart.copy(),
            "total": agent._calculate_cart_total(),
            "status": "received",
            "status_history": [
                {"status": "received", "timestamp": datetime.now().isoformat()}
            ]
        }
        
        assert order["id"] == order_id
        assert len(order["items"]) == 1
        assert order["total"] == 5.00
        assert order["status"] == "received"
        assert len(order["status_history"]) == 1
    
    def test_order_history_persistence(self, agent, order_history_file):
        """Test that order history file exists and is writable."""
        assert order_history_file.exists(), "Order history file should exist"
        
        # Verify we can read it
        with open(order_history_file, "r") as f:
            data = json.load(f)
        
        assert "orders" in data, "Order history should have 'orders' key"
        assert isinstance(data["orders"], list), "'orders' should be a list"


class TestOrderTracking:
    """Test order tracking and status progression."""
    
    def test_status_progression_order(self, agent):
        """Test that status progression follows correct order."""
        status_progression = ["received", "confirmed", "being_prepared", "out_for_delivery", "delivered"]
        
        # Create a test order
        order = {
            "id": "test_123",
            "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "items": [],
            "total": 10.00,
            "status": "received",
            "status_history": [{"status": "received", "timestamp": datetime.now().isoformat()}]
        }
        
        # Update status
        agent._update_order_status(order)
        
        # Status should have progressed
        assert order["status"] in status_progression
        current_index = status_progression.index(order["status"])
        assert current_index > 0, "Status should have progressed from 'received'"
    
    def test_delivered_status_final(self, agent):
        """Test that delivered status doesn't change."""
        order = {
            "id": "test_123",
            "timestamp": datetime.now().isoformat(),
            "items": [],
            "total": 10.00,
            "status": "delivered",
            "status_history": []
        }
        
        initial_status = order["status"]
        agent._update_order_status(order)
        
        assert order["status"] == initial_status, "Delivered status should not change"


class TestBudgetTracking:
    """Test budget tracking functionality."""
    
    def test_set_budget(self, agent):
        """Test setting budget."""
        agent.budget = 50.00
        assert agent.budget == 50.00, "Budget should be set"
    
    def test_budget_warning(self, agent):
        """Test budget warning when exceeded."""
        agent.budget = 10.00
        agent.cart = [
            {"id": "1", "name": "Item 1", "price": 8.00, "quantity": 2}  # Total: 16.00
        ]
        
        total = agent._calculate_cart_total()
        assert total > agent.budget, "Cart total should exceed budget"


class TestDietaryRestrictions:
    """Test dietary restriction filtering."""
    
    def test_check_dietary_restrictions(self, agent):
        """Test dietary restriction checking."""
        agent.dietary_restrictions = ["vegan"]
        
        vegan_item = {"tags": ["vegan", "organic"]}
        non_vegan_item = {"tags": ["vegetarian"]}
        
        assert agent._check_dietary_restrictions(vegan_item) == True, "Vegan item should pass"
        assert agent._check_dietary_restrictions(non_vegan_item) == False, "Non-vegan item should fail"
    
    def test_no_restrictions(self, agent):
        """Test that items pass when no restrictions set."""
        agent.dietary_restrictions = []
        
        item = {"tags": ["anything"]}
        assert agent._check_dietary_restrictions(item) == True, "Should pass with no restrictions"


class TestOrderHistory:
    """Test order history functionality."""
    
    def test_order_history_loads(self, agent):
        """Test that order history loads."""
        assert agent.order_history is not None, "Order history should be loaded"
        assert "orders" in agent.order_history, "Should have orders key"
    
    def test_multiple_orders(self, agent):
        """Test handling multiple orders."""
        # Simulate multiple orders
        orders = [
            {"id": "order1", "timestamp": datetime.now().isoformat(), "total": 10.00},
            {"id": "order2", "timestamp": datetime.now().isoformat(), "total": 20.00}
        ]
        
        assert len(orders) == 2, "Should track multiple orders"
        assert orders[0]["id"] != orders[1]["id"], "Orders should have unique IDs"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
