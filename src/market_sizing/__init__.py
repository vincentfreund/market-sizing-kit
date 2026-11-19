"""market-sizing-kit: transparent TAM/SAM/SOM estimates with ranges, sensitivities and Excel export."""

from .model import Approach, Driver, MarketCase, load_case
from .analysis import monte_carlo, summary, tornado, triangulation_gap
from .report import build_report
from .excel import export_excel

__all__ = [
    "Approach", "Driver", "MarketCase", "load_case",
    "monte_carlo", "summary", "tornado", "triangulation_gap",
    "build_report", "export_excel",
]
__version__ = "0.1.0"
