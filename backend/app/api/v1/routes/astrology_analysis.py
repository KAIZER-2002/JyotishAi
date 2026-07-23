from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.ephemeris.exceptions import EphemerisException
from app.infrastructure.ephemeris.service import SwissEphemerisService
from app.schemas.astrology_analysis.request import AstrologyAnalysisRequest
from app.schemas.astrology_analysis.response import AstrologyAnalysisResponse
from app.services.astrology.astrology_analysis_service import AstrologyAnalysisService
from app.services.astrology.calculators.birth_chart_calculator import (
    BirthChartCalculator,
)
from app.services.astrology.calculators.dasamsa_calculator import DasamsaCalculator
from app.services.astrology.calculators.navamsa_calculator import NavamsaCalculator
from app.services.astrology.calculators.planet_calculator import PlanetCalculator
from app.services.astrology.calculators.shastiamsa_calculator import (
    ShastiamsaCalculator,
)
from app.services.astrology.calculators.house_calculator import HouseCalculator
from app.services.astrology.calculators.vimshottari_dasha_calculator import (
    VimshottariDashaCalculator,
)

router = APIRouter(prefix="/astrology", tags=["Astrology"])


def get_astrology_analysis_service() -> AstrologyAnalysisService:
    """Dependency to provide an AstrologyAnalysisService instance."""
    ephemeris_service = SwissEphemerisService()
    planet_calculator = PlanetCalculator(ephemeris_service)
    house_calculator = HouseCalculator(ephemeris_service)
    birth_chart_calculator = BirthChartCalculator(
        ephemeris_service=ephemeris_service,
        planet_calculator=planet_calculator,
        house_calculator=house_calculator,
    )
    navamsa_calculator = NavamsaCalculator()
    dasamsa_calculator = DasamsaCalculator()
    shastiamsa_calculator = ShastiamsaCalculator()
    vimshottari_dasha_calculator = VimshottariDashaCalculator()
    
    return AstrologyAnalysisService(
        birth_chart_calculator,
        navamsa_calculator,
        dasamsa_calculator,
        shastiamsa_calculator,
        vimshottari_dasha_calculator,
    )


@router.post(
    "/analysis",
    response_model=AstrologyAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a complete astrology analysis",
    description="Generates a complete Vedic astrology analysis including birth chart, divisional charts, and dasha information.",
)
async def generate_astrology_analysis(
    request: AstrologyAnalysisRequest,
    astrology_analysis_service: AstrologyAnalysisService = Depends(get_astrology_analysis_service),
) -> AstrologyAnalysisResponse:
    """
    Endpoint to generate a complete astrology analysis.
    
    Returns:
        Complete astrology analysis including all charts and dashas
    """
    try:
        analysis = await astrology_analysis_service.generate_analysis(
            birth_datetime=request.date,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
        )
        
        # Convert the analysis to response format (this will need to be implemented)
        # For now, we'll return the analysis directly since we're just exposing the service
        # In a real implementation, we would convert the domain objects to Pydantic models
        # This is a simplified implementation for now
        
        # Note: In a full implementation, we would need to:
        # 1. Convert the domain objects (Chart, Mahadasha, etc.) to Pydantic models
        # 2. Add yoga detection and interpretation analysis
        
        return AstrologyAnalysisResponse(
            birth_chart=analysis.birth_chart,
            navamsa_chart=analysis.navamsa_chart,
            dasamsa_chart=analysis.dasamsa_chart,
            shastiamsa_chart=analysis.shastiamsa_chart,
            vimshottari_dashas=analysis.vimshottari_dashas,
            # These would be populated with actual analysis data in a complete implementation
            current_mahadasha=None,
            current_antardasha=None,
            detected_yogas=[],
            interpretation=None,
            yoga_analysis=None,
        )
    except EphemerisException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating the astrology analysis: {str(e)}",
        )