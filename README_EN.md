# 🌮 TACO MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![TACO Database](https://img.shields.io/badge/TACO-597%20foods-orange.svg)](https://www.nepa.unicamp.br/taco/)

> **Model Context Protocol (MCP) server for the Brazilian TACO nutritional database.**

Enable AI agents to search, calculate, and log Brazilian foods with accurate macro-nutritional data. Perfect for fitness apps, nutrition coaches, and personal food logging systems.

---

## 🚀 Quick Start

**Requirement:** Python 3.11+

### Option 1: Simple Install (Recommended)

```bash
pip install git+https://github.com/matheusbuniotto/taco-mcp.git
```

Done! The `taco-mcp` command is now available globally.

### Option 2: With uv (No global install)

If you use [uv](https://docs.astral.sh/uv/):

```bash
# Run directly without installing
uvx --from git+https://github.com/matheusbuniotto/taco-mcp.git taco-mcp

# Or install in current environment
uv pip install git+https://github.com/matheusbuniotto/taco-mcp.git
```

### Option 3: Development (Clone)

```bash
git clone https://github.com/matheusbuniotto/taco-mcp.git
cd taco-mcp
pip install -e "."
```

---

## 🔗 Integrations

### Hermes Agent (Simple Config)

**Step 1:** Install the package
```bash
pip install git+https://github.com/matheusbuniotto/taco-mcp.git
```

**Step 2:** Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  taco:
    command: "taco-mcp"
    timeout: 30
```

Done! Restart Hermes and the tools will be available.

### Alternative Config (no global install)

If you prefer not to install globally, use with **uv**:

```yaml
mcp_servers:
  taco:
    command: "uvx"
    args: ["--from", "git+https://github.com/matheusbuniotto/taco-mcp.git", "taco-mcp"]
    timeout: 30
```

Or with Python directly (requires clone):

```yaml
mcp_servers:
  taco:
    command: "python"
    args: ["-m", "taco_mcp.server"]
    timeout: 30
```

Tools become available as:
- `mcp_taco_search_food`
- `mcp_taco_get_food`
- `mcp_taco_calculate_macros`
- `mcp_taco_calculate_meal_macros`
- `mcp_taco_add_custom_food`
- `mcp_taco_list_custom_foods`
- `mcp_taco_delete_custom_food`

### Claude Desktop / Other MCP Clients

**Point-and-Configure:**

Edit your Claude Desktop settings file:

- **Windows:** `%APPDATA%\Claude\settings.json`
- **Mac:** `~/Library/Application Support/Claude/settings.json`
- **Linux:** `~/.config/Claude/settings.json`

Add:

```json
{
  "mcpServers": {
    "taco": {
      "command": "taco-mcp"
    }
  }
}
```

Restart Claude Desktop.

---

## 📊 Data Source

**TACO** (Tabela Brasileira de Composição de Alimentos) is the official Brazilian food composition database maintained by UNICAMP.

- **597 foods** from 20+ categories
- 28 nutritional components per food
- Values per 100g edible portion
- Official source: https://www.nepa.unicamp.br/taco/

### Categories Covered

```
Cereais e derivados          | Frutas e derivados
Verduras, hortaliças         | Gorduras e óleos
Pescados e frutos do mar     | Carnes e derivados
Leite e derivados            | Bebidas
Ovos e derivados             | Produtos açucarados
Miscelâneas                  | Industrializados
```

---

## 🛠️ Available Tools

### Core Tools

#### `search_food`

Search foods by name in Portuguese. Returns candidates from both TACO and custom foods.

```json
{
  "query": "arroz",
  "limit": 5
}
```

**Response:**
```json
{
  "query": "arroz",
  "normalized_query": "arroz",
  "results": [
    {
      "food_id": 3,
      "description": "Arroz, tipo 1, cozido",
      "category": "Cereais e derivados",
      "per_100g": {
        "kcal": 128.0,
        "protein_g": 2.5,
        "carbs_g": 28.1,
        "fat_g": 0.2,
        "fiber_g": 1.6,
        "sodium_mg": 1.0
      },
      "match_reason": "alias",
      "confidence": 1.0
    }
  ]
}
```

#### `get_food`

Get detailed food information by ID.

```json
{
  "food_id": 3
}
```

#### `calculate_macros`

Calculate macros for a specific gram amount.

```json
{
  "food_id": 3,
  "grams": 150
}
```

**Response:**
```json
{
  "food_id": 3,
  "description": "Arroz, tipo 1, cozido",
  "grams": 150.0,
  "macros": {
    "kcal": 192.0,
    "protein_g": 3.75,
    "carbs_g": 42.15,
    "fat_g": 0.3,
    "fiber_g": 2.4,
    "sodium_mg": 1.5
  }
}
```

#### `calculate_meal_macros`

Calculate total macros for a meal with multiple items.

```json
{
  "items": [
    {"food_id": 3, "grams": 150},
    {"food_id": 410, "grams": 100}
  ]
}
```

**Response:**
```json
{
  "source": "TACO",
  "items": [...],
  "total": {
    "kcal": 351.0,
    "protein_g": 35.75,
    "carbs_g": 42.15,
    "fat_g": 2.8
  }
}
```

### Custom Foods

#### `add_custom_food`

Add supplements, branded products, or homemade recipes.

```json
{
  "name": "Whey Protein Isolado Dux",
  "kcal_per_100g": 374,
  "protein_g_per_100g": 87,
  "fat_g_per_100g": 2,
  "carbs_g_per_100g": 3,
  "category": "Suplementos",
  "notes": "1 scoop = 30g"
}
```

**Custom food IDs start at 100000** to avoid conflicts with TACO IDs (1-597).

#### `list_custom_foods`

List all custom foods added.

```json
{
  "limit": 50
}
```

#### `delete_custom_food`

Remove a custom food by ID.

```json
{
  "food_id": 100001
}
```

---

## 🎯 Usage Examples

### Natural Language Food Logging

**User:** "Comi 150g de arroz e 100g de frango"

**Agent workflow:**

```python
# 1. Parse the query
items = [
    ("arroz", 150),
    ("frango", 100)
]

# 2. Search for foods
search_food("arroz")     # Returns: Arroz, tipo 1, cozido (ID 3)
search_food("frango")    # Returns: Frango, peito, grelhado (ID 410)

# 3. Calculate meal macros
calculate_meal_macros([
    {"food_id": 3, "grams": 150},
    {"food_id": 410, "grams": 100}
])

# 4. Present to user
# "Total: 351 kcal (35.8g protein, 42.2g carbs, 2.8g fat)"
```

### Adding Supplements

**User:** "Add my protein powder: 110 kcal, 24g protein per scoop"

```python
add_custom_food(
    name="My Whey Protein",
    kcal_per_100g=367,  # 110 * 100/30
    protein_g_per_100g=80,
    category="Suplementos",
    notes="1 scoop = 30g"
)
```

---

## 🌐 Aliases System

Common food aliases are mapped for better natural language matching:

```yaml
# data/aliases.yaml
arroz: 3                    # Arroz tipo 1 cozido
arroz branco: 3
arroz integral: 1
frango: 410                 # Peito grelhado
peito de frango: 410
ovo: 199                    # Ovo cozido
banana: 78                  # Banana prata
whey: 100001                # Your custom whey
```

Aliases ensure that when users say "comi arroz", the system returns the most common preparation (arroz branco cozido) rather than requiring exact database matches.

---

## 🎨 Architecture

```
├── TACO CSV (597 foods)
│   └── download_taco.py
├── SQLite Database
│   ├── foods table (TACO data)
│   ├── foods_fts (FTS5 full-text search)
│   ├── custom_foods table (user-added)
│   └── build_db.py
├── MCP Server
│   ├── search_food (FTS5 + aliases)
│   ├── calculate_macros
│   ├── calculate_meal_macros
│   └── custom_food management
└── Hermes/Claude/Any MCP Client
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SQLite + FTS5** | No external services, fast full-text search |
| **No embeddings** | TACO is small (~600 items); FTS5 is sufficient |
| **Custom food IDs offset (100000+)** | Prevents collision with official TACO IDs |
| **Aliases layer** | Handles natural language variation ("arroz" vs "arroz branco") |
| **Portuguese normalization** | Removes accents for better matching |

---

## 📁 Project Structure

```
taco-mcp/
├── data/
│   ├── raw/
│   │   └── alimentos.csv          # TACO source data
│   ├── processed/
│   │   └── taco.sqlite            # SQLite database
│   └── aliases.yaml              # Food name aliases
├── scripts/
│   ├── download_taco.py          # Download TACO CSV
│   └── build_db.py               # Build SQLite database
├── src/taco_mcp/
│   ├── __init__.py
│   ├── server.py                 # MCP server implementation
│   ├── db.py                     # Database operations
│   ├── schemas.py                # Pydantic models
│   └── normalize.py              # Text/numeric normalization
├── tests/
│   ├── test_db.py
│   └── test_normalize.py
├── pyproject.toml
└── README.md
```

---

## 🧪 Development

### Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

### Adding Aliases

Edit `data/aliases.yaml`:

```yaml
my_custom_alias: 100001
# Map common terms to food IDs
```

### Rebuilding Database

```bash
python scripts/download_taco.py --force
python scripts/build_db.py
```

---

## 📋 Roadmap

- [ ] Recipe builder (combine multiple foods into a single recipe)
- [ ] Barcode lookup integration
- [ ] Portion size estimation ("1 prato", "1 concha")
- [ ] Nutrition goal tracking (daily totals)
- [ ] Multi-language support (English descriptions)

---

## 📋 License

MIT License - see [LICENSE](LICENSE)

---

## 🪝 Acknowledgments

- **UNICAMP/NEPA** for maintaining the TACO database
- **Model Context Protocol** team for the MCP specification
- **machine-learning-mocha** for the CSV export on GitHub

---

## 📞 Support

- 🐛 Issues: [github.com/matheusbuniotto/taco-mcp/issues](https://github.com/matheusbuniotto/taco-mcp/issues)
- 📝 Discussions: [GitHub Discussions](https://github.com/matheusbuniotto/taco-mcp/discussions)

---

<p align="center">
  <i>Built with ❤️ for Brazilian nutrition tracking</i>
</p>
