"""Build a Markdown report with charts and an Excel model for a case."""

from __future__ import annotations

from pathlib import Path

from .analysis import summary, tornado, triangulation_gap
from .charts import football_field, human, tornado_chart
from .excel import export_excel
from .model import MarketCase


def _val(v: float, unit: str) -> str:
    if unit == "%":
        return f"{v:.1%}" if v < 0.1 else f"{v:.0%}"
    if abs(v) >= 1e5:
        return human(v)
    return f"{v:,.2f}".rstrip("0").rstrip(".")


def _drivers_table(drivers, currency: str) -> str:
    lines = ["| Driver | Low | Base | High | Unit | Source |", "|---|---:|---:|---:|---|---|"]
    for d in drivers:
        lo, ba, hi = (_val(x, d.unit) for x in (d.low, d.base, d.high))
        lines.append(f"| {d.name} | {lo} | {ba} | {hi} | {d.unit} | {d.source} |")
    return "\n".join(lines)


def build_report(case: MarketCase, out_dir: str | Path, slug: str) -> Path:
    out = Path(out_dir) / slug
    out.mkdir(parents=True, exist_ok=True)
    cur = case.currency

    summ = summary(case)
    football_field(summ, cur, f"{case.name}: estimates by approach", out / "football_field.png")

    md = [f"# {case.name}", "", f"> **Question:** {case.question}", "",
          f"Currency: {cur} · Year: {case.year}", ""]
    if case.notes:
        md += [case.notes.strip(), ""]

    md += ["## Answer", ""]
    f_base, f_low, f_high = case.funnel("base"), case.funnel("low"), case.funnel("high")
    md += ["| | Low | **Base** | High |", "|---|---:|---:|---:|"]
    for k in ("TAM", "SAM", "SOM"):
        if k == "SAM" and not case.sam:
            continue
        if k == "SOM" and not case.som:
            continue
        md.append(f"| {k} | {human(f_low[k], cur)} | **{human(f_base[k], cur)}** | {human(f_high[k], cur)} |")
    md += ["", f"TAM is taken from the primary approach (*{case.primary_approach.label}*).", ""]

    md += ["## Triangulation", "", "![football field](football_field.png)", "",
           "| Approach | All-low | P10 | **Base** | P90 | All-high |",
           "|---|---:|---:|---:|---:|---:|"]
    for r in summ.itertuples():
        md.append(f"| {r.approach} | {human(r.all_low, cur)} | {human(r.p10, cur)} | "
                  f"**{human(r.base, cur)}** | {human(r.p90, cur)} | {human(r.all_high, cur)} |")
    gap = triangulation_gap(case)
    if gap:
        verdict = ("approaches agree well" if gap < 1.3 else
                   "acceptable, but worth reconciling" if gap < 2 else
                   "approaches disagree, so check the structure of the weaker one")
        md += ["", f"Highest / lowest base estimate: **{gap:.2f}×** ({verdict})."]
    md.append("")

    for key, a in case.approaches.items():
        tor = tornado(a)
        tornado_chart(tor, a.value("base"), cur, f"What moves {a.label}?", out / f"tornado_{key}.png")
        md += [f"## {a.label}", "", f"Formula: {' × '.join(d.name for d in a.drivers)}", "",
               _drivers_table(a.drivers, cur), "", f"![tornado](tornado_{key}.png)", "",
               f"Biggest lever: **{tor.iloc[0]['driver']}**, which swings the result by "
               f"{human(tor.iloc[0]['swing'], cur)} ({tor.iloc[0]['swing_pct_of_base']:.0%} of base).", ""]

    if case.sam or case.som:
        md += ["## Funnel filters", ""]
        if case.sam:
            md += ["**SAM** (serviceable share)", "", _drivers_table(case.sam, cur), ""]
        if case.som:
            md += ["**SOM** (obtainable share)", "", _drivers_table(case.som, cur), ""]

    md += ["---", "*Generated with [market-sizing-kit](../../README.md). "
           "The Excel model (`model.xlsx`) contains the same logic with live formulas.*"]
    export_excel(case, out / "model.xlsx")
    path = out / "report.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path
