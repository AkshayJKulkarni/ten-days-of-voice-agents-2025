import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# Product catalog
PRODUCTS = [
    {
        "id": "mug-001",
        "name": "Stoneware Coffee Mug",
        "description": "Handcrafted ceramic mug perfect for your morning coffee",
        "price": 800,
        "currency": "INR",
        "category": "mug",
        "color": "white",
        "size": "350ml"
    },
    {
        "id": "mug-002", 
        "name": "Blue Ceramic Mug",
        "description": "Beautiful blue glazed ceramic mug",
        "price": 650,
        "currency": "INR",
        "category": "mug",
        "color": "blue",
        "size": "300ml"
    },
    {
        "id": "tshirt-001",
        "name": "Cotton T-Shirt",
        "description": "Comfortable 100% cotton t-shirt",
        "price": 1200,
        "currency": "INR",
        "category": "clothing",
        "color": "black",
        "size": "M"
    },
    {
        "id": "hoodie-001",
        "name": "Black Hoodie",
        "description": "Warm and cozy black hoodie",
        "price": 2500,
        "currency": "INR",
        "category": "clothing",
        "color": "black",
        "size": "L"
    },
    {
        "id": "hoodie-002",
        "name": "Gray Hoodie",
        "description": "Comfortable gray pullover hoodie",
        "price": 2200,
        "currency": "INR",
        "category": "clothing",
        "color": "gray",
        "size": "M"
    }
]

# In-memory orders storage
ORDERS = []

def list_products(filters: Optional[Dict] = None) -> List[Dict]:
    """List products with optional filtering"""
    if not filters:
        return PRODUCTS
    
    filtered = PRODUCTS
    
    if "category" in filters:
        filtered = [p for p in filtered if p["category"] == filters["category"]]
    
    if "max_price" in filters:
        filtered = [p for p in filtered if p["price"] <= filters["max_price"]]
    
    if "color" in filters:
        filtered = [p for p in filtered if p["color"] == filters["color"]]
    
    if "name_contains" in filters:
        search_term = filters["name_contains"].lower()
        filtered = [p for p in filtered if search_term in p["name"].lower()]
    
    return filtered

def get_product_by_id(product_id: str) -> Optional[Dict]:
    """Get a specific product by ID"""
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    return None

def create_order(line_items: List[Dict]) -> Dict:
    """Create an order from line items
    
    Args:
        line_items: [{"product_id": "...", "quantity": 1}, ...]
    
    Returns:
        Order dictionary
    """
    order_id = str(uuid.uuid4())[:8]
    total = 0
    order_items = []
    
    for item in line_items:
        product = get_product_by_id(item["product_id"])
        if product:
            quantity = item.get("quantity", 1)
            item_total = product["price"] * quantity
            total += item_total
            
            order_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": item_total,
                "currency": product["currency"]
            })
    
    order = {
        "id": order_id,
        "items": order_items,
        "total": total,
        "currency": "INR",
        "status": "CONFIRMED",
        "created_at": datetime.now().isoformat()
    }
    
    ORDERS.append(order)
    save_orders_to_file()
    return order

def get_last_order() -> Optional[Dict]:
    """Get the most recent order"""
    return ORDERS[-1] if ORDERS else None

def get_all_orders() -> List[Dict]:
    """Get all orders"""
    return ORDERS

def save_orders_to_file():
    """Save orders to JSON file"""
    orders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(orders_dir, exist_ok=True)
    
    filepath = os.path.join(orders_dir, "ecommerce_orders.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ORDERS, f, indent=2, ensure_ascii=False)

def load_orders_from_file():
    """Load orders from JSON file"""
    global ORDERS
    orders_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    filepath = os.path.join(orders_dir, "ecommerce_orders.json")
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                ORDERS = json.load(f)
    except (json.JSONDecodeError, IOError):
        ORDERS = []

# Load existing orders on import
load_orders_from_file()