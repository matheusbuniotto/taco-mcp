"""Normalization utilities for PT-BR food names and numbers."""

import re
import unicodedata
from typing import Optional


def remove_accents(text: str) -> str:
    """Remove accents from text."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_query(text: str) -> str:
    """
    Normalize food query for search.
    - Lowercase
    - Remove accents
    - Remove extra spaces
    - Remove weak words
    """
    text = text.lower().strip()
    text = remove_accents(text)
    text = re.sub(r'\s+', ' ', text)
    
    # Weak words to remove
    weak_words = {'de', 'com', 'sem', 'tipo', 'pronto', 'a', 'o', 'e', 'da', 'do'}
    words = [w for w in text.split() if w not in weak_words]
    
    return ' '.join(words)


def parse_br_number(value: str) -> Optional[float]:
    """
    Parse Brazilian number format from CSV.
    Examples:
        "2,6" -> 2.6
        "124" -> 124.0
        "NA" -> None
        "" -> None
        "Tr" -> 0.0 (trace amount)
    """
    if value is None:
        return None
    
    value = value.strip()
    
    if value in ('NA', '', 'Tr'):
        return None if value in ('NA', '') else 0.0
    
    # Replace comma with dot for decimal
    value = value.replace(',', '.')
    
    try:
        return float(value)
    except ValueError:
        return None


def round_macro(value: Optional[float], decimals: int = 2) -> Optional[float]:
    """Round macro value safely."""
    if value is None:
        return None
    return round(value, decimals)
