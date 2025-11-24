import json
import os
from datetime import datetime
from typing import List, Dict, Any


def _ensure_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _get_wellness_file_path():
    """Get the full path to wellness_log.json"""
    data_dir = _ensure_data_directory()
    return os.path.join(data_dir, "wellness_log.json")


def load_wellness_log() -> List[Dict[str, Any]]:
    """Load wellness log entries from JSON file"""
    try:
        filepath = _get_wellness_file_path()
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError, Exception):
        # If file is corrupted or any error occurs, return empty list
        return []


def save_wellness_entry(entry: Dict[str, Any]) -> bool:
    """Save a wellness entry to the log"""
    try:
        # Validate entry structure
        required_fields = ["mood", "energy", "stressors", "goals", "summary"]
        if not all(field in entry for field in required_fields):
            return False
        
        # Add timestamp if not present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
        
        # Load existing entries
        entries = load_wellness_log()
        
        # Append new entry
        entries.append(entry)
        
        # Save back to file
        filepath = _get_wellness_file_path()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception:
        return False