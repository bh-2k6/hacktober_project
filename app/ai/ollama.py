import json
import base64
import requests
from typing import List
from .base import AIProvider, ItemAnalysis
from app.config import AI_MODEL, AI_BASE_URL, EMBEDDING_MODEL

ANALYSIS_PROMPT = """Analyze this image of a lost or found item. Extract structured information about the item.

Respond with ONLY valid JSON in this exact format (no markdown, no explanation):
{
  "category": "electronics|clothing|accessories|books|sports|other",
  "object_type": "specific item type (e.g., smartphone, backpack, umbrella)",
  "color": "primary color (e.g., black, blue, red)",
  "brand": "brand name if visible, empty string if not",
  "characteristics": ["list of visible characteristics"],
  "distinctive_features": ["scratches, stickers, patterns, or other identifying marks"],
  "visible_text": "any text visible on the item, empty string if none",
  "other_attributes": {"key": "value"} ,
  "confidence": 0.0 to 1.0
}

Be precise and only include information you can actually see in the image."""

EXPLANATION_PROMPT = """You are helping match lost and found items on a college campus.

Item 1 (lost): {item1_desc}
- Category: {item1_category}
- Type: {item1_type}
- Color: {item1_color}
- Brand: {item1_brand}
- Features: {item1_features}
- Location: {location1}
- Time: {time1}

Item 2 (found): {item2_desc}
- Category: {item2_category}
- Type: {item2_type}
- Color: {item2_color}
- Brand: {item2_brand}
- Features: {item2_features}
- Location: {location2}
- Time: {time2}

In 2-3 sentences, explain why these items might be a match. Focus on the most important similarities. Do NOT claim they are definitely the same item - use cautious language like "might be" or "could be"."""


class OllamaAIProvider(AIProvider):
    def __init__(self):
        self.base_url = AI_BASE_URL.rstrip("/")
        self.model = AI_MODEL
        self.embedding_model = EMBEDDING_MODEL

    async def analyze_item(self, image_path: str, description: str) -> ItemAnalysis:
        try:
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode()

            prompt = ANALYSIS_PROMPT
            if description:
                prompt += f"\n\nAdditional context from the reporter: {description}"

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [image_b64],
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
                timeout=120,
            )
            response.raise_for_status()

            result = response.json()
            text = result.get("response", "{}")

            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            return ItemAnalysis(
                category=data.get("category", "other"),
                object_type=data.get("object_type", ""),
                color=data.get("color", ""),
                brand=data.get("brand", ""),
                characteristics=data.get("characteristics", []),
                distinctive_features=data.get("distinctive_features", []),
                visible_text=data.get("visible_text", ""),
                other_attributes=data.get("other_attributes", {}),
                confidence=data.get("confidence", 0.5),
            )
        except Exception as e:
            return ItemAnalysis(
                category="other",
                object_type="",
                color="",
                brand="",
                characteristics=[],
                distinctive_features=[],
                confidence=0.0,
            )

    async def generate_embedding(self, text: str) -> List[float]:
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception:
            return []

    async def explain_match(
        self,
        item1_analysis: ItemAnalysis,
        item2_analysis: ItemAnalysis,
        location1: str,
        location2: str,
        time1: str,
        time2: str,
    ) -> str:
        try:
            prompt = EXPLANATION_PROMPT.format(
                item1_desc=f"{item1_analysis.object_type} ({item1_analysis.color} {item1_analysis.brand})",
                item1_category=item1_analysis.category,
                item1_type=item1_analysis.object_type,
                item1_color=item1_analysis.color,
                item1_brand=item1_analysis.brand,
                item1_features=", ".join(item1_analysis.distinctive_features) if item1_analysis.distinctive_features else "none noted",
                location1=location1,
                time1=time1,
                item2_desc=f"{item2_analysis.object_type} ({item2_analysis.color} {item2_analysis.brand})",
                item2_category=item2_analysis.category,
                item2_type=item2_analysis.object_type,
                item2_color=item2_analysis.color,
                item2_brand=item2_analysis.brand,
                item2_features=", ".join(item2_analysis.distinctive_features) if item2_analysis.distinctive_features else "none noted",
                location2=location2,
                time2=time2,
            )

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "These items share some similar characteristics.")
        except Exception:
            return "These items share some similar characteristics based on their descriptions."
