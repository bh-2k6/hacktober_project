import re
import math
from collections import Counter
from typing import List
from .base import AIProvider, ItemAnalysis

CATEGORY_KEYWORDS = {
    "electronics": ["phone", "laptop", "charger", "cable", "earbuds", "headphone", "tablet", "camera", "keyboard", "mouse", "speaker", "usb", "adapter", "power bank"],
    "clothing": ["jacket", "hoodie", "sweater", "shirt", "pants", "jeans", "coat", "scarf", "glove", "hat", "beanie", "socks", "shoes", "sneaker", "backpack"],
    "accessories": ["watch", "wallet", "purse", "bag", "umbrella", "glasses", "sunglasses", "jewelry", "necklace", "bracelet", "ring", "belt", "keychain"],
    "books": ["book", "notebook", "textbook", "journal", "planner", "folder", "binder", "pen", "pencil", "highlighter", "calculator"],
    "sports": ["ball", "racket", "bat", "helmet", "bike", "skateboard", "frisbee", "yoga mat", "dumbbell", "water bottle"],
    "other": [],
}

COLOR_KEYWORDS = {
    "black": ["black", "dark"],
    "white": ["white", "light", "cream", "ivory"],
    "red": ["red", "crimson", "maroon", "burgundy"],
    "blue": ["blue", "navy", "sky", "teal", "azure"],
    "green": ["green", "olive", "mint", "forest", "lime"],
    "yellow": ["yellow", "gold", "amber", "mustard"],
    "orange": ["orange", "peach", "coral", "tangerine"],
    "purple": ["purple", "violet", "lavender", "magenta", "plum"],
    "pink": ["pink", "rose", "fuchsia", "magenta"],
    "brown": ["brown", "tan", "beige", "khaki", "chocolate"],
    "gray": ["gray", "grey", "silver", "charcoal", "slate"],
    "silver": ["silver", "metallic", "chrome"],
    "gold": ["gold", "golden", "brass"],
}

BRAND_KEYWORDS = {
    "apple": ["apple", "iphone", "ipad", "macbook", "airpods", "airpod"],
    "samsung": ["samsung", "galaxy"],
    "sony": ["sony", "playstation", "ps5", "ps4"],
    "nike": ["nike", "air max", "jordan"],
    "adidas": ["adidas", "stan smith"],
    "dell": ["dell", "alienware"],
    "hp": ["hp", "pavilion", "omen"],
    "lenovo": ["lenovo", "thinkpad", "ideapad"],
    "asus": ["asus", "rog", "zenbook"],
    "microsoft": ["microsoft", "surface", "xbox"],
    "logitech": ["logitech"],
    "canon": ["canon", "eos"],
    "nikon": ["nikon"],
    "bose": ["bose"],
    "jbl": ["jbl"],
    "anker": ["anker"],
    "moleskine": ["moleskine"],
    "pilot": ["pilot"],
    "sharpie": ["sharpie"],
}


def _extract_category(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "other"


def _extract_color(text: str) -> str:
    text_lower = text.lower()
    for color, keywords in COLOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return color
    return ""


def _extract_brand(text: str) -> str:
    text_lower = text.lower()
    for brand, keywords in BRAND_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return brand
    return ""


def _extract_object_type(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return kw
    words = re.findall(r'\b\w+\b', text_lower)
    if len(words) >= 2:
        return " ".join(words[:2])
    return words[0] if words else "item"


def _tokenize(text: str) -> List[str]:
    return re.findall(r'\b\w+\b', text.lower())


class MockAIProvider(AIProvider):
    async def analyze_item(self, image_path: str, description: str) -> ItemAnalysis:
        combined = f"{description}".strip()
        if not combined:
            combined = "unknown item"

        category = _extract_category(combined)
        color = _extract_color(combined)
        brand = _extract_brand(combined)
        object_type = _extract_object_type(combined)

        characteristics = []
        if color:
            characteristics.append(f"{color} color")
        if brand:
            characteristics.append(f"{brand} brand")

        distinctive_features = []
        words = _tokenize(combined)
        for word in words:
            if len(word) > 4 and word not in distinctive_features:
                distinctive_features.append(word)
            if len(distinctive_features) >= 3:
                break

        return ItemAnalysis(
            category=category,
            object_type=object_type,
            color=color,
            brand=brand,
            characteristics=characteristics,
            distinctive_features=distinctive_features,
            confidence=0.7,
        )

    async def generate_embedding(self, text: str) -> List[float]:
        tokens = _tokenize(text)
        vocab = sorted(set(tokens))
        return [float(tokens.count(w)) for w in vocab] if vocab else [0.0]

    async def explain_match(
        self,
        item1_analysis: ItemAnalysis,
        item2_analysis: ItemAnalysis,
        location1: str,
        location2: str,
        time1: str,
        time2: str,
    ) -> str:
        reasons = []

        if item1_analysis.object_type == item2_analysis.object_type and item1_analysis.object_type:
            reasons.append(f"both describe {item1_analysis.object_type}s")

        if item1_analysis.color and item2_analysis.color and item1_analysis.color == item2_analysis.color:
            reasons.append(f"both are {item1_analysis.color}")

        if item1_analysis.brand and item2_analysis.brand and item1_analysis.brand == item2_analysis.brand:
            reasons.append(f"both are {item1_analysis.brand} brand")

        if location1 == location2:
            reasons.append(f"reported at the same location ({location1})")
        elif location1.split()[0] == location2.split()[0]:
            reasons.append(f"reported near each other ({location1} and {location2})")

        if not reasons:
            return "These items share some similar characteristics."

        return "Potential match because " + ", ".join(reasons) + "."
