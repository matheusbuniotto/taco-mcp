"""Database operations for TACO data."""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional
import yaml

from .normalize import normalize_query, parse_br_number, round_macro
from .schemas import (
    CalculateMacrosOutput, CalculatedMacros,
    CalculateMealMacrosOutput, GetFoodOutput,
    MacroPer100g, MealItemInput, MealItemOutput,
    MealTotal, SearchFoodOutput, FoodResult
)


class TacoDB:
    """TACO database wrapper."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._aliases: dict = {}
        self._load_aliases()
    
    def _load_aliases(self):
        """Load aliases from YAML file."""
        aliases_path = Path(__file__).parent.parent.parent / "data" / "aliases.yaml"
        if aliases_path.exists():
            with open(aliases_path, 'r', encoding='utf-8') as f:
                self._aliases = yaml.safe_load(f) or {}
        else:
            self._aliases = {}
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _row_to_macros(self, row: sqlite3.Row) -> MacroPer100g:
        """Convert row to MacroPer100g."""
        return MacroPer100g(
            kcal=row['kcal_per_100g'],
            protein_g=row['protein_g_per_100g'],
            carbs_g=row['carbs_g_per_100g'],
            fat_g=row['fat_g_per_100g'],
            fiber_g=row['fiber_g_per_100g'],
            sodium_mg=row['sodium_mg_per_100g']
        )
    
    def search_food(self, query: str, limit: int = 5) -> SearchFoodOutput:
        """Search for foods by name."""
        normalized = normalize_query(query)
        results: List[FoodResult] = []
        
        conn = self._get_connection()
        try:
            # Check aliases first
            alias_id = self._aliases.get(normalized.lower())
            if alias_id:
                cursor = conn.execute(
                    """SELECT id, source_id, category, description,
                              kcal_per_100g, protein_g_per_100g, fat_g_per_100g,
                              carbs_g_per_100g, fiber_g_per_100g, sodium_mg_per_100g
                       FROM foods WHERE id = ?""",
                    (alias_id,)
                )
                row = cursor.fetchone()
                if row:
                    results.append(FoodResult(
                        food_id=row['id'],
                        description=row['description'],
                        category=row['category'],
                        per_100g=self._row_to_macros(row),
                        match_reason='alias',
                        confidence=1.0
                    ))
            
            # FTS search
            if len(results) < limit:
                cursor = conn.execute(
                    """SELECT foods.id, foods.source_id, foods.category, foods.description,
                              foods.kcal_per_100g, foods.protein_g_per_100g, foods.fat_g_per_100g,
                              foods.carbs_g_per_100g, foods.fiber_g_per_100g, foods.sodium_mg_per_100g,
                              rank
                       FROM foods_fts
                       JOIN foods ON foods_fts.rowid = foods.id
                       WHERE foods_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (normalized, limit - len(results))
                )
                for row in cursor:
                    # Skip if already added via alias
                    if any(r.food_id == row['id'] for r in results):
                        continue
                    results.append(FoodResult(
                        food_id=row['id'],
                        description=row['description'],
                        category=row['category'],
                        per_100g=self._row_to_macros(row),
                        match_reason='fts',
                        confidence=1.0 / (1 + abs(row['rank']))
                    ))
        finally:
            conn.close()
        
        return SearchFoodOutput(
            query=query,
            normalized_query=normalized,
            results=results
        )
    
    def get_food(self, food_id: int) -> Optional[GetFoodOutput]:
        """Get food by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, source_id, category, description,
                          kcal_per_100g, protein_g_per_100g, fat_g_per_100g,
                          carbs_g_per_100g, fiber_g_per_100g, sodium_mg_per_100g
                   FROM foods WHERE id = ?""",
                (food_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return GetFoodOutput(
                food_id=row['id'],
                description=row['description'],
                category=row['category'],
                per_100g=self._row_to_macros(row)
            )
        finally:
            conn.close()
    
    def calculate_macros(self, food_id: int, grams: float) -> Optional[CalculateMacrosOutput]:
        """Calculate macros for specific gram amount."""
        food = self.get_food(food_id)
        if not food:
            return None
        
        per_100g = food.per_100g
        factor = grams / 100.0
        
        def calc(val):
            return round_macro(val * factor, decimals=2) if val is not None else None
        
        macros = CalculatedMacros(
            kcal=calc(per_100g.kcal),
            protein_g=calc(per_100g.protein_g),
            carbs_g=calc(per_100g.carbs_g),
            fat_g=calc(per_100g.fat_g),
            fiber_g=calc(per_100g.fiber_g),
            sodium_mg=calc(per_100g.sodium_mg)
        )
        
        return CalculateMacrosOutput(
            food_id=food_id,
            description=food.description,
            grams=grams,
            macros=macros
        )
    
    def calculate_meal_macros(
        self, items: List[MealItemInput]
    ) -> CalculateMealMacrosOutput:
        """Calculate total macros for a meal."""
        meal_items: List[MealItemOutput] = []
        warnings: List[str] = []
        total = MealTotal()
        
        for item in items:
            result = self.calculate_macros(item.food_id, item.grams)
            if not result:
                warnings.append(f"Food ID {item.food_id} not found")
                continue
            
            meal_items.append(MealItemOutput(
                food_id=result.food_id,
                description=result.description,
                grams=result.grams,
                macros=result.macros
            ))
            
            m = result.macros
            if m.kcal:
                total.kcal += m.kcal
            if m.protein_g:
                total.protein_g += m.protein_g
            if m.carbs_g:
                total.carbs_g += m.carbs_g
            if m.fat_g:
                total.fat_g += m.fat_g
            if m.fiber_g:
                total.fiber_g += m.fiber_g
            if m.sodium_mg:
                total.sodium_mg += m.sodium_mg
        
        # Round totals
        total.kcal = round(total.kcal, 1)
        total.protein_g = round(total.protein_g, 2)
        total.carbs_g = round(total.carbs_g, 2)
        total.fat_g = round(total.fat_g, 2)
        total.fiber_g = round(total.fiber_g, 2)
        total.sodium_mg = round(total.sodium_mg, 2)
        
        return CalculateMealMacrosOutput(
            source="TACO",
            items=meal_items,
            total=total,
            warnings=warnings
        )
    
    # ========== Custom Foods ==========
    
    def _init_custom_foods_table(self):
        """Initialize custom foods table if not exists."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_foods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT DEFAULT 'Custom',
                    kcal_per_100g REAL,
                    protein_g_per_100g REAL,
                    fat_g_per_100g REAL,
                    carbs_g_per_100g REAL,
                    fiber_g_per_100g REAL,
                    sodium_mg_per_100g REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS custom_foods_fts USING fts5(
                    name,
                    content='custom_foods',
                    content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    def add_custom_food(
        self,
        name: str,
        kcal_per_100g: float,
        protein_g_per_100g: float = 0,
        fat_g_per_100g: float = 0,
        carbs_g_per_100g: float = 0,
        fiber_g_per_100g: float = 0,
        sodium_mg_per_100g: float = 0,
        category: str = "Custom",
        notes: str = ""
    ) -> int:
        """Add a custom food. Returns the new food ID."""
        self._init_custom_foods_table()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO custom_foods
                (name, category, kcal_per_100g, protein_g_per_100g, fat_g_per_100g,
                 carbs_g_per_100g, fiber_g_per_100g, sodium_mg_per_100g, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, category, kcal_per_100g, protein_g_per_100g, fat_g_per_100g,
                  carbs_g_per_100g, fiber_g_per_100g, sodium_mg_per_100g, notes))
            
            food_id = cursor.lastrowid
            
            # Add to FTS index
            conn.execute(
                "INSERT INTO custom_foods_fts(rowid, name) VALUES (?, ?)",
                (food_id, name)
            )
            
            conn.commit()
            return food_id
        finally:
            conn.close()
    
    def list_custom_foods(self, limit: int = 50) -> List[dict]:
        """List all custom foods."""
        self._init_custom_foods_table()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, name, category, kcal_per_100g, protein_g_per_100g,
                          fat_g_per_100g, carbs_g_per_100g, fiber_g_per_100g,
                          sodium_mg_per_100g, notes, created_at
                   FROM custom_foods
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def delete_custom_food(self, food_id: int) -> bool:
        """Delete a custom food. Returns True if deleted."""
        self._init_custom_foods_table()
        
        conn = self._get_connection()
        try:
            # Delete from FTS first
            conn.execute("DELETE FROM custom_foods_fts WHERE rowid = ?", (food_id,))
            
            # Delete from main table
            cursor = conn.execute("DELETE FROM custom_foods WHERE id = ?", (food_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_custom_food(self, food_id: int) -> Optional[GetFoodOutput]:
        """Get custom food by ID."""
        self._init_custom_foods_table()
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT id, name, category, kcal_per_100g, protein_g_per_100g,
                          fat_g_per_100g, carbs_g_per_100g, fiber_g_per_100g, sodium_mg_per_100g
                   FROM custom_foods WHERE id = ?""",
                (food_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return GetFoodOutput(
                food_id=row['id'],
                description=row['name'],
                category=row['category'],
                per_100g=MacroPer100g(
                    kcal=row['kcal_per_100g'],
                    protein_g=row['protein_g_per_100g'],
                    fat_g=row['fat_g_per_100g'],
                    carbs_g=row['carbs_g_per_100g'],
                    fiber_g=row['fiber_g_per_100g'],
                    sodium_mg=row['sodium_mg_per_100g']
                )
            )
        finally:
            conn.close()
    
    def search_custom_foods(self, query: str, limit: int = 5, id_offset: int = 0) -> List[FoodResult]:
        """Search custom foods."""
        self._init_custom_foods_table()
        
        normalized = normalize_query(query)
        results: List[FoodResult] = []
        
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT custom_foods.id, custom_foods.name, custom_foods.category,
                          custom_foods.kcal_per_100g, custom_foods.protein_g_per_100g,
                          custom_foods.fat_g_per_100g, custom_foods.carbs_g_per_100g,
                          custom_foods.fiber_g_per_100g, custom_foods.sodium_mg_per_100g
                   FROM custom_foods_fts
                   JOIN custom_foods ON custom_foods_fts.rowid = custom_foods.id
                   WHERE custom_foods_fts MATCH ?
                   LIMIT ?""",
                (normalized, limit)
            )
            for row in cursor:
                results.append(FoodResult(
                    food_id=row['id'] + id_offset,  # Add offset
                    description=row['name'],
                    category=row['category'],
                    per_100g=MacroPer100g(
                        kcal=row['kcal_per_100g'],
                        protein_g=row['protein_g_per_100g'],
                        fat_g=row['fat_g_per_100g'],
                        carbs_g=row['carbs_g_per_100g'],
                        fiber_g=row['fiber_g_per_100g'],
                        sodium_mg=row['sodium_mg_per_100g']
                    ),
                    match_reason='custom',
                    confidence=1.0
                ))
        finally:
            conn.close()
        
        return results
