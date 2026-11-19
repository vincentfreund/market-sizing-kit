"""Matplotlib charts in a clean, consulting-style look."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK = "#1f2933"
MUTED = "#9aa5b1"
ACCENT = "#2f6f8f"
LIGHT = "#cfe3ec"


def human(x: float, currency: str = "") -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    for div, suf in ((1e9, "bn"), (1e6, "m"), (1e3, "k")):
        if x >= div:
            return f"{sign}{currency} {x / div:,.1f}{suf}".strip()
    return f"{sign}{currency} {x:,.0f}".strip()


def _style(ax) -> None:
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=INK, length=0)
    ax.grid(axis="x", color="#e4e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def football_field(summary: pd.DataFrame, currency: str, title: str, path: Path) -> Path:
    """Horizontal range bars: light = all-low…all-high, dark = P10…P90, tick = base."""
    fig, ax = plt.subplots(figsize=(9, 1.2 + 0.9 * len(summary)))
    for i, r in enumerate(summary.itertuples()):
        y = len(summary) - 1 - i
        ax.barh(y, r.all_high - r.all_low, left=r.all_low, height=0.55, color=LIGHT)
        ax.barh(y, r.p90 - r.p10, left=r.p10, height=0.55, color=ACCENT)
        ax.plot([r.base, r.base], [y - 0.32, y + 0.32], color=INK, linewidth=2)
        ax.text(r.all_high, y, "  " + human(r.base, currency), va="center", color=INK, fontsize=9)
    ax.set_yticks(range(len(summary)))
    ax.set_yticklabels(list(summary["approach"])[::-1])
    ax.xaxis.set_major_formatter(lambda x, _: human(x))
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.set_xlabel("light = all-low to all-high  ·  dark = P10–P90 (Monte Carlo)  ·  line = base case",
                  color=MUTED, fontsize=8, loc="left", labelpad=10)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def tornado_chart(tor: pd.DataFrame, base: float, currency: str, title: str, path: Path) -> Path:
    """Classic tornado: biggest swing on top, bars centred on the base value."""
    tor = tor.iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 1.2 + 0.55 * len(tor)))
    y = range(len(tor))
    ax.barh(y, tor["low_value"] - base, left=base, color=MUTED, height=0.6, label="driver at low")
    ax.barh(y, tor["high_value"] - base, left=base, color=ACCENT, height=0.6, label="driver at high")
    ax.axvline(base, color=INK, linewidth=1)
    ax.set_yticks(list(y))
    ax.set_yticklabels(tor["driver"])
    ax.xaxis.set_major_formatter(lambda x, _: human(x))
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
