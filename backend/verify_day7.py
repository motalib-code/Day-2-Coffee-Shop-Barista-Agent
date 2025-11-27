"""
Quick verification script for Day 7 - Food & Grocery Ordering Agent

This script verifies that:
1. All required files exist
2. Catalog is properly formatted
3. Order history is initialized
4. Agent can be imported
5. All tools are properly defined
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_success(msg: str):
    print(f"{GREEN}✓{RESET} {msg}")


def print_error(msg: str):
    print(f"{RED}✗{RESET} {msg}")


def print_warning(msg: str):
    print(f"{YELLOW}⚠{RESET} {msg}")


def print_info(msg: str):
    print(f"{BLUE}ℹ{RESET} {msg}")


def verify_file_exists(file_path: Path, description: str) -> bool:
    """Verify a file exists."""
    if file_path.exists():
        print_success(f"{description} exists: {file_path.name}")
        return True
    else:
        print_error(f"{description} not found: {file_path}")
        return False


def verify_catalog(catalog_path: Path) -> bool:
    """Verify catalog structure."""
    try:
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
        
        if not isinstance(catalog, list):
            print_error("Catalog should be a list")
            return False
        
        if len(catalog) < 20:
            print_warning(f"Catalog has only {len(catalog)} items (recommended: 20+)")
        else:
            print_success(f"Catalog has {len(catalog)} items")
        
        # Check structure of first item
        required_fields = ["id", "name", "category", "price", "brand", "size", "in_stock"]
        if catalog:
            item = catalog[0]
            missing = [f for f in required_fields if f not in item]
            if missing:
                print_error(f"Catalog items missing fields: {missing}")
                return False
            else:
                print_success("Catalog structure is valid")
        
        # Check for tags
        tagged_items = [i for i in catalog if "tags" in i and i["tags"]]
        print_info(f"  {len(tagged_items)}/{len(catalog)} items have dietary tags")
        
        return True
    
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in catalog: {e}")
        return False
    except Exception as e:
        print_error(f"Error reading catalog: {e}")
        return False


def verify_order_history(history_path: Path) -> bool:
    """Verify order history structure."""
    try:
        with open(history_path, "r") as f:
            history = json.load(f)
        
        if not isinstance(history, dict):
            print_error("Order history should be a dict")
            return False
        
        if "orders" not in history:
            print_error("Order history missing 'orders' key")
            return False
        
        if "recipes" not in history:
            print_warning("Order history missing 'recipes' key")
        else:
            recipes = history["recipes"]
            print_success(f"Order history has {len(recipes)} recipe mappings")
            for recipe_name in list(recipes.keys())[:3]:
                print_info(f"  Recipe: '{recipe_name}' → {len(recipes[recipe_name])} items")
        
        num_orders = len(history["orders"])
        if num_orders == 0:
            print_info("Order history is empty (expected for new installation)")
        else:
            print_success(f"Order history contains {num_orders} order(s)")
        
        return True
    
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in order history: {e}")
        return False
    except Exception as e:
        print_error(f"Error reading order history: {e}")
        return False


def verify_agent_code(agent_path: Path) -> bool:
    """Verify agent code can be imported."""
    try:
        # Add src to path
        sys.path.insert(0, str(agent_path.parent))
        
        # Try to import
        from day7_agent import FoodGroceryAgent
        
        print_success("Agent code imports successfully")
        
        # Check for required tools
        agent_class = FoodGroceryAgent
        tools = []
        
        # Get all methods with function_tool decorator
        for attr_name in dir(agent_class):
            attr = getattr(agent_class, attr_name)
            if callable(attr) and hasattr(attr, "__wrapped__"):
                tools.append(attr_name)
        
        if len(tools) > 0:
            print_success(f"Agent has {len(tools)} function tools")
            for tool in sorted(tools):
                print_info(f"  - {tool}")
        else:
            print_warning("No function tools detected (may be normal)")
        
        return True
    
    except ImportError as e:
        print_error(f"Cannot import agent: {e}")
        return False
    except Exception as e:
        print_error(f"Error verifying agent code: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("Day 7 - Food & Grocery Ordering Agent - Verification")
    print("=" * 60 + "\n")
    
    # Get paths
    backend_dir = Path(__file__).parent
    catalog_path = backend_dir / "catalog.json"
    history_path = backend_dir / "order_history.json"
    agent_path = backend_dir / "src" / "day7_agent.py"
    
    all_passed = True
    
    # 1. Check files exist
    print_info("Checking required files...")
    all_passed &= verify_file_exists(catalog_path, "Catalog file")
    all_passed &= verify_file_exists(history_path, "Order history file")
    all_passed &= verify_file_exists(agent_path, "Agent code")
    print()
    
    # 2. Verify catalog
    if catalog_path.exists():
        print_info("Verifying catalog...")
        all_passed &= verify_catalog(catalog_path)
        print()
    
    # 3. Verify order history
    if history_path.exists():
        print_info("Verifying order history...")
        all_passed &= verify_order_history(history_path)
        print()
    
    # 4. Verify agent code
    if agent_path.exists():
        print_info("Verifying agent code...")
        all_passed &= verify_agent_code(agent_path)
        print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print_success("All verifications passed! ✨")
        print_info("You can now run the agent with:")
        print_info("  cd backend")
        print_info("  uv run python src/day7_agent.py dev")
    else:
        print_error("Some verifications failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
