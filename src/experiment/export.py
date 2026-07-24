"""Read a Statsig raw data export and join exposures to metric values."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

EXPOSURE_FILE = "checkout_flow_first_exposures.csv"
METRIC_FILE = "checkout_flow_unit_metrics.csv"


def assignment(path: Path) -> dict[str, str]:
    """Map each unit to its experiment group from the first-exposure export."""
    with open(path, newline="") as fh:
        return {r["unit_id"]: r["experiment_group"] for r in csv.DictReader(fh)}


def totals(path: Path, metric: str) -> dict[str, float]:
    """Sum metric values per unit for one metric name."""
    values: dict[str, float] = defaultdict(float)
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["metric_name"] == metric:
                values[row["unit_id"]] += float(row["metric_value"])
    return values


def arms(directory: Path, metric: str = "purchase",
         exposures: str = EXPOSURE_FILE,
         metrics: str = METRIC_FILE) -> dict[str, np.ndarray]:
    """Per-unit metric values for the control and treatment arms.

    Units exposed but never recorded in the metric file contribute zero, which
    is what keeps the denominator equal to the exposed population.
    """
    groups = assignment(Path(directory) / exposures)
    values = totals(Path(directory) / metrics, metric)
    arm: dict[str, list[float]] = {"control": [], "treatment": []}
    for unit, group in groups.items():
        if group in arm:
            arm[group].append(values.get(unit, 0.0))
    return {name: np.asarray(vals, float) for name, vals in arm.items()}


def counts(values: np.ndarray) -> tuple[int, int]:
    """Units and units with a nonzero value, for a proportion test."""
    return values.size, int(np.count_nonzero(values))
