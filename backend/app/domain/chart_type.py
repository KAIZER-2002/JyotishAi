from enum import Enum


class ChartType(Enum):
    """
    Supported divisional charts (Vargas).
    """
    RASI = "Rasi"
    NAVAMSA = "Navamsa"
    DREKKANA = "Drekkana"
    DASAMSA = "Dasamsa"
    SHASTIAMSA = "Shastiamsa"
    HORA = "Hora"
