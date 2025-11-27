"""
Display catalog items by category for Day 7 agent
"""

import json
from pathlib import Path
from collections import defaultdict

def display_catalog():
    catalog_path = Path(__file__).parent / "catalog.json"
    
    try:
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
        
        # Group by category
        by_category = defaultdict(list)
        for item in catalog:
            by_category[item["category"]].append(item)
        
        print("\n" + "=" * 70)
        print("FRESHMART PRODUCT CATALOG")
        print("=" * 70 + "\n")
        
        for category in sorted(by_category.keys()):
            items = by_category[category]
            print(f"\n📦 {category.upper()} ({len(items)} items)")
            print("-" * 70)
            
            for item in sorted(items, key=lambda x: x["name"]):
                tags_str = ""
                if item.get("tags"):
                    tags_str = f" [{', '.join(item['tags'])}]"
                
                stock_status = "✓" if item.get("in_stock", False) else "✗"
                
                print(f"  {stock_status} {item['name']}")
                print(f"     {item['brand']} | {item['size']} | ${item['price']}{tags_str}")
        
        print("\n" + "=" * 70)
        print(f"Total Items: {len(catalog)}")
        
        # Count tags
        all_tags = set()
        for item in catalog:
            all_tags.update(item.get("tags", []))
        
        print(f"Dietary Tags: {', '.join(sorted(all_tags))}")
        print("=" * 70 + "\n")
        
        # Show recipes
        history_path = Path(__file__).parent / "order_history.json"
        if history_path.exists():
            with open(history_path, "r") as f:
                history = json.load(f)
            
            recipes = history.get("recipes", {})
            if recipes:
                print("\n" + "=" * 70)
                print("AVAILABLE RECIPES")
                print("=" * 70 + "\n")
                
                for recipe_name, item_ids in sorted(recipes.items()):
                    print(f"🍽️  '{recipe_name}'")
                    items_in_recipe = []
                    for item_id in item_ids:
                        for item in catalog:
                            if item["id"] == item_id:
                                items_in_recipe.append(item["name"])
                                break
                    
                    for item_name in items_in_recipe:
                        print(f"     - {item_name}")
                    print()
                
                print("=" * 70 + "\n")
    
    except FileNotFoundError:
        print("❌ Catalog file not found. Please run from backend directory.")
    except json.JSONDecodeError:
        print("❌ Invalid JSON in catalog file")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    display_catalog()
