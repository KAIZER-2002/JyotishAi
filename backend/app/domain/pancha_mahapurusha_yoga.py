from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping, Tuple

from app.domain.house_number import HouseNumber
from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext
from app.domain.zodiac import ZodiacSign


KENDRA_HOUSES: Final[Tuple[HouseNumber, ...]] = (
    HouseNumber.FIRST,
    HouseNumber.FOURTH,
    HouseNumber.SEVENTH,
    HouseNumber.TENTH,
)


@dataclass(frozen=True)
class MahapurushaDefinition:
    key: str
    name: str
    planet: PlanetType
    own_signs: Tuple[ZodiacSign, ...]


PANCHA_MAHAPURUSHA_DEFINITIONS: Final[Tuple[MahapurushaDefinition, ...]] = (
    MahapurushaDefinition(
        key="ruchaka",
        name="Ruchaka Yoga",
        planet=PlanetType.MARS,
        own_signs=(ZodiacSign.ARIES, ZodiacSign.SCORPIO),
    ),
    MahapurushaDefinition(
        key="bhadra",
        name="Bhadra Yoga",
        planet=PlanetType.MERCURY,
        own_signs=(ZodiacSign.GEMINI, ZodiacSign.VIRGO),
    ),
    MahapurushaDefinition(
        key="hamsa",
        name="Hamsa Yoga",
        planet=PlanetType.JUPITER,
        own_signs=(ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES),
    ),
    MahapurushaDefinition(
        key="malavya",
        name="Malavya Yoga",
        planet=PlanetType.VENUS,
        own_signs=(ZodiacSign.TAURUS, ZodiacSign.LIBRA),
    ),
    MahapurushaDefinition(
        key="sasa",
        name="Sasa Yoga",
        planet=PlanetType.SATURN,
        own_signs=(ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS),
    ),
)

YOGA_DESCRIPTIONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "ruchaka": "Mars occupies a kendra in own sign or exaltation.",
        "bhadra": "Mercury occupies a kendra in own sign or exaltation.",
        "hamsa": "Jupiter occupies a kendra in own sign or exaltation.",
        "malavya": "Venus occupies a kendra in own sign or exaltation.",
        "sasa": "Saturn occupies a kendra in own sign or exaltation.",
    }
)


class PanchaMahapurushaYogaRule:
    def evaluate(self, context: YogaContext) -> Tuple[YogaResult, ...]:
        results: list[YogaResult] = []

        for definition in PANCHA_MAHAPURUSHA_DEFINITIONS:
            result = self._evaluate_definition(context, definition)
            if result is not None:
                results.append(result)

        return tuple(results)

    def _evaluate_definition(
        self,
        context: YogaContext,
        definition: MahapurushaDefinition,
    ) -> YogaResult | None:
        planet = context.planet(definition.planet)
        if planet is None or planet.house_number not in KENDRA_HOUSES:
            return None

        is_exalted = context.is_exalted(definition.planet)
        is_own_sign = planet.zodiac_sign in definition.own_signs
        if not is_exalted and not is_own_sign:
            return None

        return YogaResult(
            yoga=Yoga(
                key=definition.key,
                name=definition.name,
                yoga_type=YogaType.PANCHA_MAHAPURUSHA_YOGA,
                description=YOGA_DESCRIPTIONS[definition.key],
            ),
            strength=(
                YogaStrength.EXCEPTIONAL
                if is_exalted
                else YogaStrength.STRONG
            ),
            involved_planets=(definition.planet,),
            involved_houses=(planet.house_number,),
            evidence=(
                f"{definition.planet.value} is in {planet.zodiac_sign.value}.",
                f"{definition.planet.value} occupies house {planet.house_number.value}.",
            ),
        )
