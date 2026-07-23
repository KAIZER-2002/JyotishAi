from typing import Sequence
from app.domain.yoga_detection import YogaRule
from app.domain.pancha_mahapurusha_yoga import PanchaMahapurushaYogaRule
from app.domain.gaja_kesari_yoga import GajaKesariYogaRule
from app.domain.budhaditya_yoga import BudhadityaYogaRule
from app.domain.chandra_mangala_yoga import ChandraMangalaYogaRule
from app.domain.raj_yoga import RajYogaRule
from app.domain.dhana_yoga import DhanaYogaRule


class YogaRuleRegistry:
    """
    Registry responsible for instantiating and providing the collection
    of all currently implemented YogaRule instances used by the application.
    """

    def __init__(self) -> None:
        self._rules: Sequence[YogaRule] = (
            PanchaMahapurushaYogaRule(),
            GajaKesariYogaRule(),
            BudhadityaYogaRule(),
            ChandraMangalaYogaRule(),
            RajYogaRule(),
            DhanaYogaRule(),
        )

    def get_rules(self) -> Sequence[YogaRule]:
        """
        Returns all registered YogaRule instances.
        """
        return self._rules
