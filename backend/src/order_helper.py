import json
import os
from datetime import datetime


def save_order_to_json(order: dict) -> str:
    """Save order to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"order_{timestamp}.json"
    
    orders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "orders")
    os.makedirs(orders_dir, exist_ok=True)
    
    filepath = os.path.join(orders_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(order, f, indent=2, ensure_ascii=False)
    
    return filepath


def is_order_complete(order: dict) -> bool:
    """Check if all required order fields are filled"""
    return all([
        order.get("drinkType", "").strip(),
        order.get("size", "").strip(),
        order.get("milk", "").strip(),
        order.get("name", "").strip()
    ])