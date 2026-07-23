import datetime
from typing import Optional, AsyncGenerator

from app.domain.llm_provider import LLMProvider, LLMRequest, LLMResponse
from app.domain.prompt import StructuredPrompt, PromptMessage, PromptRole
from app.exceptions.llm import GeminiProviderException
from app.infrastructure.ephemeris.service import SwissEphemerisService
from app.schemas.astrology import BirthChartRequest
from app.services.astrology.astrology_analysis_service import AstrologyAnalysisService
from app.services.astrology.calculators.birth_chart_calculator import BirthChartCalculator
from app.services.astrology.calculators.dasamsa_calculator import DasamsaCalculator
from app.services.astrology.calculators.house_calculator import HouseCalculator
from app.services.astrology.calculators.navamsa_calculator import NavamsaCalculator
from app.services.astrology.calculators.planet_calculator import PlanetCalculator
from app.services.astrology.calculators.shastiamsa_calculator import ShastiamsaCalculator
from app.services.astrology.calculators.vimshottari_dasha_calculator import (
    VimshottariDashaCalculator,
)
from app.services.astrology.interpretation_service import InterpretationService
from app.services.astrology.prompt_builder_service import PromptBuilderService
from app.services.astrology.yoga_analysis_service import YogaAnalysisService
from app.services.llm.providers.gemini_provider import GeminiProvider


class AstrologyChatService:
    """
    Coordinates Swiss Ephemeris calculations, Yoga analysis,
    interpretations, prompt building, and LLM providers.
    """

    def __init__(
        self,
        analysis_service: Optional[AstrologyAnalysisService] = None,
        yoga_analysis_service: Optional[YogaAnalysisService] = None,
        interpretation_service: Optional[InterpretationService] = None,
        prompt_builder_service: Optional[PromptBuilderService] = None,
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        # Default composition
        ephemeris_service = SwissEphemerisService()
        planet_calculator = PlanetCalculator(ephemeris_service)
        house_calculator = HouseCalculator(ephemeris_service)
        birth_chart_calculator = BirthChartCalculator(
            ephemeris_service=ephemeris_service,
            planet_calculator=planet_calculator,
            house_calculator=house_calculator,
        )

        self._analysis_service = analysis_service or AstrologyAnalysisService(
            birth_chart_calculator=birth_chart_calculator,
            navamsa_calculator=NavamsaCalculator(),
            dasamsa_calculator=DasamsaCalculator(),
            shastiamsa_calculator=ShastiamsaCalculator(),
            vimshottari_dasha_calculator=VimshottariDashaCalculator(),
        )
        self._yoga_analysis_service = yoga_analysis_service or YogaAnalysisService()
        self._interpretation_service = interpretation_service or InterpretationService()
        self._prompt_builder_service = prompt_builder_service or PromptBuilderService()
        self._llm_provider = llm_provider or GeminiProvider()

    async def chat(
        self,
        birth_data: BirthChartRequest,
        user_query: str,
        history: Optional[list] = None,
        model_hint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Coordinates full pipeline:
        1. AstrologyAnalysis (charts + Vimshottari Dashas)
        2. YogaAnalysis (all 6 rules + scores)
        3. InterpretationReport (deterministic life areas)
        4. StructuredPrompt (optionally incorporating conversation history)
        5. Gemini completion
        """
        # 1. Generate full analysis
        analysis = await self._analysis_service.generate_analysis(
            birth_datetime=birth_data.date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            ayanamsa=birth_data.ayanamsa,
            house_system=birth_data.house_system,
        )

        # 2. Analyze yogas
        yogas = self._yoga_analysis_service.analyze(analysis)

        # 3. Interpret life areas
        interpretations = self._interpretation_service.interpret(yogas, analysis)

        # 4. Build prompt
        if history:
            # Reconstruct structured prompt using the first query in history
            first_query = history[0].content
            base_prompt = self._prompt_builder_service.build(
                astrology_analysis=analysis,
                yoga_analysis=yogas,
                interpretation_report=interpretations,
                user_query=first_query,
            )
            
            combined_messages = list(base_prompt.messages)
            
            # Map history messages (excluding the first user query, which is already in base_prompt)
            for msg in history[1:]:
                role = PromptRole.USER if msg.role == "user" else PromptRole.ASSISTANT
                combined_messages.append(PromptMessage(role=role, content=msg.content))
                
            # Append the current query if not already present at the end
            if not combined_messages or combined_messages[-1].content != user_query:
                combined_messages.append(PromptMessage(role=PromptRole.USER, content=user_query))
            
            prompt = StructuredPrompt(
                sections=base_prompt.sections,
                messages=tuple(combined_messages),
                metadata=base_prompt.metadata,
            )
        else:
            prompt = self._prompt_builder_service.build(
                astrology_analysis=analysis,
                yoga_analysis=yogas,
                interpretation_report=interpretations,
                user_query=user_query,
            )

        # 5. Call LLM
        request = LLMRequest(
            prompt=prompt,
            temperature=temperature,
            model_hint=model_hint,
            max_tokens=max_tokens,
        )
        return await self._llm_provider.acomplete(request)

    async def stream_chat(
        self,
        birth_data: BirthChartRequest,
        user_query: str,
        history: Optional[list] = None,
        model_hint: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[LLMResponse, None]:
        """
        Streaming variant — yields partial LLMResponse chunks as they arrive.
        Uses the same prompt-building pipeline as chat(), but calls provider.astream().
        """
        # 1. Generate full analysis
        analysis = await self._analysis_service.generate_analysis(
            birth_datetime=birth_data.date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            ayanamsa=birth_data.ayanamsa,
            house_system=birth_data.house_system,
        )

        # 2. Analyze yogas
        yogas = self._yoga_analysis_service.analyze(analysis)

        # 3. Interpret life areas
        interpretations = self._interpretation_service.interpret(yogas, analysis)

        # 4. Build prompt (same history logic as chat())
        if history:
            first_query = history[0].content
            base_prompt = self._prompt_builder_service.build(
                astrology_analysis=analysis,
                yoga_analysis=yogas,
                interpretation_report=interpretations,
                user_query=first_query,
            )
            combined_messages = list(base_prompt.messages)
            for msg in history[1:]:
                role = PromptRole.USER if msg.role == "user" else PromptRole.ASSISTANT
                combined_messages.append(PromptMessage(role=role, content=msg.content))
            if not combined_messages or combined_messages[-1].content != user_query:
                combined_messages.append(PromptMessage(role=PromptRole.USER, content=user_query))
            prompt = StructuredPrompt(
                sections=base_prompt.sections,
                messages=tuple(combined_messages),
                metadata=base_prompt.metadata,
            )
        else:
            prompt = self._prompt_builder_service.build(
                astrology_analysis=analysis,
                yoga_analysis=yogas,
                interpretation_report=interpretations,
                user_query=user_query,
            )

        # 5. Stream from LLM
        request = LLMRequest(
            prompt=prompt,
            temperature=temperature,
            model_hint=model_hint,
            max_tokens=max_tokens,
        )
        async for chunk in self._llm_provider.astream(request):
            yield chunk
