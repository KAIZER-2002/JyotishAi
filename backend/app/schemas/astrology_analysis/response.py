from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.astrology import (
    BirthChartResponse,
    NavamsaChartResponse,
    DasamsaChartResponse,
    ShastiamsaChartResponse,
    VimshottariDashaResponse,
)
from app.domain.yoga_detection import Yoga

class AstrologyAnalysisResponse(BaseModel):
    """Complete API response for a complete astrology analysis."""
    birth_chart: BirthChartResponse
    navamsa_chart: NavamsaChartResponse
    dasamsa_chart: DasamsaChartResponse
    shastiamsa_chart: ShastiamsaChartResponse
    vimshottari_dashas: VimshottariDashaResponse
    current_mahadasha: Optional[str] = None
    current_antardasha: Optional[str] = None
    detected_yogas: List[Yoga] = []
    interpretation: Optional[str] = None
    yoga_analysis: Optional[str] = None