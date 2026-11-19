"""Sensitivity (tornado), Monte Carlo ranges and triangulation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .model import Approach, MarketCase


def tornado(approach: Approach) -> pd.DataFrame:
    """Swing each driver from low to high while holding the others at base.

    Sorted by swing size – the top rows are the assumptions worth researching first.
    """
    base = approach.value("base")
    rows = []
    for d in approach.drivers:
        lo = approach.value(overrides={d.name: d.low})
        hi = approach.value(overrides={d.name: d.high})
        rows.append({"driver": d.name, "low_value": lo, "high_value": hi,
                     "swing": hi - lo, "swing_pct_of_base": (hi - lo) / base if base else np.nan})
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def monte_carlo(approach: Approach, n: int = 20_000, seed: int | None = 1) -> np.ndarray:
    """Sample every driver from a triangular(low, base, high) distribution and multiply.

    Unlike "all lows × all lows", this gives a realistic range, because it's
    unlikely that every single assumption is at its extreme at the same time.
    """
    rng = np.random.default_rng(seed)
    out = np.ones(n)
    for d in approach.drivers:
        if d.low == d.high:
            out *= d.base
        else:
            out *= rng.triangular(d.low, d.base, d.high, size=n)
    return out


def summary(case: MarketCase, n: int = 20_000) -> pd.DataFrame:
    """One row per approach: deterministic low/base/high plus Monte Carlo P10/P50/P90."""
    rows = []
    for key, a in case.approaches.items():
        sims = monte_carlo(a, n=n)
        rows.append({
            "approach": a.label,
            "key": key,
            "all_low": a.value("low"),
            "base": a.value("base"),
            "all_high": a.value("high"),
            "p10": float(np.percentile(sims, 10)),
            "p50": float(np.percentile(sims, 50)),
            "p90": float(np.percentile(sims, 90)),
        })
    return pd.DataFrame(rows)


def triangulation_gap(case: MarketCase) -> float | None:
    """Ratio between the highest and lowest base estimate across approaches.

    Rule of thumb: if two independent approaches are within ~30% of each other
    the estimate is reasonably robust; beyond 2× something structural is off.
    """
    bases = [a.value("base") for a in case.approaches.values()]
    if len(bases) < 2 or min(bases) <= 0:
        return None
    return max(bases) / min(bases)
