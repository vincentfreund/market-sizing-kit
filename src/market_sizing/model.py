"""Core model: drivers, approaches and the TAM → SAM → SOM funnel.

A market size estimate is written as a chain of drivers that multiply:

    revenue pool = households × share that buys × purchases / year × price

Every driver gets a LOW, BASE and HIGH value plus a source. That's the habit
consultants care about: each number is explicit, has a range, and can be
challenged on its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import prod
from pathlib import Path

import yaml


@dataclass
class Driver:
    name: str
    low: float
    base: float
    high: float
    unit: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        # PyYAML reads "83.5e6" (no sign in the exponent) as a string, so coerce.
        for attr in ("low", "base", "high"):
            try:
                setattr(self, attr, float(getattr(self, attr)))
            except (TypeError, ValueError):
                raise ValueError(f"Driver '{self.name}': {attr} is not a number") from None
        if not (self.low <= self.base <= self.high):
            raise ValueError(
                f"Driver '{self.name}': need low <= base <= high, got "
                f"{self.low} / {self.base} / {self.high}"
            )


@dataclass
class Approach:
    key: str
    label: str
    drivers: list[Driver]

    def value(self, case: str = "base", overrides: dict[str, float] | None = None) -> float:
        overrides = overrides or {}
        return prod(overrides.get(d.name, getattr(d, case)) for d in self.drivers)


@dataclass
class MarketCase:
    name: str
    question: str
    currency: str
    year: int | str
    approaches: dict[str, Approach]
    primary: str
    sam: list[Driver] = field(default_factory=list)
    som: list[Driver] = field(default_factory=list)
    notes: str = ""

    @property
    def primary_approach(self) -> Approach:
        return self.approaches[self.primary]

    def funnel(self, case: str = "base") -> dict[str, float]:
        """TAM from the primary approach, then SAM and SOM filters on top."""
        tam = self.primary_approach.value(case)
        sam = tam * prod(getattr(d, case) for d in self.sam)
        som = sam * prod(getattr(d, case) for d in self.som)
        return {"TAM": tam, "SAM": sam, "SOM": som}


def _drivers(raw: list[dict]) -> list[Driver]:
    return [Driver(**d) for d in raw or []]


def load_case(path: str | Path) -> MarketCase:
    """Load a case from YAML (see cases/_template.yaml)."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    approaches = {
        key: Approach(key=key, label=a.get("label", key), drivers=_drivers(a["drivers"]))
        for key, a in raw["approaches"].items()
    }
    primary = raw.get("primary", next(iter(approaches)))
    if primary not in approaches:
        raise ValueError(f"primary approach '{primary}' not found")
    funnel = raw.get("funnel", {}) or {}
    return MarketCase(
        name=raw["name"],
        question=raw["question"],
        currency=raw.get("currency", "EUR"),
        year=raw.get("year", ""),
        approaches=approaches,
        primary=primary,
        sam=_drivers(funnel.get("sam")),
        som=_drivers(funnel.get("som")),
        notes=raw.get("notes", ""),
    )
