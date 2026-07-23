from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from types import MappingProxyType
from typing import Final, Mapping, Tuple


class DashaLord(Enum):
    """
    Planetary lords used in the Vimshottari Dasha system.
    """
    KETU = "Ketu"
    VENUS = "Venus"
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    RAHU = "Rahu"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    MERCURY = "Mercury"


class DashaLevel(Enum):
    """
    Supported and planned Vimshottari Dasha nesting levels.
    """
    MAHADASHA = "Mahadasha"
    ANTARDASHA = "Antardasha"
    PRATYANTAR_DASHA = "Pratyantar Dasha"
    SUKSHMA_DASHA = "Sukshma Dasha"
    PRANA_DASHA = "Prana Dasha"


VIMSHOTTARI_SEQUENCE: Final[Tuple[DashaLord, ...]] = (
    DashaLord.KETU,
    DashaLord.VENUS,
    DashaLord.SUN,
    DashaLord.MOON,
    DashaLord.MARS,
    DashaLord.RAHU,
    DashaLord.JUPITER,
    DashaLord.SATURN,
    DashaLord.MERCURY,
)


PLANETARY_PERIOD_YEARS: Final[Mapping[DashaLord, int]] = MappingProxyType(
    {
        DashaLord.KETU: 7,
        DashaLord.VENUS: 20,
        DashaLord.SUN: 6,
        DashaLord.MOON: 10,
        DashaLord.MARS: 7,
        DashaLord.RAHU: 18,
        DashaLord.JUPITER: 16,
        DashaLord.SATURN: 19,
        DashaLord.MERCURY: 17,
    }
)


@dataclass(frozen=True)
class DashaPeriod:
    """
    Base immutable domain model for a Vimshottari Dasha period.
    """
    lord: DashaLord
    start_datetime: datetime
    end_datetime: datetime
    level: DashaLevel
    sub_periods: Tuple["DashaPeriod", ...] = ()

    @property
    def duration(self) -> timedelta:
        return self.end_datetime - self.start_datetime


@dataclass(frozen=True)
class PratyantarDasha(DashaPeriod):
    """
    Immutable domain model for a Pratyantar Dasha period.
    """
    level: DashaLevel = field(
        default=DashaLevel.PRATYANTAR_DASHA,
        init=False,
    )
    parent_antardasha: "Antardasha | None" = None


@dataclass(frozen=True)
class Antardasha(DashaPeriod):
    """
    Immutable domain model for an Antardasha period.
    """
    level: DashaLevel = field(default=DashaLevel.ANTARDASHA, init=False)
    sub_periods: Tuple[PratyantarDasha, ...] = ()
    parent_mahadasha: "Mahadasha | None" = None


@dataclass(frozen=True)
class Mahadasha(DashaPeriod):
    """
    Immutable domain model for a Mahadasha period.
    """
    level: DashaLevel = field(default=DashaLevel.MAHADASHA, init=False)
    sub_periods: Tuple[Antardasha, ...] = ()
