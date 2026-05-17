# 🌮 TACO MCP Server - Tabela Nutricional Brasileira para Agentes de IA

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![TACO Database](https://img.shields.io/badge/TACO-597%20alimentos-orange.svg)](https://www.nepa.unicamp.br/taco/)

> **Servidor MCP (Model Context Protocol) para a Tabela TACO de composição de alimentos brasileiros.**

Conecte agentes de inteligência artificial à maior base de dados nutricionais do Brasil. Calcule calorias, proteínas, carboidratos e gorduras de 597 alimentos brasileiros oficiais. Ideal para apps de dieta, coaching nutricional e controle de macros.

[📖 English Version](README_EN.md)

---

## 🚀 Instalação Rápida

### Pré-requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recomendado) ou pip

### Passo a Passo

```bash
# Clone o repositório
git clone https://github.com/matheusbuniotto/taco-mcp.git
cd taco-mcp

# Instale as dependências
uv venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

uv pip install -e "."

# Baixe e construa a base de dados TACO
python scripts/download_taco.py
python scripts/build_db.py

# Inicie o servidor MCP
python -m taco_mcp.server
```

---

## 🔗 Integrações Disponíveis

### Hermes Agent

Adicione ao seu `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  taco:
    command: "uv"
    args:
      - "run"
      - "--project"
      - "/caminho/para/taco-mcp"
      - "python"
      - "-m"
      - "taco_mcp.server"
    timeout: 30
```

As ferramentas aparecerão como:
- `mcp_taco_search_food` - Buscar alimentos
- `mcp_taco_get_food` - Detalhes do alimento
- `mcp_taco_calculate_macros` - Calcular macros por grama
- `mcp_taco_calculate_meal_macros` - Calcular refeição completa
- `mcp_taco_add_custom_food` - Adicionar alimento customizado
- `mcp_taco_list_custom_foods` - Listar customizados
- `mcp_taco_delete_custom_food` - Remover customizado

### Claude Desktop / Outros Clientes MCP

```json
{
  "mcpServers": {
    "taco": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/caminho/para/taco-mcp",
        "python",
        "-m",
        "taco_mcp.server"
      ]
    }
  }
}
```

---

## 📊 Base de Dados TACO

A **TACO** (Tabela Brasileira de Composição de Alimentos) é mantida pela UNICAMP/NEPA e é a referência oficial para nutrição no Brasil.

- **597 alimentos** em mais de 20 categorias
- 28 componentes nutricionais por alimento
- Valores por 100g de porção comestível
- Fonte oficial: https://www.nepa.unicamp.br/taco/

### Categorias de Alimentos

```
Cereais e derivados              | Frutas e derivados
Verduras, hortaliças             | Gorduras e óleos
Pescados e frutos do mar         | Carnes e derivados
Leite e derivados                | Bebidas (alcoólicas e não)
Ovos e derivados                 | Produtos açucarados
Miscelâneas                      | Alimentos industrializados
Leguminosas                      | Nozes e sementes
```

---

## 🛠️ Ferramentas Disponíveis

### Busca e Consulta

#### `search_food` - Buscar Alimentos

Busque alimentos por nome em português. Retorna candidatos do TACO e alimentos customizados.

```json
{
  "query": "arroz",
  "limit": 5
}
```

**Resposta:**
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

#### `get_food` - Detalhes do Alimento

```json
{
  "food_id": 3
}
```

#### `calculate_macros` - Calcular Macronutrientes

Calcule calorias e macros para uma quantidade específica em gramas.

```json
{
  "food_id": 3,
  "grams": 150
}
```

**Resposta:**
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

#### `calculate_meal_macros` - Calcular Refeição Completa

```json
{
  "items": [
    {"food_id": 3, "grams": 150},
    {"food_id": 410, "grams": 100}
  ]
}
```

**Resposta:**
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

### Alimentos Customizados

#### `add_custom_food` - Adicionar Suplemento ou Marca

Adicione whey protein, creatina, barras de proteína ou receitas caseiras.

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

**IDs de alimentos customizados começam em 100000** para evitar conflito com o TACO (1-597).

#### `list_custom_foods` - Listar Customizados

```json
{
  "limit": 50
}
```

#### `delete_custom_food` - Remover Alimento

```json
{
  "food_id": 100001
}
```

---

## 🎯 Exemplos de Uso

### Diário Alimentar em Linguagem Natural

**Usuário:** "Comi 150g de arroz e 100g de frango"

**Fluxo do agente:**

```python
# 1. Extrai os itens
itens = [
    ("arroz", 150),
    ("frango", 100)
]

# 2. Busca os alimentos
search_food("arroz")     # Retorna: Arroz, tipo 1, cozido (ID 3)
search_food("frango")    # Retorna: Frango, peito, grelhado (ID 410)

# 3. Calcula a refeição
calculate_meal_macros([
    {"food_id": 3, "grams": 150},
    {"food_id": 410, "grams": 100}
])

# 4. Apresenta ao usuário
# "Total: 351 kcal (35.8g proteína, 42.2g carboidratos, 2.8g gorduras)"
```

### Adicionando Suplementos

**Usuário:** "Cadastra meu whey: 110 kcal, 24g proteína por scoop"

```python
add_custom_food(
    name="Meu Whey Protein",
    kcal_per_100g=367,  # 110 * 100/30
    protein_g_per_100g=80,
    category="Suplementos",
    notes="1 scoop = 30g"
)
```

---

## 🌐 Sistema de Apelidos (Aliases)

Mapeamento de termos comuns para facilitar busca em linguagem natural:

```yaml
# data/aliases.yaml
arroz: 3                    # Arroz tipo 1 cozido
arroz branco: 3
arroz integral: 1
frango: 410                 # Peito grelhado
peito de frango: 410
ovo: 199                    # Ovo cozido
banana: 78                  # Banana prata
feijao: 175                 # Feijão carioca
batata: 156                 # Batata inglesa cozida
pao: 51                     # Pão francês
```

Os aliases garantem que quando o usuário diz "comi arroz", o sistema retorne o preparo mais comum (arroz branco cozido) ao invés de exigir correspondência exata.

---

## 🎨 Arquitetura

```
├── CSV TACO (597 alimentos)
│   └── download_taco.py
├── Banco SQLite
│   ├── tabela foods (dados TACO)
│   ├── tabela foods_fts (busca FTS5)
│   ├── tabela custom_foods (alimentos do usuário)
│   └── build_db.py
├── Servidor MCP
│   ├── search_food (FTS5 + aliases)
│   ├── calculate_macros
│   ├── calculate_meal_macros
│   └── Gerenciamento de custom_foods
└── Cliente MCP (Hermes, Claude, etc.)
```

### Decisões de Design

| Decisão | Motivação |
|---------|-----------|
| **SQLite + FTS5** | Sem serviços externos, busca full-text rápida |
| **Sem embeddings** | Base pequena (~600 itens); FTS5 é suficiente |
| **Offset de IDs (100000+)** | Evita colisão com IDs oficiais do TACO |
| **Camada de aliases** | Lida com variação de linguagem natural |
| **Normalização PT-BR** | Remove acentos para melhor matching |

---

## 📁 Estrutura do Projeto

```
taco-mcp/
├── data/
│   ├── raw/
│   │   └── alimentos.csv          # Dados fonte TACO
│   ├── processed/
│   │   └── taco.sqlite            # Banco SQLite
│   └── aliases.yaml              # Apelidos de alimentos
├── scripts/
│   ├── download_taco.py          # Download do CSV TACO
│   └── build_db.py               # Constrói banco SQLite
├── src/taco_mcp/
│   ├── __init__.py
│   ├── server.py                 # Implementação MCP
│   ├── db.py                     # Operações de banco
│   ├── schemas.py                # Modelos Pydantic
│   └── normalize.py              # Normalização de texto
├── tests/
│   ├── test_db.py
│   └── test_normalize.py
├── pyproject.toml
├── README.md
├── README_EN.md
└── LICENSE
```

---

## 🧪 Desenvolvimento

### Executar Testes

```bash
uv pip install pytest
python -m pytest tests/ -v
```

### Adicionar Aliases

Edite `data/aliases.yaml`:

```yaml
meu_apelido_customizado: 100001
# Mapeie termos comuns para IDs de alimentos
```

### Reconstruir Base de Dados

```bash
python scripts/download_taco.py --force
python scripts/build_db.py
```

---

## 📋 Roadmap

- [ ] Construtor de receitas (combinar múltiplos alimentos)
- [ ] Integração com busca por código de barras
- [ ] Estimativa de porções ("1 prato", "1 concha", "1 fatia")
- [ ] Acompanhamento de metas diárias
- [ ] Suporte multilíngue (descrições em inglês)

---

## 📋 Licença

MIT License - veja [LICENSE](LICENSE)

---

## 🪝 Agradecimentos

- **UNICAMP/NEPA** por manter a base TACO
- **Model Context Protocol** pela especificação MCP
- **machine-learning-mocha** pela exportação CSV no GitHub

---

## 📞 Suporte

- 🐛 Issues: [github.com/matheusbuniotto/taco-mcp/issues](https://github.com/matheusbuniotto/taco-mcp/issues)
- 📝 Discussões: [GitHub Discussions](https://github.com/matheusbuniotto/taco-mcp/discussions)

---

<p align="center">
  <i>Feito com ❤️ para a nutrição brasileira</i>
</p>
