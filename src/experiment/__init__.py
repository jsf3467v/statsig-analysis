"""statsig-experiment-toolkit: SDK-instrumented A/B analysis with correct stats."""
from .report import report
from .simulate import dataset, simulate
from .stats import Result, cuped, power, sample_size, sprt, two_proportion, welch, winsorize

__version__ = "0.1.0"

__all__ = [
    "two_proportion", "welch", "winsorize", "sprt", "sample_size", "power",
    "cuped", "Result", "dataset", "simulate", "report",
]
