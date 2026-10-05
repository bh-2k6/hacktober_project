import math
import re
from datetime import datetime
from typing import List, Tuple
from difflib import SequenceMatcher

WEIGHTS = {
    "object_type": 0.25,
    "category": 0.15,
    "color": 0.15,
    "brand": 0.10,
    "text_similarity": 0.15,
    "image_similarity": 0.10,
    "location": 0.05,
    "temporal": 0.05,
}

SIMILAR_COLORS = {
    "black": ["gray", "charcoal", "dark"],
    "white": ["silver", "cream", "light"],
    "blue": ["navy", "teal", "azure"],
    "red": ["maroon", "burgundy", "crimson"],
    "green": ["olive", "mint", "forest"],
    "yellow": ["gold", "amber"],
    "orange": ["peach", "coral"],
    "purple": ["violet", "lavender", "plum"],
    "pink": ["rose", "fuchsia"],
    "brown": ["tan", "beige", "khaki"],
    "gray": ["silver", "charcoal", "slate"],
    "silver": ["gray", "metallic"],
    "gold": ["yellow", "golden", "brass"],
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r'\b\w+\b', text.lower())


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _jaccard_similarity(text1: str, text2: str) -> float:
    tokens1 = set(_tokenize(text1))
    tokens2 = set(_tokenize(text2))
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)


def _string_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def _color_similarity(c1: str, c2: str) -> float:
    if not c1 or not c2:
        return 0.0
    if c1.lower() == c2.lower():
        return 1.0
    similar = SIMILAR_COLORS.get(c1.lower(), [])
    if c2.lower() in similar:
        return 0.7
    similar = SIMILAR_COLORS.get(c2.lower(), [])
    if c1.lower() in similar:
        return 0.7
    return 0.0


def _ahash_similarity(hash1: str, hash2: str) -> float:
    if not hash1 or not hash2:
        return 0.0
    if len(hash1) != len(hash2):
        return 0.0
    try:
        h1 = int(hash1, 16)
        h2 = int(hash2, 16)
        max_bits = len(hash1) * 4
        xor = h1 ^ h2
        hamming = bin(xor).count("1")
        return 1.0 - (hamming / max_bits)
    except (ValueError, TypeError):
        return 0.0


def _location_similarity(loc1: str, loc2: str) -> float:
    if not loc1 or not loc2:
        return 0.0
    if loc1.lower() == loc2.lower():
        return 1.0
    words1 = set(_tokenize(loc1))
    words2 = set(_tokenize(loc2))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    return len(intersection) / max(len(words1), len(words2))


def _temporal_similarity(time1: str, time2: str) -> float:
    try:
        dt1 = datetime.fromisoformat(time1.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(time2.replace("Z", "+00:00"))
        diff_hours = abs((dt1 - dt2).total_seconds()) / 3600

        if diff_hours <= 1:
            return 1.0
        elif diff_hours <= 24:
            return 0.8
        elif diff_hours <= 72:
            return 0.5
        elif diff_hours <= 168:
            return 0.2
        else:
            return 0.0
    except (ValueError, TypeError):
        return 0.0


def _embedding_similarity(emb1: List[float], emb2: List[float]) -> float:
    if not emb1 or not emb2:
        return 0.0
    if len(emb1) != len(emb2):
        return 0.0
    return _cosine_similarity(emb1, emb2)


def compute_match_score(
    lost_item: dict,
    found_item: dict,
) -> Tuple[float, dict]:
    factors = {}

    obj_type_sim = _string_similarity(
        lost_item.get("object_type", ""),
        found_item.get("object_type", ""),
    )
    factors["object_type"] = obj_type_sim

    cat_sim = _string_similarity(
        lost_item.get("category", ""),
        found_item.get("category", ""),
    )
    factors["category"] = cat_sim

    color_sim = _color_similarity(
        lost_item.get("color", ""),
        found_item.get("color", ""),
    )
    factors["color"] = color_sim

    brand_sim = _string_similarity(
        lost_item.get("brand", ""),
        found_item.get("brand", ""),
    )
    factors["brand"] = brand_sim

    lost_embedding = lost_item.get("embedding")
    found_embedding = found_item.get("embedding")

    if lost_embedding and found_embedding:
        factors["embedding_similarity"] = _embedding_similarity(lost_embedding, found_embedding)
        factors["text_similarity"] = factors["embedding_similarity"]
    else:
        factors["text_similarity"] = _jaccard_similarity(
            lost_item.get("description", "") + " " + lost_item.get("title", ""),
            found_item.get("description", "") + " " + found_item.get("title", ""),
        )

    img_sim = _ahash_similarity(
        lost_item.get("image_phash", ""),
        found_item.get("image_phash", ""),
    )
    factors["image_similarity"] = img_sim

    loc_sim = _location_similarity(
        lost_item.get("location", ""),
        found_item.get("location", ""),
    )
    factors["location"] = loc_sim

    time_sim = _temporal_similarity(
        lost_item.get("date_time", ""),
        found_item.get("date_time", ""),
    )
    factors["temporal"] = time_sim

    score = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
    score = max(0.0, min(1.0, score))

    return score, factors


def generate_explanation(factors: dict, lost_item: dict, found_item: dict) -> str:
    reasons = []

    if factors["object_type"] >= 0.8:
        obj_type = lost_item.get("object_type") or found_item.get("object_type")
        if obj_type:
            reasons.append(f"both describe {obj_type}s")

    if factors["color"] >= 0.7:
        color = lost_item.get("color") or found_item.get("color")
        if color:
            reasons.append(f"both are {color}")

    if factors["brand"] >= 0.8:
        brand = lost_item.get("brand") or found_item.get("brand")
        if brand:
            reasons.append(f"both are {brand} brand")

    if factors["location"] >= 0.5:
        loc1 = lost_item.get("location", "")
        loc2 = found_item.get("location", "")
        if loc1 == loc2:
            reasons.append(f"reported at the same location ({loc1})")
        else:
            reasons.append(f"reported near each other ({loc1} and {loc2})")

    if factors["temporal"] >= 0.5:
        reasons.append("reported within a similar timeframe")

    if factors["image_similarity"] >= 0.6:
        reasons.append("images show visual similarity")

    if not reasons:
        return "These items share some similar characteristics based on their descriptions."

    return "Potential match because " + ", ".join(reasons) + "."
