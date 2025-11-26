"""Utility functions for the Teach-the-Tutor agent system."""

import json
import logging
import random
from pathlib import Path
from typing import Any

logger = logging.getLogger("tutor_utils")

# Path to content file
CONTENT_FILE = Path(__file__).parent.parent / "shared-data" / "day4_tutor_content.json"


def load_concepts() -> list[dict[str, Any]]:
    """Load all learning concepts from the JSON file.
    
    Returns:
        List of concept dictionaries
    """
    if not CONTENT_FILE.exists():
        logger.error(f"Content file not found: {CONTENT_FILE}")
        return []
    
    try:
        with open(CONTENT_FILE) as f:
            concepts = json.load(f)
        logger.info(f"Loaded {len(concepts)} concepts")
        return concepts
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse content file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading concepts: {e}")
        return []


def get_concept_by_id(concept_id: str) -> dict[str, Any] | None:
    """Get a specific concept by its ID.
    
    Args:
        concept_id: The ID of the concept to retrieve
    
    Returns:
        Concept dictionary or None if not found
    """
    concepts = load_concepts()
    for concept in concepts:
        if concept.get("id") == concept_id:
            return concept
    
    logger.warning(f"Concept not found: {concept_id}")
    return None


def get_random_concept() -> dict[str, Any] | None:
    """Get a random concept from the content file.
    
    Returns:
        Random concept dictionary or None if no concepts available
    """
    concepts = load_concepts()
    if not concepts:
        return None
    return random.choice(concepts)


def get_concepts_by_difficulty(difficulty: str) -> list[dict[str, Any]]:
    """Get all concepts of a specific difficulty level.
    
    Args:
        difficulty: The difficulty level (beginner, intermediate, advanced)
    
    Returns:
        List of matching concepts
    """
    concepts = load_concepts()
    return [c for c in concepts if c.get("difficulty") == difficulty]


def format_concept_for_learning(concept: dict[str, Any]) -> str:
    """Format a concept for the Learn mode explanation.
    
    Args:
        concept: The concept dictionary
    
    Returns:
        Formatted explanation text for voice output
    """
    title = concept.get("title", "Unknown Topic")
    summary = concept.get("summary", "")
    key_points = concept.get("key_points", [])
    
    explanation = f"Let me explain {title}. {summary}"
    
    if key_points:
        explanation += "\n\nThe key points to remember are: "
        explanation += ", ".join(key_points)
    
    return explanation


def format_concept_for_quiz(concept: dict[str, Any]) -> str:
    """Format a concept for the Quiz mode question.
    
    Args:
        concept: The concept dictionary
    
    Returns:
        Quiz question text for voice output
    """
    title = concept.get("title", "this topic")
    question = concept.get("sample_question", f"Can you tell me about {title}?")
    
    return f"Here's a question about {title}: {question}"


def format_concept_for_teachback(concept: dict[str, Any]) -> str:
    """Format a concept for the Teach-Back mode prompt.
    
    Args:
        concept: The concept dictionary
    
    Returns:
        Teach-back prompt text for voice output
    """
    title = concept.get("title", "this topic")
    
    return f"Now it's your turn to be the teacher! Can you explain {title} to me in your own words? Pretend I'm a beginner who's never heard of this concept before."


def get_concept_list_text() -> str:
    """Get a voice-friendly list of all available concepts.
    
    Returns:
        Text listing all concepts
    """
    concepts = load_concepts()
    if not concepts:
        return "No concepts available."
    
    concept_titles = [c.get("title", "Unknown") for c in concepts]
    
    if len(concept_titles) == 1:
        return f"I can teach you about {concept_titles[0]}."
    elif len(concept_titles) == 2:
        return f"I can teach you about {concept_titles[0]} or {concept_titles[1]}."
    else:
        last = concept_titles[-1]
        others = ", ".join(concept_titles[:-1])
        return f"I can teach you about {others}, or {last}."


def find_concept_by_keyword(keyword: str) -> dict[str, Any] | None:
    """Find a concept by searching for a keyword in title or ID.
    
    Args:
        keyword: Search term (case-insensitive)
    
    Returns:
        Matching concept or None
    """
    concepts = load_concepts()
    keyword_lower = keyword.lower()
    
    # First try exact ID match
    for concept in concepts:
        if concept.get("id", "").lower() == keyword_lower:
            return concept
    
    # Then try title match
    for concept in concepts:
        title = concept.get("title", "").lower()
        if keyword_lower in title:
            return concept
    
    return None
