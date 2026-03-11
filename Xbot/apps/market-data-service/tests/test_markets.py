from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "main.py"
SPEC = spec_from_file_location("market_data_main", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
list_markets = MODULE.list_markets


def test_markets_non_empty():
    payload = list_markets()
    assert payload["count"] > 0
    assert len(payload["items"]) == payload["count"]
