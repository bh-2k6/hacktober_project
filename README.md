# AI Lost & Found

AI-powered lost and found matching system for college campuses. Uses open-weight multimodal AI to automatically identify potential matches between lost and found reports.

## Features

- **AI Image Analysis**: Upload a photo of a lost or found item and the AI extracts structured information (category, color, brand, distinctive features)
- **Automatic Matching**: The system automatically finds potential matches between lost and found reports using a deterministic weighted scoring algorithm
- **Transparent Explanations**: Every match includes a "Why this matches" section showing exactly which factors contributed to the score
- **Match Management**: Mark matches as confirmed, rejected, or pending
- **Privacy-First Contact**: Contact/claim workflow that doesn't publicly expose personal information
- **Demo Mode**: Works without AI inference using a deterministic mock provider

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) [Ollama](https://ollama.ai) for real AI inference

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd hacktober_project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed demo data (optional)
python scripts/seed_demo_data.py
```

### Running

```bash
# Start the application
python main.py
```

Open http://localhost:8000 in your browser.

### Using Real AI (Optional)

```bash
# Install Ollama from https://ollama.ai, then:
ollama pull llava:7b
ollama pull nomic-embed-text

# Configure environment
cp .env.example .env
# Edit .env: AI_PROVIDER=ollama

# Restart the application
python main.py
```

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `mock` | `ollama` for real AI, `mock` for demo mode |
| `AI_MODEL` | `llava:7b` | Vision model for image analysis |
| `AI_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Text embedding model |
| `PORT` | `8000` | Server port |

## How It Works

### AI Analysis Pipeline

1. User uploads an image and description
2. The AI provider (Ollama + LLaVA) analyzes the image and extracts:
   - Object category (electronics, clothing, accessories, etc.)
   - Object type (smartphone, backpack, etc.)
   - Color, brand, visible text
   - Distinctive features and characteristics
3. This structured data is stored with the report

### Matching Algorithm

When a new report is submitted, the system compares it against all opposite-type reports using weighted factors:

| Factor | Weight | Method |
|--------|--------|--------|
| Object type | 25% | String similarity |
| Category | 15% | String similarity |
| Color | 15% | Color similarity (with similar color groups) |
| Brand | 10% | String similarity |
| Text similarity | 15% | Jaccard similarity on tokens |
| Image similarity | 10% | Average hash (aHash) Hamming distance |
| Location | 5% | Location string similarity |
| Temporal | 5% | Time difference decay |

The final score is a weighted sum. The AI generates a human-readable explanation based on the top contributing factors.

### AI Provider Architecture

```
AIProvider (abstract base)
├── analyzeItem()     → Extract structured info from image + description
├── generateEmbedding() → Generate text embedding vector
└── explainMatch()    → Generate human-readable match explanation

Providers:
├── OllamaAIProvider  → Real AI using Ollama + LLaVA
└── MockAIProvider    → Deterministic demo provider (no AI required)
```

## API Endpoints

### Items
- `POST /api/items` - Create a new lost/found report (with optional image)
- `GET /api/items` - List items (filter by type, status, category, search)
- `GET /api/items/{id}` - Get item details
- `PATCH /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

### Matches
- `GET /api/matches` - List matches (filter by status, min_score)
- `GET /api/matches/{id}` - Get match details
- `PATCH /api/matches/{id}` - Update match status (pending/confirmed/rejected)
- `POST /api/matches/contact` - Send contact request
- `GET /api/matches/contact/{match_id}` - Get contact requests for a match

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

## Project Structure

```
hacktober_project/
├── main.py                 # FastAPI entry point
├── requirements.txt
├── .env.example
├── app/
│   ├── config.py           # Configuration
│   ├── database.py         # SQLite database
│   ├── models.py           # Pydantic schemas
│   ├── ai/                 # AI provider abstraction
│   │   ├── base.py         # Abstract base class
│   │   ├── ollama.py       # Ollama implementation
│   │   └── mock.py         # Demo provider
│   ├── matching/           # Matching engine
│   │   └── engine.py       # Scoring algorithm
│   ├── routes/             # API routes
│   │   ├── items.py
│   │   ├── matches.py
│   │   └── dashboard.py
│   └── static/             # Frontend
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
├── data/
│   ├── uploads/            # Uploaded images
│   └── lost_and_found.db   # SQLite database
└── scripts/
    └── seed_demo_data.py   # Demo data generator
```

## Technology Stack

- **Backend**: Python + FastAPI
- **Database**: SQLite
- **AI**: Ollama + LLaVA (open-weight multimodal model)
- **Embeddings**: nomic-embed-text (open-weight)
- **Frontend**: Vanilla JS + Modern CSS
- **Image Processing**: Pillow (aHash)

## License

MIT License - see [LICENSE](LICENSE) file
