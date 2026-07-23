from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.yoga_rule_registry import YogaRuleRegistry
from app.domain.pancha_mahapurusha_yoga import PanchaMahapurushaYogaRule
from app.domain.gaja_kesari_yoga import GajaKesariYogaRule
from app.domain.budhaditya_yoga import BudhadityaYogaRule
from app.domain.chandra_mangala_yoga import ChandraMangalaYogaRule
from app.domain.raj_yoga import RajYogaRule
from app.domain.dhana_yoga import DhanaYogaRule


def test_yoga_rule_registry_instantiates_rules() -> None:
    registry = YogaRuleRegistry()
    rules = registry.get_rules()

    assert len(rules) == 6
    assert any(isinstance(rule, PanchaMahapurushaYogaRule) for rule in rules)
    assert any(isinstance(rule, GajaKesariYogaRule) for rule in rules)
    assert any(isinstance(rule, BudhadityaYogaRule) for rule in rules)
    assert any(isinstance(rule, ChandraMangalaYogaRule) for rule in rules)
    assert any(isinstance(rule, RajYogaRule) for rule in rules)
    assert any(isinstance(rule, DhanaYogaRule) for rule in rules)
