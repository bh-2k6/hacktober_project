from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class ItemAnalysis:
    category: str = ""
    object_type: str = ""
    color: str = ""
    brand: str = ""
    characteristics: List[str] = field(default_factory=list)
    distinctive_features: List[str] = field(default_factory=list)
    visible_text: str = ""
    other_attributes: dict = field(default_factory=dict)
    confidence: float = 0.0


class AIProvider(ABC):
    @abstractmethod
    async def analyze_item(self, image_path: str, description: str) -> ItemAnalysis:
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def explain_match(
        self,
        item1_analysis: ItemAnalysis,
        item2_analysis: ItemAnalysis,
        location1: str,
        location2: str,
        time1: str,
        time2: str,
    ) -> str:
        pass
