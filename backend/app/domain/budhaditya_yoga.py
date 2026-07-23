from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext
from app.domain.zodiac import ZodiacSign


class BudhadityaYogaRule:
    """
    Budhaditya Yoga is formed when the Sun (Aditya) and Mercury (Budha)
    are conjunct in the same zodiac sign.
    """

    def evaluate(self, context: YogaContext) -> YogaResult | None:
        sun = context.planet(PlanetType.SUN)
        mercury = context.planet(PlanetType.MERCURY)

        if sun is None or mercury is None:
            return None

        # Check if they are conjunct (in the same sign)
        if not context.are_conjunct(PlanetType.SUN, PlanetType.MERCURY):
            return None

        return YogaResult(
            yoga=Yoga(
                key="budhaditya",
                name="Budhaditya Yoga",
                yoga_type=YogaType.BUDHADITYA_YOGA,
                description="Sun and Mercury are conjunct in the same sign.",
            ),
            strength=self._strength(sun.zodiac_sign),
            involved_planets=(PlanetType.SUN, PlanetType.MERCURY),
            involved_houses=tuple(
                house
                for house in (sun.house_number, mercury.house_number)
                if house is not None
            ),
            evidence=(
                f"Sun is in {sun.zodiac_sign.value}.",
                f"Mercury is in {mercury.zodiac_sign.value}.",
                "Sun and Mercury are conjunct in the same sign.",
            ),
        )

    def _strength(self, sign: ZodiacSign) -> YogaStrength:
        # Exalted conditions: Sun is exalted in Aries, Mercury in Virgo
        if sign in (ZodiacSign.ARIES, ZodiacSign.VIRGO):
            return YogaStrength.EXCEPTIONAL

        # Own sign conditions: Sun owns Leo, Mercury owns Gemini/Virgo
        if sign in (ZodiacSign.LEO, ZodiacSign.GEMINI):
            return YogaStrength.STRONG

        return YogaStrength.MODERATE
