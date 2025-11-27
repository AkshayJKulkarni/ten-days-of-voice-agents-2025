import json
import os
from typing import Dict, List, Any, Tuple


def load_faq_data() -> Tuple[str, str, str, List[Dict[str, str]]]:
    """Load FAQ data from JSON file
    
    Returns:
        Tuple of (company_name, description, pricing, faq_list)
    """
    try:
        faq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "day5_company_faq.json")
        with open(faq_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return (
            data.get("company", ""),
            data.get("description", ""),
            data.get("pricing", ""),
            data.get("faq", [])
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return ("", "", "", [])