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


class TestExcludeAndRenormalize:
    def test_complete_metadata_perfect_match(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Blue Jansport Backpack",
            "description": "Blue Jansport backpack with laptop compartment",
            "location": "Library 2nd floor", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": [1.0, 0.5, 0.3],
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Blue Jansport Backpack",
            "description": "Blue Jansport backpack with laptop compartment",
            "location": "Library 2nd floor", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": [1.0, 0.5, 0.3],
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_complete_metadata_genuine_mismatch(self):
        lost = {
            "object_type": "smartphone", "category": "electronics", "color": "black",
            "brand": "apple", "title": "iPhone",
            "description": "iPhone with blue case",
            "location": "Library", "date_time": "2026-10-05T10:00:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "umbrella", "category": "accessories", "color": "red",
            "brand": "", "title": "Umbrella",
            "description": "Red umbrella",
            "location": "Gym", "date_time": "2026-10-05T10:00:00",
            "image_phash": "11223344", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score < 0.3

    def test_both_colors_missing(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "Jansport", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "Jansport", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_one_color_missing(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "Jansport", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_both_brands_missing(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "", "title": "Backpack",
            "description": "Blue backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "", "title": "Backpack",
            "description": "Blue backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_color_and_brand_missing(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_color_brand_location_temporal_missing(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "", "date_time": "",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "", "title": "Backpack",
            "description": "Jansport backpack",
            "location": "", "date_time": "",
            "image_phash": "aabbccdd", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_no_image(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Backpack",
            "description": "Blue Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Backpack",
            "description": "Blue Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_one_image_missing(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Backpack",
            "description": "Blue Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Jansport", "title": "Backpack",
            "description": "Blue Jansport backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_jaccard_fallback(self):
        lost = {
            "object_type": "phone", "category": "electronics", "color": "black",
            "brand": "samsung", "title": "Phone",
            "description": "Samsung Galaxy phone",
            "location": "Library", "date_time": "2026-10-05T10:00:00",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "phone", "category": "electronics", "color": "black",
            "brand": "samsung", "title": "Phone",
            "description": "Samsung Galaxy phone",
            "location": "Library", "date_time": "2026-10-05T10:00:00",
            "image_phash": "", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert "embedding_similarity" not in factors
        assert factors["text_similarity"] > 0
        assert score == 1.0

    def test_object_type_only(self):
        lost = {
            "object_type": "backpack", "category": "", "color": "",
            "brand": "", "title": "",
            "description": "",
            "location": "", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "", "color": "",
            "brand": "", "title": "",
            "description": "",
            "location": "", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 0.625

    def test_object_type_and_location(self):
        lost = {
            "object_type": "backpack", "category": "", "color": "",
            "brand": "", "title": "",
            "description": "",
            "location": "Library", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "", "color": "",
            "brand": "", "title": "",
            "description": "",
            "location": "Library", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == pytest.approx(0.75)

    def test_object_type_and_category(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "", "title": "",
            "description": "",
            "location": "", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "",
            "brand": "", "title": "",
            "description": "",
            "location": "", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_object_type_category_color(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "", "title": "",
            "description": "",
            "location": "", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "", "title": "",
            "description": "",
            "location": "", "date_time": "",
            "image_phash": "", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0

    def test_conflicting_known_attributes(self):
        lost = {
            "object_type": "backpack", "category": "bags", "color": "red",
            "brand": "Nike", "title": "Backpack",
            "description": "Red Nike backpack",
            "location": "Library", "date_time": "2025-08-12T10:00",
            "image_phash": "aabbccdd", "embedding": None,
        }
        found = {
            "object_type": "backpack", "category": "bags", "color": "blue",
            "brand": "Adidas", "title": "Backpack",
            "description": "Blue Adidas backpack",
            "location": "Gym", "date_time": "2025-08-15T10:00",
            "image_phash": "11223344", "embedding": None,
        }
        score, factors = compute_match_score(lost, found)
        assert factors["color"] == 0.0
        assert factors["brand"] < 1.0
        assert score < 1.0

    def test_heart_scenario(self):
        lost = {
            "object_type": "heart", "category": "other", "color": "",
            "brand": "", "title": "Heart",
            "description": "Heart",
            "location": "AB3-611", "date_time": "2025-08-12T12:12",
            "image_phash": "f7c7c7c7c3c3f5ff", "embedding": [3.0],
        }
        found = {
            "object_type": "heart", "category": "other", "color": "",
            "brand": "", "title": "Heart",
            "description": "Heart",
            "location": "AB3-611", "date_time": "2025-08-12T12:12",
            "image_phash": "f7c7c7c7c3c3f5ff", "embedding": [3.0],
        }
        score, factors = compute_match_score(lost, found)
        assert score == 1.0
        assert factors["image_similarity"] == 1.0
        assert factors["embedding_similarity"] == 1.0
        assert factors["text_similarity"] == 1.0
