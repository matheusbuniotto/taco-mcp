#!/usr/bin/env python3
"""MCP server for TACO nutritional database."""

import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .db import TacoDB
from .schemas import (
    CalculateMacrosInput,
    CalculateMealMacrosInput,
    GetFoodInput,
    MealItemInput,
    SearchFoodInput,
    SearchFoodOutput,
)

# Find database path - check multiple locations
def find_db_path() -> Path:
    """Find database path, checking multiple locations."""
    # Try installed package first (when installed via pip)
    candidates = [
        Path(__file__).parent / "data" / "taco.sqlite",  # Installed package
        Path(__file__).parent.parent.parent / "data" / "processed" / "taco.sqlite",  # Dev
        Path.cwd() / "data" / "processed" / "taco.sqlite",  # CWD
        Path.home() / ".local" / "share" / "taco-mcp" / "taco.sqlite",  # User data
    ]
    for path in candidates:
        if path.exists():
            return path
    # Return first candidate even if not exists (for error message)
    return candidates[0]

DB_PATH = find_db_path()

# Initialize database
db = TacoDB(DB_PATH)

# Create MCP server
app = Server("taco-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_food",
            description="Search for foods in the TACO database by name. Returns multiple candidates with macros per 100g. Includes both official TACO foods and custom foods.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Food name to search for (Portuguese)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_food",
            description="Get detailed information about a specific food by ID. Works for both TACO and custom foods.",
            inputSchema={
                "type": "object",
                "properties": {
                    "food_id": {
                        "type": "integer",
                        "description": "Food ID"
                    }
                },
                "required": ["food_id"]
            }
        ),
        Tool(
            name="calculate_macros",
            description="Calculate macros for a specific food and gram amount. Works for both TACO and custom foods.",
            inputSchema={
                "type": "object",
                "properties": {
                    "food_id": {
                        "type": "integer",
                        "description": "Food ID"
                    },
                    "grams": {
                        "type": "number",
                        "description": "Amount in grams",
                        "minimum": 0,
                        "maximum": 10000
                    }
                },
                "required": ["food_id", "grams"]
            }
        ),
        Tool(
            name="calculate_meal_macros",
            description="Calculate total macros for a meal with multiple food items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "List of food items with amounts",
                        "items": {
                            "type": "object",
                            "properties": {
                                "food_id": {
                                    "type": "integer",
                                    "description": "Food ID"
                                },
                                "grams": {
                                    "type": "number",
                                    "description": "Amount in grams",
                                    "minimum": 0
                                }
                            },
                            "required": ["food_id", "grams"]
                        }
                    }
                },
                "required": ["items"]
            }
        ),
        Tool(
            name="add_custom_food",
            description="Add a custom food to the database (e.g., supplements, branded products, homemade recipes). Returns the new food ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the food (e.g., 'Whey Protein Isolado', 'Pão de Queijo Caseiro')"
                    },
                    "kcal_per_100g": {
                        "type": "number",
                        "description": "Calories per 100g",
                        "minimum": 0
                    },
                    "protein_g_per_100g": {
                        "type": "number",
                        "description": "Protein in grams per 100g",
                        "default": 0
                    },
                    "fat_g_per_100g": {
                        "type": "number",
                        "description": "Fat in grams per 100g",
                        "default": 0
                    },
                    "carbs_g_per_100g": {
                        "type": "number",
                        "description": "Carbohydrates in grams per 100g",
                        "default": 0
                    },
                    "fiber_g_per_100g": {
                        "type": "number",
                        "description": "Fiber in grams per 100g",
                        "default": 0
                    },
                    "sodium_mg_per_100g": {
                        "type": "number",
                        "description": "Sodium in mg per 100g",
                        "default": 0
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (default: 'Custom')",
                        "default": "Custom"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes (brand, recipe source, etc.)",
                        "default": ""
                    }
                },
                "required": ["name", "kcal_per_100g"]
            }
        ),
        Tool(
            name="list_custom_foods",
            description="List all custom foods added to the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            }
        ),
        Tool(
            name="delete_custom_food",
            description="Delete a custom food by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "food_id": {
                        "type": "integer",
                        "description": "Custom food ID to delete"
                    }
                },
                "required": ["food_id"]
            }
        )
    ]


