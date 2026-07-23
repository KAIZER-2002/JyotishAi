from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.ascendant import Ascendant
from app.domain.astrology_analysis import AstrologyAnalysis
from app.domain.chart import Chart
from app.domain.chart_type import ChartType
from app.domain.house import House
from app.domain.house_number import HouseNumber
from app.domain.nakshatra import Nakshatra
from app.domain.planet import Planet
from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext, YogaDetectionEngine, YogaEvaluator
from app.domain.zodiac import ZodiacSign


def planet(
    planet_type: PlanetType,
    longitude: float,
    sign: ZodiacSign,
    house_number: HouseNumber,
) -> Planet:
    return Planet(
        planet=planet_type,
        longitude=longitude,
        latitude=0.0,
        zodiac_sign=sign,
        house_number=house_number,
        retrograde=False,
        nakshatra=Nakshatra.ASHWINI,
        pada=1,
        degree_within_sign=longitude % 30.0,
    )


def chart(*planets: Planet) -> Chart:
    return Chart(
        ascendant=Ascendant(
            zodiac_sign=ZodiacSign.ARIES,
            longitude=0.0,
            nakshatra=Nakshatra.ASHWINI,
            pada=1,
            degree_within_sign=0.0,
        ),
        planets=planets,
        houses=tuple(
            House(
                house_number=house_number,
                start_longitude=float(index * 30),
                end_longitude=float((index + 1) * 30),
            )
            for index, house_number in enumerate(HouseNumber)
        ),
    )


def analysis() -> AstrologyAnalysis:
    birth_chart = chart(
        planet(PlanetType.SUN, 10.0, ZodiacSign.ARIES, HouseNumber.FIRST),
        planet(PlanetType.MOON, 40.0, ZodiacSign.TAURUS, HouseNumber.SECOND),
        planet(PlanetType.MARS, 100.0, ZodiacSign.CANCER, HouseNumber.FOURTH),
        planet(PlanetType.SATURN, 190.0, ZodiacSign.LIBRA, HouseNumber.SEVENTH),
    )
    navamsa_chart = chart(
        planet(PlanetType.SUN, 280.0, ZodiacSign.CAPRICORN, HouseNumber.TENTH)
    )
    return AstrologyAnalysis(
        birth_chart=birth_chart,
        navamsa_chart=navamsa_chart,
        dasamsa_chart=chart(),
        shastiamsa_chart=chart(),
        vimshottari_dashas=(),
    )


def yoga(key: str) -> Yoga:
    return Yoga(
        key=key,
        name=key,
        yoga_type=YogaType.OTHER,
    )


class RecordingRule:
    def __init__(
        self,
        name: str,
        calls: list[str],
        result: Yoga | None = None,
    ) -> None:
        self._name = name
        self._calls = calls
        self._result = result

    def evaluate(self, context: YogaContext) -> Yoga | None:
        self._calls.append(self._name)
        assert context.planet(PlanetType.SUN) is not None
        return self._result


class FailingRule:
    def __init__(self, name: str, calls: list[str]) -> None:
        self._name = name
        self._calls = calls

    def evaluate(self, context: YogaContext) -> Yoga | None:
        self._calls.append(self._name)
        raise ValueError("Rule failed.")


def test_yoga_detection_empty_rule_set_returns_no_results() -> None:
    engine = YogaDetectionEngine(rules=())

    results = engine.detect(YogaContext(analysis()))

    assert results == ()


def test_yoga_detection_evaluates_multiple_rules() -> None:
    calls: list[str] = []
    first_yoga = yoga("first")
    second_yoga = yoga("second")
    engine = YogaDetectionEngine(
        rules=(
            RecordingRule("first", calls, first_yoga),
            RecordingRule("second", calls, second_yoga),
        )
    )

    results = engine.detect(YogaContext(analysis()))

    assert calls == ["first", "second"]
    assert tuple(result.yoga for result in results) == (first_yoga, second_yoga)


def test_yoga_detection_preserves_rule_execution_order() -> None:
    calls: list[str] = []
    engine = YogaDetectionEngine(
        rules=(
            RecordingRule("one", calls),
            RecordingRule("two", calls),
            RecordingRule("three", calls),
        )
    )

    engine.detect(YogaContext(analysis()))

    assert calls == ["one", "two", "three"]


def test_yoga_detection_aggregates_detected_results() -> None:
    first_yoga = yoga("first")
    third_yoga = yoga("third")
    engine = YogaDetectionEngine(
        rules=(
            RecordingRule("first", [], first_yoga),
            RecordingRule("second", [], None),
            RecordingRule("third", [], third_yoga),
        )
    )

    results = engine.detect(YogaContext(analysis()))

    assert tuple(result.yoga for result in results) == (first_yoga, third_yoga)
    assert all(result.strength is YogaStrength.MODERATE for result in results)


def test_yoga_detection_isolates_rule_errors() -> None:
    calls: list[str] = []
    successful_yoga = yoga("successful")
    engine = YogaDetectionEngine(
        rules=(
            FailingRule("failing", calls),
            RecordingRule("successful", calls, successful_yoga),
        )
    )

    results = engine.detect(YogaContext(analysis()))

    assert calls == ["failing", "successful"]
    assert tuple(result.yoga for result in results) == (successful_yoga,)


def test_yoga_evaluator_can_propagate_rule_errors() -> None:
    calls: list[str] = []
    engine = YogaDetectionEngine(
        rules=(FailingRule("failing", calls),),
        evaluator=YogaEvaluator(isolate_rule_errors=False),
    )

    with pytest.raises(ValueError, match="Rule failed."):
        engine.detect(YogaContext(analysis()))


def test_yoga_context_helpers() -> None:
    context = YogaContext(analysis())

    assert context.chart() is context.analysis.birth_chart
    assert context.chart(ChartType.NAVAMSA) is context.analysis.navamsa_chart
    assert context.planet(PlanetType.SUN).zodiac_sign is ZodiacSign.ARIES
    assert context.house(HouseNumber.FIRST).start_longitude == 0.0
    assert context.sign_of_planet(PlanetType.MOON) is ZodiacSign.TAURUS
    assert context.house_lord(HouseNumber.FIRST) is PlanetType.MARS
    assert tuple(
        planet.planet for planet in context.planets_in_house(HouseNumber.FIRST)
    ) == (PlanetType.SUN,)
    assert tuple(
        planet.planet for planet in context.planets_in_sign(ZodiacSign.ARIES)
    ) == (PlanetType.SUN,)
    assert context.are_conjunct(PlanetType.SUN, PlanetType.SUN)
    assert context.has_aspect(PlanetType.SUN, PlanetType.SATURN)
    assert context.is_exalted(PlanetType.SUN)
    assert context.is_debilitated(PlanetType.MARS)
    assert (
        context.sign_of_planet(PlanetType.SUN, ChartType.NAVAMSA)
        is ZodiacSign.CAPRICORN
    )


def test_yoga_context_rejects_unsupported_divisional_chart() -> None:
    context = YogaContext(analysis())

    with pytest.raises(ValueError, match="Unsupported chart type"):
        context.chart(ChartType.DREKKANA)
