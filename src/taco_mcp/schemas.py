"""Pydantic schemas for MCP tool inputs/outputs."""

from typing import List, Optional
from pydantic import BaseModel


class MacroPer100g(BaseModel):
    """Macros per 100g of food."""
    kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class FoodResult(BaseModel):
    """Single food search result."""
    food_id: int
    description: str
    category: str
    per_100g: MacroPer100g
    match_reason: str = "fts"  # fts, alias, exact
    confidence: float = 1.0


class SearchFoodInput(BaseModel):
    """Input for search_food tool."""
    query: str
    limit: int = 5


class SearchFoodOutput(BaseModel):
    """Output for search_food tool."""
    query: str
    normalized_query: str
    results: List[FoodResult]


class GetFoodInput(BaseModel):
    """Input for get_food tool."""
    food_id: int


class GetFoodOutput(BaseModel):
    """Output for get_food tool."""
    food_id: int
    description: str
    category: str
    per_100g: MacroPer100g


class CalculatedMacros(BaseModel):
    """Macros calculated for specific gram amount."""
    kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class CalculateMacrosInput(BaseModel):
    """Input for calculate_macros tool."""
    food_id: int
    grams: float


class CalculateMacrosOutput(BaseModel):
    """Output for calculate_macros tool."""
    food_id: int
    description: str
    grams: float
    macros: CalculatedMacros


class MealItemInput(BaseModel):
    """Single item in meal calculation."""
    food_id: int
    grams: float


class MealItemOutput(BaseModel):
    """Single item result in meal calculation."""
    food_id: int
    description: str
    grams: float
    macros: CalculatedMacros


class CalculateMealMacrosInput(BaseModel):
    """Input for calculate_meal_macros tool."""
    items: List[MealItemInput]


class MealTotal(BaseModel):
    """Total macros for meal."""
    kcal: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0


class CalculateMealMacrosOutput(BaseModel):
    """Output for calculate_meal_macros tool."""
    source: str = "TACO"
    items: List[MealItemOutput]
    total: MealTotal
    warnings: List[str] = []
