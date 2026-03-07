"""
Unit tests for the Business Analysis Module.
"""

import pytest
from app.modules.business_analysis import BusinessAnalysisModule


@pytest.fixture
def module():
    return BusinessAnalysisModule()


class TestBusinessAnalysisModule:
    """Tests for business analysis functions."""

    @pytest.mark.asyncio
    async def test_analyze_market(self, module):
        result = await module.analyze_market("SaaS marketing in Europe")
        assert "insights" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_analyze_competitors(self, module):
        result = await module.analyze_competitors(["Company A", "Company B"])
        assert "analysis" in result
        assert "insights" in result

    @pytest.mark.asyncio
    async def test_generate_swot(self, module):
        result = await module.generate_swot("Our new product launch")
        assert "analysis" in result
        assert "swot" in result["analysis"]

    @pytest.mark.asyncio
    async def test_generate_pestel(self, module):
        result = await module.generate_pestel("European tech market")
        assert "analysis" in result
        assert "pestel" in result["analysis"]

    @pytest.mark.asyncio
    async def test_create_personas(self, module):
        result = await module.create_personas("general", 3)
        assert "personas" in result
        assert "insights" in result

    @pytest.mark.asyncio
    async def test_handle_swot(self, module):
        result = await module.handle("Do a SWOT analysis for our product", {})
        assert "response" in result
        assert result["response"] != ""

    @pytest.mark.asyncio
    async def test_handle_general(self, module):
        result = await module.handle("Research the market for AI tools", {})
        assert "response" in result
