"""Export a case to an Excel model with LIVE formulas.

The workbook is meant to be opened and played with: change any yellow input
cell and every result updates, just like a model in a real engagement.
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .model import Driver, MarketCase

HEAD = Font(bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="2F6F8F")
INPUT_FILL = PatternFill("solid", fgColor="FFF4C2")
BOLD = Font(bold=True)
NUM = "#,##0.00"
BIG = '#,##0'


def _header(ws, row: int, labels: list[str]) -> None:
    for i, label in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=label)
        c.font, c.fill = HEAD, HEAD_FILL


def _driver_block(ws, start_row: int, title: str, drivers: list[Driver]) -> tuple[int, int, int]:
    """Write a block of drivers. Returns (first_row, last_row, next_free_row)."""
    ws.cell(row=start_row, column=1, value=title).font = Font(bold=True, size=12)
    _header(ws, start_row + 1, ["Driver", "Low", "Base", "High", "Unit", "Source"])
    first = start_row + 2
    for i, d in enumerate(drivers):
        r = first + i
        ws.cell(row=r, column=1, value=d.name)
        for col, val in ((2, d.low), (3, d.base), (4, d.high)):
            c = ws.cell(row=r, column=col, value=val)
            c.fill = INPUT_FILL
            c.number_format = "0.0%" if d.unit == "%" else NUM
        ws.cell(row=r, column=5, value=d.unit)
        ws.cell(row=r, column=6, value=d.source).alignment = Alignment(wrap_text=True)
    last = first + len(drivers) - 1
    return first, last, last + 1


def export_excel(case: MarketCase, path: str | Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Model"
    ws["A1"] = case.name
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = case.question
    ws["A3"] = f"Currency: {case.currency}   ·   Year: {case.year}   ·   Yellow cells are inputs."

    row = 5
    result_cells: dict[str, int] = {}
    for key, a in case.approaches.items():
        first, last, row = _driver_block(ws, row, a.label, a.drivers)
        ws.cell(row=row, column=1, value=f"Result: {a.label}").font = BOLD
        for col in (2, 3, 4):
            L = get_column_letter(col)
            c = ws.cell(row=row, column=col, value=f"=PRODUCT({L}{first}:{L}{last})")
            c.font, c.number_format = BOLD, BIG
        result_cells[key] = row
        row += 3

    # Funnel
    tam_row = result_cells[case.primary]
    ws.cell(row=row, column=1, value="Funnel (TAM from primary approach)").font = Font(bold=True, size=12)
    _header(ws, row + 1, ["Step", "Low", "Base", "High"])
    r = row + 2
    ws.cell(row=r, column=1, value="TAM").font = BOLD
    for col in (2, 3, 4):
        L = get_column_letter(col)
        ws.cell(row=r, column=col, value=f"={L}{tam_row}").number_format = BIG
    prev = r
    row = r + 2

    for step, drivers in (("SAM", case.sam), ("SOM", case.som)):
        if not drivers:
            continue
        first, last, row = _driver_block(ws, row, f"{step} filters", drivers)
        ws.cell(row=row, column=1, value=step).font = BOLD
        for col in (2, 3, 4):
            L = get_column_letter(col)
            c = ws.cell(row=row, column=col, value=f"={L}{prev}*PRODUCT({L}{first}:{L}{last})")
            c.font, c.number_format = BOLD, BIG
        prev = row
        row += 3

    for col, width in zip("ABCDEF", (38, 16, 16, 16, 14, 60)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A5"

    path = Path(path)
    wb.save(path)
    return path
