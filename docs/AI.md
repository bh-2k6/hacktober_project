# AI Documentation

## Overview

TraceBack uses open-weight AI models as a core component of its functionality. The AI is not a chatbot add-on — it is the engine that understands images, extracts structured information, and drives the matching system.

## AI Models

### Primary: LLaVA (Large Language and Vision Assistant)

**Model**: `llava:7b` (configurable via `AI_MODEL`)

**What it does**: Analyzes images of lost/found items and extracts structured information:
- Object category (electronics, clothing, accessories, books, sports, other)
- Object type (smartphone, backpack, umbrella, etc.)
- Color, brand, visible text
- Distinctive features and characteristics

**Why LLaVA**:
- Open-weight (based on Llama architecture)
- Multimodal — understands both images and text
- Can run on CPU with 16GB RAM
- Good at extracting structured information from images
- Active open-source community

**Alternative models**:
- `llava:3b` — smaller, faster, less capable
- `moondream2` — ultra-lightweight (~2B parameters)

### Embedding Model: nomic-embed-text

**Model**: `nomic-embed-text` (configurable via `EMBEDDING_MODEL`)

**What it does**: Generates text embeddings for semantic similarity matching.

**Why nomic-embed-text**:
- Open-weight (Apache 2.0)
- Small (~274MB)
- Good quality for semantic similarity
- Runs efficiently on CPU

**Fallback**: TF-IDF with cosine similarity (no model required)

## AI Provider Architecture

```
AIProvider (abstract base)
├── analyzeItem(image_path, description) → ItemAnalysis
├── generate_embedding(text) → List[float]
└── explain_match(item1, item2, ...) → str

Implementations:
├── OllamaAIProvider  → Real AI using Ollama API
└── MockAIProvider    → Deterministic demo provider
```

### OllamaAIProvider

Uses the Ollama local API for all AI operations:

1. **Image Analysis**: Sends image as base64 to `/api/generate` with LLaVA model
2. **Embeddings**: Uses `/api/embeddings` with nomic-embed-text model
3. **Match Explanation**: Uses LLaVA to generate human-readable explanations

### MockAIProvider

Deterministic provider for demo/development without AI inference:

1. **Image Analysis**: Uses keyword matching on description text
2. **Embeddings**: Simple token frequency vectors
3. **Match Explanation**: Template-based explanations

## How AI Inference Runs on Your Hardware

**Target**: AMD Ryzen 5 8640U, 16GB RAM, integrated graphics

### With Ollama (Real AI)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull models
ollama pull llava:7b        # ~4.7GB download
ollama pull nomic-embed-text # ~274MB download

# Run (Ollama starts automatically)
ollama serve
```

**Performance on Ryzen 5 8640U / 16GB RAM**:
- `llava:7b`: ~10-30 seconds per image analysis (CPU only)
- `llava:3b`: ~5-15 seconds per image analysis
- `moondream2`: ~3-8 seconds per image analysis
- Embeddings: <1 second per text

**Memory usage**:
- `llava:7b`: ~4-6GB RAM
- `llava:3b`: ~2-3GB RAM
- `moondream2`: ~1-2GB RAM

### Without Ollama (Demo Mode)

Set `AI_PROVIDER=mock` in `.env`. The app uses deterministic keyword-based analysis and works instantly with no model downloads.

## AI Analysis Pipeline

```
User uploads image + description
         │
         ▼
┌─────────────────────────┐
│   OllamaAIProvider      │
│   ┌─────────────────┐   │
│   │ LLaVA analyzes │   │
│   │ image + text    │   │
│   └────────┬────────┘   │
│            │            │
│   ┌────────▼────────┐   │
│   │ Returns JSON:   │   │
│   │ {               │   │
│   │   category,     │   │
│   │   object_type,  │   │
│   │   color,        │   │
│   │   brand,        │   │
│   │   features...   │   │
│   │ }               │   │
│   └─────────────────┘   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Stored in database     │
│  with item report       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Matching engine uses   │
│  structured fields to   │
│  find potential matches │
└─────────────────────────┘
```

## Matching Algorithm

The AI provides understanding; the application controls scoring:

| Factor | Weight | Source |
|--------|--------|--------|
| Object type | 25% | AI-extracted |
| Category | 15% | AI-extracted |
| Color | 15% | AI-extracted |
| Brand | 10% | AI-extracted |
| Text similarity | 15% | User descriptions |
| Image similarity | 10% | aHash (average hash) Hamming distance |
| Location | 5% | User input |
| Temporal | 5% | User input |

**Important**: The LLM does NOT generate the match percentage. The score is computed deterministically by the matching engine. The LLM only generates the human-readable explanation.

## Configuration

```env
# Use "ollama" for real AI, "mock" for demo mode
AI_PROVIDER=ollama

# Vision model (llava:7b, llava:3b, moondream2, etc.)
AI_MODEL=llava:7b

# Ollama API URL
AI_BASE_URL=http://localhost:11434

# Embedding model
EMBEDDING_MODEL=nomic-embed-text
```

## Open-Source AI Credits

- **LLaVA**: Based on Llama architecture, open-weight
- **Ollama**: Open-source model runner (MIT License)
- **nomic-embed-text**: Open-weight text embedding model (Apache 2.0)
