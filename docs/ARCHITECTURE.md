# Architecture Documentation

## Overview

TraceBack is a single-process web application built with FastAPI. It uses a clean modular architecture with clear separation between UI, API, database, AI provider, and matching engine.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser (SPA)                     │
│         Vanilla JS + Modern CSS (no build)          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────────────┐
│                 FastAPI Application                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ items.py    │  │ matches.py   │  │ dashboard  │ │
│  │ (CRUD)      │  │ (matching)   │  │ (stats)    │ │
│  └──────┬──────┘  └──────┬───────┘  └────────────┘ │
│         │                │                          │
│  ┌──────▼────────────────▼──────────────────────┐  │
│  │              AI Provider Layer               │  │
│  │  ┌─────────────┐    ┌──────────────────┐    │  │
│  │  │ OllamaAI    │    │ MockAIProvider   │    │  │
│  │  │ Provider    │    │ (demo fallback)  │    │  │
│  │  └─────────────┘    └──────────────────┘    │  │
│  └──────────────────┬───────────────────────────┘  │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐  │
│  │           Matching Engine                     │  │
│  │  Deterministic weighted scoring algorithm     │  │
│  └──────────────────┬───────────────────────────┘  │
│                     │                               │
│  ┌──────────────────▼───────────────────────────┐  │
│  │              SQLite Database                  │  │
│  │  items │ matches │ contact_requests           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Report Submission
```
User → POST /api/items (image + description)
  → AI Provider analyzes image → ItemAnalysis
  → Store item with AI-extracted fields
  → Matching engine finds potential matches
  → Store matches with scores and explanations
```

### 2. Match Discovery
```
New item submitted
  → For each opposite-type active item:
    → Compute factor scores (object type, color, brand, etc.)
    → Calculate weighted final score
    → If score >= 0.3: create match record
  → Generate explanation from top factors
```

### 3. Match Management
```
User reviews match → PATCH /api/matches/{id}
  → status: pending → confirmed/rejected
  → If confirmed: mark both items as "reunited"
```

## AI Provider Abstraction

The AI provider layer is designed for easy model swapping:

```python
class AIProvider(ABC):
    async def analyze_item(image_path, description) -> ItemAnalysis
    async def generate_embedding(text) -> List[float]
    async def explain_match(item1, item2, ...) -> str
```

**OllamaAIProvider**: Uses Ollama API with LLaVA for image analysis and nomic-embed-text for embeddings.

**MockAIProvider**: Deterministic keyword-based analysis for demo/development without AI inference.

## Matching Engine

The matching engine uses a transparent, deterministic scoring system:

1. **Object Type (25%)**: String similarity between AI-extracted object types
2. **Category (15%)**: String similarity between categories
3. **Color (15%)**: Color similarity with similar color groups
4. **Brand (10%)**: String similarity between brands
5. **Text Similarity (15%)**: Jaccard similarity on description tokens
6. **Image Similarity (10%)**: aHash (average hash) Hamming distance
7. **Location (5%)**: Location string similarity
8. **Temporal (5%)**: Time difference decay function

Final score = Σ(factor_score × weight), clamped to [0, 1]

## Database Schema

### items
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| type | TEXT | 'lost' or 'found' |
| title | TEXT | Item title |
| description | TEXT | User description |
| category | TEXT | AI-extracted category |
| object_type | TEXT | AI-extracted object type |
| color | TEXT | AI-extracted color |
| brand | TEXT | AI-extracted brand |
| characteristics | TEXT (JSON) | AI-extracted characteristics |
| distinctive_features | TEXT (JSON) | AI-extracted features |
| visible_text | TEXT | AI-extracted visible text |
| other_attributes | TEXT (JSON) | Additional AI attributes |
| location | TEXT | Report location |
| date_time | TEXT | ISO datetime |
| image_path | TEXT | Path to uploaded image |
| image_phash | TEXT | Average hash (aHash) |
| status | TEXT | 'active', 'reunited', 'expired' |

### matches
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| lost_item_id | INTEGER FK | Reference to lost item |
| found_item_id | INTEGER FK | Reference to found item |
| score | REAL | Match score (0-1) |
| explanation | TEXT | Human-readable explanation |
| factor_scores | TEXT (JSON) | Individual factor scores |
| status | TEXT | 'pending', 'confirmed', 'rejected' |

### contact_requests
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| match_id | INTEGER FK | Reference to match |
| requester_type | TEXT | 'lost_owner' or 'found_finder' |
| message | TEXT | Contact message |
| status | TEXT | 'pending', 'approved', 'rejected' |

## Security Considerations

- No personal contact information is publicly exposed
- Contact requests require approval before sharing details
- Image uploads are validated for type and size
- SQL injection prevented via parameterized queries
- No API keys in frontend code
- Environment variables for all sensitive configuration
