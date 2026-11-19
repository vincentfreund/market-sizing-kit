from pathlib import Path

import pytest
from openpyxl import load_workbook

from market_sizing import (
    Approach, Driver, build_report, load_case, monte_carlo, summary, tornado, triangulation_gap,
)

CASES = Path(__file__).resolve().parents[1] / "cases"


def approach():
    return Approach("a", "A", [
        Driver("people", 100, 100, 100),
        Driver("share", 0.1, 0.2, 0.3, unit="%"),
        Driver("price", 5, 10, 20),
    ])


def test_product():
    a = approach()
    assert a.value("base") == pytest.approx(200)
    assert a.value("low") == pytest.approx(50)
    assert a.value("high") == pytest.approx(600)


def test_driver_order_validated():
    with pytest.raises(ValueError):
        Driver("bad", 3, 2, 1)


def test_driver_coerces_yaml_strings():
    assert Driver("x", "1e6", "2e6", "3e6").base == 2e6


def test_tornado_sorted_and_correct():
    t = tornado(approach())
    assert list(t["driver"])[:2] == ["price", "share"]
    assert t.loc[t.driver == "price", "low_value"].item() == pytest.approx(100)
    assert t.loc[t.driver == "people", "swing"].item() == 0


def test_monte_carlo_within_bounds():
    s = monte_carlo(approach(), n=5000)
    assert s.min() >= 50 and s.max() <= 600


@pytest.mark.parametrize("name", ["padel_germany", "specialty_coffee_munich"])
def test_example_cases(name, tmp_path):
    case = load_case(CASES / f"{name}.yaml")
    f = case.funnel()
    assert f["TAM"] > f["SAM"] > f["SOM"] > 0
    s = summary(case, n=2000)
    assert (s["p10"] <= s["p90"]).all()
    assert triangulation_gap(case) >= 1

    report = build_report(case, tmp_path, name)
    assert report.exists()
    wb = load_workbook(report.parent / "model.xlsx")
    formulas = [c.value for row in wb["Model"].iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    assert any("PRODUCT" in f for f in formulas)


def test_template_loads():
    case = load_case(CASES / "_template.yaml")
    assert case.primary == "bottom_up"
