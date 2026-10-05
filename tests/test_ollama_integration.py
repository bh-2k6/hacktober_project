import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from app.database import init_db, get_db_connection
from app.matching.engine import compute_match_score
from app.ai.ollama import OllamaAIProvider
from app.ai.base import ItemAnalysis

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    with get_db_connection() as conn:
        conn.execute("DELETE FROM matches")
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM contact_requests")
    yield


def _mock_ollama_response(embedding=None, analysis_text=None):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    if embedding is not None:
        mock_response.json.return_value = {"embedding": embedding}
    elif analysis_text is not None:
        mock_response.json.return_value = {"response": analysis_text}
    else:
        mock_response.json.return_value = {"embedding": []}

    return mock_response


def _mock_analysis_json():
    return json.dumps({
        "category": "electronics",
        "object_type": "phone",
        "color": "black",
        "brand": "",
        "characteristics": [],
        "distinctive_features": [],
        "visible_text": "",
        "other_attributes": {},
        "confidence": 0.8,
    })


class TestOllamaUnavailable:
    def test_ollama_unavailable_embedding_graceful_fallback(self):
        with patch("app.ai.ollama.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("Ollama not available")

            with patch("app.config.AI_PROVIDER", "ollama"):
                response = client.post(
                    "/api/items",
                    data={
                        "type": "lost",
                        "title": "Test Phone",
                        "description": "A test phone",
                        "location": "Test Location",
                        "date_time": "2026-10-05T12:00:00",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["title"] == "Test Phone"

    def test_ollama_unavailable_embedding_stored_as_none(self):
        with patch("app.ai.ollama.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("Ollama not available")

            with patch("app.config.AI_PROVIDER", "ollama"):
                response = client.post(
                    "/api/items",
                    data={
                        "type": "lost",
                        "title": "Test Phone",
                        "description": "A test phone",
                        "location": "Test Location",
                        "date_time": "2026-10-05T12:00:00",
                    },
                )

                assert response.status_code == 200
                item_id = response.json()["id"]

                with get_db_connection() as conn:
                    row = conn.execute("SELECT embedding FROM items WHERE id = ?", (item_id,)).fetchone()
                    assert row["embedding"] is None

    def test_ollama_unavailable_matching_falls_back_to_jaccard(self):
        lost = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "black phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": None,
        }
        found = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "black phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": None,
        }

        score, factors = compute_match_score(lost, found)
        assert factors["text_similarity"] > 0
        assert score > 0.3

    def test_real_ollama_provider_generate_embedding_failure(self):
        provider = OllamaAIProvider()

        with patch("app.ai.ollama.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("Connection refused")

            import asyncio
            result = asyncio.run(provider.generate_embedding("test text"))

            assert result == []
            mock_post.assert_called_once()


class TestOllamaIntegration:
    def test_real_ollama_embedding_integration_path(self):
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_analysis = _mock_analysis_json()

        with patch("app.ai.ollama.requests.post") as mock_post:
            def side_effect(*args, **kwargs):
                if "/api/embeddings" in args[0]:
                    return _mock_ollama_response(embedding=mock_embedding)
                elif "/api/generate" in args[0]:
                    return _mock_ollama_response(analysis_text=mock_analysis)
                return _mock_ollama_response()

            mock_post.side_effect = side_effect

            with patch("app.config.AI_PROVIDER", "ollama"):
                response = client.post(
                    "/api/items",
                    data={
                        "type": "lost",
                        "title": "Test Phone",
                        "description": "A test phone",
                        "location": "Test Location",
                        "date_time": "2026-10-05T12:00:00",
                    },
                )

                assert response.status_code == 200
                item_id = response.json()["id"]

                embedding_calls = [
                    call for call in mock_post.call_args_list
                    if "/api/embeddings" in call[0][0]
                ]
                assert len(embedding_calls) == 1

                with get_db_connection() as conn:
                    row = conn.execute("SELECT embedding FROM items WHERE id = ?", (item_id,)).fetchone()
                    assert row["embedding"] is not None
                    stored_embedding = json.loads(row["embedding"])
                    assert stored_embedding == mock_embedding

    def test_real_ollama_provider_generate_embedding_success(self):
        mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        provider = OllamaAIProvider()

        with patch("app.ai.ollama.requests.post") as mock_post:
            mock_post.return_value = _mock_ollama_response(embedding=mock_embedding)

            import asyncio
            result = asyncio.run(provider.generate_embedding("test text"))

            assert result == mock_embedding
            mock_post.assert_called_once()

            call_args = mock_post.call_args
            assert "/api/embeddings" in call_args[0][0]
            assert call_args[1]["json"]["prompt"] == "test text"

    def test_compute_match_score_uses_cosine_embedding_similarity(self):
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]

        lost = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": emb1,
        }
        found = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": emb2,
        }

        score, factors = compute_match_score(lost, found)

        assert "embedding_similarity" in factors
        assert factors["embedding_similarity"] == 1.0
        assert factors["text_similarity"] == 1.0

    def test_compute_match_score_embedding_vs_jaccard_difference(self):
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [0.0, 1.0, 0.0]

        lost = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": emb1,
        }
        found = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": emb2,
        }

        score, factors = compute_match_score(lost, found)

        assert "embedding_similarity" in factors
        assert factors["embedding_similarity"] == 0.0

    def test_compute_match_score_prefers_embeddings_when_available(self):
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]

        lost_with_emb = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": emb1,
        }
        found_with_emb = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": emb2,
        }

        lost_without_emb = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": None,
        }
        found_without_emb = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": None,
        }

        score_with, factors_with = compute_match_score(lost_with_emb, found_with_emb)
        score_without, factors_without = compute_match_score(lost_without_emb, found_without_emb)

        assert "embedding_similarity" in factors_with
        assert factors_with["embedding_similarity"] == 1.0
        assert "embedding_similarity" not in factors_without

        assert score_with > 0
        assert score_without > 0

    def test_final_score_changes_with_embeddings_vs_jaccard(self):
        from app.matching.engine import WEIGHTS

        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]

        lost_base = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "black smartphone with case",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
        }

        found_base = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "",
            "description": "mobile device",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
        }

        lost_with_emb = {**lost_base, "embedding": emb1}
        found_with_emb = {**found_base, "embedding": emb2}
        lost_without_emb = {**lost_base, "embedding": None}
        found_without_emb = {**found_base, "embedding": None}

        score_with, factors_with = compute_match_score(lost_with_emb, found_with_emb)
        score_without, factors_without = compute_match_score(lost_without_emb, found_without_emb)

        assert "embedding_similarity" in factors_with
        assert factors_with["embedding_similarity"] == 1.0
        assert factors_with["text_similarity"] == 1.0

        assert "embedding_similarity" not in factors_without
        assert factors_without["text_similarity"] < 1.0

        comparable_with = {
            "object_type", "category", "color",
            "text_similarity", "location", "temporal",
        }
        comparable_weight_with = sum(WEIGHTS[k] for k in comparable_with)
        expected_score_with = (
            sum(factors_with[k] * WEIGHTS[k] for k in comparable_with)
            / comparable_weight_with
        )
        if comparable_weight_with < 0.40:
            expected_score_with *= comparable_weight_with / 0.40
        expected_score_with = max(0.0, min(1.0, expected_score_with))

        assert abs(score_with - expected_score_with) < 0.001

        assert score_with > score_without
