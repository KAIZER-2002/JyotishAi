from app.domain.planet_type import PlanetType
from app.domain.yoga import Yoga, YogaResult, YogaStrength, YogaType
from app.domain.yoga_detection import YogaContext
from app.domain.zodiac import ZodiacSign


class ChandraMangalaYogaRule:
    """
    Chandra Mangala Yoga is formed when the Moon (Chandra) and Mars (Mangala)
    are conjunct in the same zodiac sign or stand in an aspect relationship.
    """

    def evaluate(self, context: YogaContext) -> YogaResult | None:
        moon = context.planet(PlanetType.MOON)
        mars = context.planet(PlanetType.MARS)

        if moon is None or mars is None:
            return None

        is_conjunct = context.are_conjunct(PlanetType.MOON, PlanetType.MARS)
        aspects_moon = context.has_aspect(PlanetType.MARS, PlanetType.MOON)
        aspects_mars = context.has_aspect(PlanetType.MOON, PlanetType.MARS)

        if not (is_conjunct or aspects_moon or aspects_mars):
            return None

        # Build evidence
        evidence_list = [
            f"Moon is in {moon.zodiac_sign.value} in house {moon.house_number.value if moon.house_number else 'None'}.",
            f"Mars is in {mars.zodiac_sign.value} in house {mars.house_number.value if mars.house_number else 'None'}.",
        ]

        if is_conjunct:
            relationship_desc = "Moon and Mars are conjunct in the same sign."
        else:
            relationship_desc = "Moon and Mars share an aspect relationship."

        evidence_list.append(relationship_desc)

        return YogaResult(
            yoga=Yoga(
                key="chandra_mangala",
                name="Chandra Mangala Yoga",
                yoga_type=YogaType.CHANDRA_MANGALA_YOGA,
                description="Moon and Mars are in conjunction or aspect relationship.",
            ),
            strength=self._strength(moon.zodiac_sign, mars.zodiac_sign),
            involved_planets=(PlanetType.MOON, PlanetType.MARS),
            involved_houses=tuple(
                house
                for house in (moon.house_number, mars.house_number)
                if house is not None
            ),
            evidence=tuple(evidence_list),
        )

    def _strength(self, moon_sign: ZodiacSign, mars_sign: ZodiacSign) -> YogaStrength:
        # Exaltation: Moon in Taurus, Mars in Capricorn
        if moon_sign == ZodiacSign.TAURUS or mars_sign == ZodiacSign.CAPRICORN:
            return YogaStrength.EXCEPTIONAL

        # Own sign: Moon in Cancer, Mars in Aries/Scorpio
        if moon_sign == ZodiacSign.CANCER or mars_sign in (ZodiacSign.ARIES, ZodiacSign.SCORPIO):
            return YogaStrength.STRONG

        return YogaStrength.MODERATE
