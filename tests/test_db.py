"""Tests for database operations."""

import pytest
from pathlib import Path

from taco_mcp.db import TacoDB
from taco_mcp.schemas import MealItemInput


def get_db():
    """Get database instance for tests."""
    db_path = Path(__file__).parent.parent / "data" / "processed" / "taco.sqlite"
    if not db_path.exists():
        pytest.skip("Database not built. Run scripts/build_db.py first.")
    return TacoDB(db_path)


def test_search_food_returns_results():
    db = get_db()
    result = db.search_food("arroz", limit=5)
    assert len(result.results) > 0
    assert any("Arroz" in r.description for r in result.results)


def test_search_food_alias():
    db = get_db()
    result = db.search_food("arroz")
    # Should match alias first
    assert result.results[0].match_reason == "alias"
    assert result.results[0].food_id == 3  # arroz branco cozido


def test_get_food_exists():
    db = get_db()
    food = db.get_food(3)
    assert food is not None
    assert "Arroz" in food.description
    assert food.per_100g.kcal is not None


def test_get_food_not_exists():
    db = get_db()
    food = db.get_food(99999)
    assert food is None


def test_calculate_macros():
    db = get_db()
    result = db.calculate_macros(3, 150)
    assert result is not None
    assert result.grams == 150
    assert result.macros.kcal is not None
    # 128 kcal/100g * 1.5 = 192 kcal
    assert result.macros.kcal == pytest.approx(192.0)


def test_calculate_meal_macros():
    db = get_db()
    meal = db.calculate_meal_macros([
        MealItemInput(food_id=3, grams=150),  # arroz
        MealItemInput(food_id=410, grams=100),  # frango
    ])
    
    assert len(meal.items) == 2
    assert meal.total.kcal > 0
    assert meal.total.protein_g > 0
    assert meal.total.carbs_g > 0
