import json
import os
from typing import Dict, List, Optional, Any


def load_course_content() -> Dict[str, Any]:
    """Load course content from JSON file"""
    try:
        content_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "course_content.json")
        with open(content_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"concepts": []}


def select_concept(concept_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Select a concept by ID or return first available"""
    content = load_course_content()
    concepts = content.get("concepts", [])
    
    if not concepts:
        return None
    
    if concept_id:
        for concept in concepts:
            if concept.get("id") == concept_id:
                return concept
    
    return concepts[0]  # Return first concept if no ID specified


def get_available_concepts() -> List[str]:
    """Get list of available concept IDs"""
    content = load_course_content()
    return [concept.get("id", "") for concept in content.get("concepts", [])]