import pytest
from app.ai.mock import MockAIProvider
from app.ai.base import ItemAnalysis


class TestMockAIProvider:
    @pytest.mark.asyncio
    async def test_analyze_item_with_description(self):
        provider = MockAIProvider()
        result = await provider.analyze_item("", "Black iPhone 13 with blue case")

        assert result.category == "electronics"
        assert result.object_type == "phone"
        assert result.color == "black"
        assert result.brand == "apple"

    @pytest.mark.asyncio
    async def test_analyze_item_empty_description(self):
        provider = MockAIProvider()
        result = await provider.analyze_item("", "")

        assert result.category == "other"
        assert result.confidence == 0.7

    @pytest.mark.asyncio
    async def test_generate_embedding(self):
        provider = MockAIProvider()
        embedding = await provider.generate_embedding("test text")

        assert isinstance(embedding, list)
        assert len(embedding) > 0

    @pytest.mark.asyncio
    async def test_explain_match(self):
        provider = MockAIProvider()
        analysis1 = ItemAnalysis(
            category="electronics",
            object_type="smartphone",
            color="black",
            brand="apple",
        )
        analysis2 = ItemAnalysis(
            category="electronics",
            object_type="smartphone",
            color="black",
            brand="apple",
        )

        explanation = await provider.explain_match(
            analysis1, analysis2,
            "Library", "Library",
            "2026-10-05T10:00:00", "2026-10-05T11:00:00",
        )

        assert "smartphone" in explanation
        assert "black" in explanation
