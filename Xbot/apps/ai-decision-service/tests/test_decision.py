from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "main.py"
SPEC = spec_from_file_location("ai_decision_main", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DecisionRequest = MODULE.DecisionRequest
generate_decision = MODULE.generate_decision


def test_generate_decision_is_bounded():
    result = generate_decision(
        DecisionRequest(
            market_id="poly-1",
            context={
                "momentum_score": 0.5,
                "volatility_score": 0.1,
                "mid_price": 0.61,
                "deployable_capital": 1000
            }
        )
    )
    assert 0 <= result.confidence <= 1
    assert result.quantity > 0
    assert result.limit_price > 0
