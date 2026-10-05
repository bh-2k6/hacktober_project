import pytest
from app.matching.engine import compute_match_score, generate_explanation, _jaccard_similarity, _embedding_similarity


class TestMatching:
    def test_matching_lost_found_items(self):
        lost = {
            "object_type": "smartphone",
            "category": "electronics",
            "color": "black",
            "brand": "apple",
            "description": "iPhone with blue case",
            "title": "iPhone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "aabbccdd",
            "embedding": None,
        }
        found = {
            "object_type": "smartphone",
            "category": "electronics",
            "color": "black",
            "brand": "apple",
            "description": "iPhone with blue case",
            "title": "iPhone",
            "location": "Library",
            "date_time": "2026-10-05T11:00:00",
            "image_phash": "aabbccdd",
            "embedding": None,
        }

        score, factors = compute_match_score(lost, found)
        assert score > 0.7
        assert factors["object_type"] == 1.0
        assert factors["color"] == 1.0
        assert factors["brand"] == 1.0

    def test_no_possible_matches(self):
        lost = {
            "object_type": "smartphone",
            "category": "electronics",
            "color": "black",
            "brand": "apple",
            "description": "iPhone",
            "title": "iPhone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "aabbccdd",
            "embedding": None,
        }
        found = {
            "object_type": "umbrella",
            "category": "accessories",
            "color": "red",
            "brand": "",
            "description": "Red umbrella",
            "title": "Umbrella",
            "location": "Gym",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "11223344",
            "embedding": None,
        }

        score, factors = compute_match_score(lost, found)
        assert score < 0.3

    def test_embedding_similarity(self):
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]
        emb3 = [0.0, 1.0, 0.0]

        assert _embedding_similarity(emb1, emb2) == 1.0
        assert _embedding_similarity(emb1, emb3) == 0.0

    def test_embedding_fallback_to_jaccard(self):
        lost = {
            "object_type": "phone",
            "category": "electronics",
            "color": "black",
            "brand": "samsung",
            "description": "Samsung Galaxy phone",
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
            "brand": "samsung",
            "description": "Samsung Galaxy phone",
            "title": "Phone",
            "location": "Library",
            "date_time": "2026-10-05T10:00:00",
            "image_phash": "",
            "embedding": None,
        }

        score, factors = compute_match_score(lost, found)
        assert factors["text_similarity"] > 0

    def test_jaccard_similarity(self):
        assert _jaccard_similarity("hello world", "hello world") == 1.0
        assert _jaccard_similarity("hello world", "goodbye world") == 1.0 / 3.0
        assert _jaccard_similarity("hello", "goodbye") == 0.0

    def test_generate_explanation(self):
        lost = {
            "object_type": "smartphone",
            "color": "black",
            "brand": "apple",
            "location": "Library",
        }
        found = {
            "object_type": "smartphone",
            "color": "black",
            "brand": "apple",
            "location": "Library",
        }
        factors = {
            "object_type": 1.0,
            "color": 1.0,
            "brand": 1.0,
            "location": 1.0,
            "temporal": 0.8,
            "text_similarity": 0.5,
            "image_similarity": 0.0,
            "category": 1.0,
        }

        explanation = generate_explanation(factors, lost, found)
        assert "smartphone" in explanation
        assert "black" in explanation
        assert "apple" in explanation
