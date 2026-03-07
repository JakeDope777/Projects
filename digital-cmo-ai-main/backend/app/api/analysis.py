"""
Business Analysis API endpoints.

GET/POST /analysis/market      - Market research
POST     /analysis/competitors - Competitor analysis
POST     /analysis/swot        - SWOT analysis
POST     /analysis/pestel      - PESTEL analysis
POST     /analysis/personas    - Persona generation
"""

from fastapi import APIRouter, Depends

from ..db.schemas import (
    MarketAnalysisRequest,
    CompetitorAnalysisRequest,
    SWOTRequest,
    PESTELRequest,
    PersonaRequest,
    AnalysisResponse,
)
from ..modules.business_analysis import BusinessAnalysisModule

router = APIRouter(prefix="/analysis", tags=["Business Analysis"])

# Module instance
_module = BusinessAnalysisModule()


def get_module() -> BusinessAnalysisModule:
    return _module


@router.post("/market", response_model=AnalysisResponse)
async def analyze_market(
    request: MarketAnalysisRequest,
    module: BusinessAnalysisModule = Depends(get_module),
):
    """Conduct market research and return insights."""
    result = await module.analyze_market(request.query, request.context)
    return AnalysisResponse(**result)


@router.post("/competitors", response_model=AnalysisResponse)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    module: BusinessAnalysisModule = Depends(get_module),
):
    """Analyse competitors and produce a comparative matrix."""
    result = await module.analyze_competitors(
        company_names=request.company_names,
        context=request.context,
    )
    return AnalysisResponse(**result)


@router.post("/swot", response_model=AnalysisResponse)
async def generate_swot(
    request: SWOTRequest,
    module: BusinessAnalysisModule = Depends(get_module),
):
    """Generate a SWOT analysis for the specified subject."""
    result = await module.generate_swot(
        subject=request.subject,
        context=request.context,
    )
    return AnalysisResponse(**result)


@router.post("/pestel", response_model=AnalysisResponse)
async def generate_pestel(
    request: PESTELRequest,
    module: BusinessAnalysisModule = Depends(get_module),
):
    """Generate a PESTEL analysis for the specified subject."""
    result = await module.generate_pestel(
        subject=request.subject,
        context=request.context,
    )
    return AnalysisResponse(**result)


@router.post("/personas", response_model=AnalysisResponse)
async def create_personas(
    request: PersonaRequest,
    module: BusinessAnalysisModule = Depends(get_module),
):
    """Generate buyer personas based on data and context."""
    result = await module.create_personas(
        request.data_source, request.num_personas, request.context
    )
    return AnalysisResponse(**result)
