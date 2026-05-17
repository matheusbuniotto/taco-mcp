#!/usr/bin/env python3
"""Build SQLite database from TACO CSV."""

import csv
import sqlite3
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from taco_mcp.normalize import parse_br_number


def build_database():
    """Build SQLite database from TACO CSV."""
    data_dir = Path(__file__).parent.parent / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = raw_dir / "alimentos.csv"
    if not csv_path.exists():
        print("CSV not found. Run download_taco.py first.")
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    db_path = processed_dir / "taco.sqlite"
    
    # Remove existing db
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE foods (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            kcal_per_100g REAL,
            protein_g_per_100g REAL,
            fat_g_per_100g REAL,
            carbs_g_per_100g REAL,
            fiber_g_per_100g REAL,
            sodium_mg_per_100g REAL,
            raw_json TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE VIRTUAL TABLE foods_fts USING fts5(
            description,
            category,
            content='foods',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        )
    """)
    
    # Read and insert data
    print("Reading CSV...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)
    
    print(f"Found {len(rows)} foods")
    
    # Column mapping
    col_map = {
        'id': 'Número do Alimento',
        'category': 'Categoria do alimento',
        'description': 'Descrição dos alimentos',
        'kcal': 'Energia (kcal)',
        'protein': 'Proteína (g)',
        'fat': 'Lipídeos (g)',
        'carbs': 'Carboidrato (g)',
        'fiber': 'Fibra Alimentar (g)',
        'sodium': 'Sódio (mg)',
    }
    
    for i, row in enumerate(rows, 1):
        source_id = int(row[col_map['id']])
        category = row[col_map['category']]
        description = row[col_map['description']]
        
        kcal = parse_br_number(row.get(col_map['kcal'], ''))
        protein = parse_br_number(row.get(col_map['protein'], ''))
        fat = parse_br_number(row.get(col_map['fat'], ''))
        carbs = parse_br_number(row.get(col_map['carbs'], ''))
        fiber = parse_br_number(row.get(col_map['fiber'], ''))
        sodium = parse_br_number(row.get(col_map['sodium'], ''))
        
        # Store raw row as JSON for future use
        import json
        raw_json = json.dumps(dict(row), ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO foods
            (id, source_id, category, description,
             kcal_per_100g, protein_g_per_100g, fat_g_per_100g,
             carbs_g_per_100g, fiber_g_per_100g, sodium_mg_per_100g,
             raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i, source_id, category, description,
            kcal, protein, fat, carbs, fiber, sodium,
            raw_json
        ))
    
    # Populate FTS index
    cursor.execute("INSERT INTO foods_fts(foods_fts) VALUES('rebuild')")
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM foods")
    count = cursor.fetchone()[0]
    print(f"Inserted {count} foods into database")
    
    cursor.execute("SELECT COUNT(*) FROM foods_fts")
    fts_count = cursor.fetchone()[0]
    print(f"FTS index has {fts_count} entries")
    
    conn.close()
    print(f"Database created at {db_path}")
    
    return db_path


if __name__ == "__main__":
    build_database()
