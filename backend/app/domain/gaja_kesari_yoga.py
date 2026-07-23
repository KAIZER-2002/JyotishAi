from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext
from app.domain.zodiac import ZodiacSign


class GajaKesariYogaRule:
    def evaluate(self, context: YogaContext) -> YogaResult | None:
        moon = context.planet(PlanetType.MOON)
        jupiter = context.planet(PlanetType.JUPITER)
        if moon is None or jupiter is None:
            return None

        if not context.is_planet_in_kendra_from_planet(
            target_planet=PlanetType.JUPITER,
            reference_planet=PlanetType.MOON,
        ):
            return None

        return YogaResult(
            yoga=Yoga(
                key="gaja_kesari",
                name="Gaja Kesari Yoga",
                yoga_type=YogaType.GAJA_KESARI_YOGA,
                description="Jupiter occupies a kendra from the Moon.",
            ),
            strength=self._strength(context),
            involved_planets=(PlanetType.MOON, PlanetType.JUPITER),
            involved_houses=tuple(
                house
                for house in (moon.house_number, jupiter.house_number)
                if house is not None
            ),
            evidence=(
                f"Moon is in {moon.zodiac_sign.value}.",
                f"Jupiter is in {jupiter.zodiac_sign.value}.",
                "Jupiter is in a kendra from the Moon.",
            ),
        )

    def _strength(self, context: YogaContext) -> YogaStrength:
        if context.is_exalted(PlanetType.JUPITER):
            return YogaStrength.EXCEPTIONAL

        jupiter_sign = context.sign_of_planet(PlanetType.JUPITER)
        if jupiter_sign in (ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES):
            return YogaStrength.STRONG

        return YogaStrength.MODERATE
