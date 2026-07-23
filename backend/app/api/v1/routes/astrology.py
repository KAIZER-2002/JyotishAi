from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.db.models.user import User
from app.infrastructure.ephemeris.exceptions import EphemerisException
from app.infrastructure.ephemeris.service import SwissEphemerisService
from app.schemas.astrology import (
    BirthChartRequest,
    BirthChartResponse,
    DasamsaChartResponse,
    NavamsaChartResponse,
    ShastiamsaChartResponse,
    VimshottariDashaResponse,
)
from app.services.astrology.astrology_service import AstrologyService
from app.services.astrology.calculators.birth_chart_calculator import (
    BirthChartCalculator,
)
from app.services.astrology.calculators.dasamsa_calculator import DasamsaCalculator
from app.services.astrology.calculators.house_calculator import HouseCalculator
from app.services.astrology.calculators.navamsa_calculator import NavamsaCalculator
from app.services.astrology.calculators.planet_calculator import PlanetCalculator
from app.services.astrology.calculators.shastiamsa_calculator import (
    ShastiamsaCalculator,
)


router = APIRouter(prefix="/astrology", tags=["Astrology"])


def get_astrology_service() -> AstrologyService:
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
    return AstrologyService(
        birth_chart_calculator,
        navamsa_calculator,
        dasamsa_calculator,
        shastiamsa_calculator,
    )


@router.post(
    "/birth-chart",
    response_model=BirthChartResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a birth chart",
    description="Generates a Vedic birth chart for the provided birth data.",
)
async def generate_birth_chart(
    request: BirthChartRequest,
    astrology_service: AstrologyService = Depends(get_astrology_service),
    current_user: User = Depends(get_current_user),
) -> BirthChartResponse:
    try:
        return await astrology_service.generate_birth_chart(
            birth_datetime=request.date,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
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
            detail=f"An unexpected error occurred while generating the birth chart: {str(e)}",
        )


@router.post(
    "/navamsa",
    response_model=NavamsaChartResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Navamsa chart",
    description="Generates a D9 Navamsa chart for the provided birth data.",
)
async def generate_navamsa_chart(
    request: BirthChartRequest,
    astrology_service: AstrologyService = Depends(get_astrology_service),
    current_user: User = Depends(get_current_user),
) -> NavamsaChartResponse:
    try:
        return await astrology_service.generate_navamsa_chart(
            birth_datetime=request.date,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
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
            detail=f"An unexpected error occurred while generating the Navamsa chart: {str(e)}",
        )


@router.post(
    "/d10",
    response_model=DasamsaChartResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Dasamsa chart",
    description="Generates a D10 Dasamsa chart for the provided birth data.",
)
async def generate_dasamsa_chart(
    request: BirthChartRequest,
    astrology_service: AstrologyService = Depends(get_astrology_service),
    current_user: User = Depends(get_current_user),
) -> DasamsaChartResponse:
    try:
        return await astrology_service.generate_dasamsa_chart(
            birth_datetime=request.date,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
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
            detail=f"An unexpected error occurred while generating the Dasamsa chart: {str(e)}",
        )


@router.post(
    "/d60",
    response_model=ShastiamsaChartResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Shastiamsa chart",
    description="Generates a D60 Shastiamsa chart for the provided birth data.",
)
async def generate_shastiamsa_chart(
    request: BirthChartRequest,
    astrology_service: AstrologyService = Depends(get_astrology_service),
    current_user: User = Depends(get_current_user),
) -> ShastiamsaChartResponse:
    try:
        return await astrology_service.generate_shastiamsa_chart(
            birth_datetime=request.date,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
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
            detail=f"An unexpected error occurred while generating the Shastiamsa chart: {str(e)}",
        )


@router.post(
    "/vimshottari-dasha",
    response_model=VimshottariDashaResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a Vimshottari Dasha timeline",
    description="Generates a Vimshottari Dasha timeline for the provided birth data.",
)
async def generate_vimshottari_dasha(
    request: BirthChartRequest,
    astrology_service: AstrologyService = Depends(get_astrology_service),
    current_user: User = Depends(get_current_user),
) -> VimshottariDashaResponse:
    try:
        return await astrology_service.generate_vimshottari_dasha(
            birth_datetime=request.date,
            latitude=request.latitude,
            longitude=request.longitude,
            ayanamsa=request.ayanamsa,
            house_system=request.house_system,
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
            detail=f"An unexpected error occurred while generating the Vimshottari Dasha timeline: {str(e)}",
        )