CUSTOM_FOOD_ID_OFFSET = 100000  # Custom foods start at this ID

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "search_food":
        args = SearchFoodInput(**arguments)
        # Search both TACO and custom foods
        taco_results = db.search_food(args.query, args.limit)
        custom_results = db.search_custom_foods(args.query, args.limit, id_offset=CUSTOM_FOOD_ID_OFFSET)
        
        # Combine results
        all_results = taco_results.results + custom_results
        # Limit to requested amount
        all_results = all_results[:args.limit]
        
        result = SearchFoodOutput(
            query=args.query,
            normalized_query=taco_results.normalized_query,
            results=all_results
        )
        return [TextContent(
            type="text",
            text=result.model_dump_json(indent=2)
        )]
    
    elif name == "get_food":
        args = GetFoodInput(**arguments)
        food_id = args.food_id
        
        # Check if it's a custom food ID (>= offset)
        if food_id >= CUSTOM_FOOD_ID_OFFSET:
            result = db.get_custom_food(food_id - CUSTOM_FOOD_ID_OFFSET)
            if result:
                # Adjust ID in response
                result.food_id = food_id
        else:
            # Try TACO first
            result = db.get_food(food_id)
            if result is None:
                # Check if there's a custom food with this ID (legacy)
                result = db.get_custom_food(food_id)
        
        if result is None:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Food ID {food_id} not found"}, indent=2)
            )]
        return [TextContent(
            type="text",
            text=result.model_dump_json(indent=2)
        )]
    
    elif name == "calculate_macros":
        args = CalculateMacrosInput(**arguments)
        food_id = args.food_id
        
        # Check if it's a custom food
        if food_id >= CUSTOM_FOOD_ID_OFFSET:
            custom_id = food_id - CUSTOM_FOOD_ID_OFFSET
            custom = db.get_custom_food(custom_id)
            if custom:
                from .schemas import CalculatedMacros, CalculateMacrosOutput
                from .normalize import round_macro
                per_100g = custom.per_100g
                factor = args.grams / 100.0
                
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
                
                result = CalculateMacrosOutput(
                    food_id=food_id,
                    description=custom.description,
                    grams=args.grams,
                    macros=macros
                )
            else:
                result = None
        else:
            # Try TACO
            result = db.calculate_macros(food_id, args.grams)
            if result is None:
                # Try custom food (legacy)
                custom = db.get_custom_food(food_id)
                if custom:
                    from .schemas import CalculatedMacros, CalculateMacrosOutput
                    from .normalize import round_macro
                    per_100g = custom.per_100g
                    factor = args.grams / 100.0
                    
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
                    
                    result = CalculateMacrosOutput(
                        food_id=food_id,
                        description=custom.description,
                        grams=args.grams,
                        macros=macros
                    )
        
        if result is None:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Food ID {food_id} not found"}, indent=2)
            )]
        return [TextContent(
            type="text",
            text=result.model_dump_json(indent=2)
        )]
    
    elif name == "calculate_meal_macros":
        raw_items = arguments.get("items", [])
        items = [MealItemInput(food_id=item["food_id"], grams=item["grams"]) for item in raw_items]
        result = db.calculate_meal_macros(items)
        return [TextContent(
            type="text",
            text=result.model_dump_json(indent=2)
        )]
    
    elif name == "add_custom_food":
        raw_id = db.add_custom_food(
            name=arguments["name"],
            kcal_per_100g=arguments["kcal_per_100g"],
            protein_g_per_100g=arguments.get("protein_g_per_100g", 0),
            fat_g_per_100g=arguments.get("fat_g_per_100g", 0),
            carbs_g_per_100g=arguments.get("carbs_g_per_100g", 0),
            fiber_g_per_100g=arguments.get("fiber_g_per_100g", 0),
            sodium_mg_per_100g=arguments.get("sodium_mg_per_100g", 0),
            category=arguments.get("category", "Custom"),
            notes=arguments.get("notes", "")
        )
        # Return ID with offset to distinguish from TACO foods
        food_id = raw_id + CUSTOM_FOOD_ID_OFFSET
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "food_id": food_id,
                "name": arguments["name"],
                "message": f"Custom food '{arguments['name']}' added with ID {food_id}"
            }, indent=2)
        )]
    
    elif name == "list_custom_foods":
        limit = arguments.get("limit", 50)
        foods = db.list_custom_foods(limit)
        # Add offset to IDs
        for food in foods:
            food['id'] = food['id'] + CUSTOM_FOOD_ID_OFFSET
        return [TextContent(
            type="text",
            text=json.dumps({
                "count": len(foods),
                "foods": foods
            }, indent=2)
        )]
    
    elif name == "delete_custom_food":
        food_id = arguments["food_id"]
        # Convert to raw ID
        if food_id >= CUSTOM_FOOD_ID_OFFSET:
            food_id = food_id - CUSTOM_FOOD_ID_OFFSET
        deleted = db.delete_custom_food(food_id)
        if deleted:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Custom food ID {arguments['food_id']} deleted"
                }, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Custom food ID {arguments['food_id']} not found"
                }, indent=2)
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
        )]


async def main():
    """Run MCP server."""
    # Check database exists
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}", file=__import__('sys').stderr)
        print("Run: python scripts/download_taco.py && python scripts/build_db.py", file=__import__('sys').stderr)
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
